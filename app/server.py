#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flask 本地服务：产品详情套图工具 Web UI。

双击 EXE（或 python3 app/server.py）启动，浏览器自动打开任务配置页。
任务在后台线程跑 pipeline/run.py，进度通过 /api/status 轮询。
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import threading
import uuid
from urllib.parse import urlparse

from flask import Flask, request, jsonify, render_template, send_file, abort

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def base_dir():
    """项目根：EXE 版用 EXE 所在目录（products/ 输出写这里）；源码版用仓库根。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(APP_DIR)


def resource_path(rel):
    """打包进 EXE 的只读资源（pipeline/、templates、static）。"""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return os.path.join(meipass, rel)
    return os.path.join(base_dir(), rel)


BASE_DIR = base_dir()
PRODUCTS_DIR = os.path.join(BASE_DIR, "products")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".product-image-set", "config.json")

app = Flask(__name__,
            template_folder=resource_path(os.path.join("app", "templates")),
            static_folder=resource_path(os.path.join("app", "static")))

JOBS = {}          # job_id -> job dict
JOBS_LOCK = threading.Lock()

MODULE_ORDER = ["ingest", "analyze", "plan", "copy", "ops_copy",
                "douyin", "generate", "layout", "validate"]
STATUS_LABEL = {"done": "已完成", "ok": "已完成", "running": "进行中", "pending": "等待中",
                "failed": "失败", "skipped": "已跳过"}
# manifest 里成功记为 ok，统一归一化为 done
STATUS_NORM = {"ok": "done"}

SEASON_LABEL = {"spring": "春", "summer": "夏", "autumn": "秋", "winter": "冬",
                "christmas": "圣诞", "easter": "复活节", "halloween": "万圣节",
                "black_friday": "黑五", "new_year": "新年", "valentine": "情人节"}
THEME_LABEL = {"manhattan": "Manhattan 浅色", "intellinet": "Intellinet 深色"}


# ---------- 工具函数 ----------

def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    d = os.path.dirname(CONFIG_PATH)
    os.makedirs(d, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass


def parse_product_input(text):
    """handle 或产品页 URL → (handle, site)。"""
    text = (text or "").strip()
    if not text:
        return None, None
    if text.startswith("http"):
        m = re.search(r"/products/([a-z0-9\-]+)", text)
        if not m:
            return None, None
        u = urlparse(text)
        site = f"{u.scheme}://{u.netloc}"
        return m.group(1), site
    return text, "https://manhattanproducts.eu"


HANDLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]*$")


def is_valid_handle(handle):
    """料号 handle 白名单：防 ../../evil 或 C:\\Temp\\x 拼出 products 之外的 workdir（军师评审 M5）。"""
    return bool(handle) and bool(HANDLE_RE.match(handle))


def check_same_origin():
    """POST 接口来源校验：Origin/Referer 若存在，其 host 必须等于 request.host（军师评审 M3）。

    返回 None 表示通过，否则返回 (jsonify body, status) 元组。
    两个头都不存在时放行（兼容 curl 这类直调）。
    """
    for hdr in ("Origin", "Referer"):
        val = request.headers.get(hdr)
        if not val:
            continue
        try:
            host = urlparse(val).netloc.split("@")[-1]
        except Exception:
            return jsonify({"error": "forbidden"}), 403
        # netloc 可能带端口；request.host 同样带端口，直接比完整 host
        if host.lower() != request.host.lower():
            return jsonify({"error": "forbidden"}), 403
    return None


def pipeline_cmd():
    """run.py 的启动命令。EXE 冻结模式走 launcher 的 --pipeline-worker 垫片。"""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--pipeline-worker", "pipeline/run.py"]
    return [sys.executable, resource_path(os.path.join("pipeline", "run.py"))]


def read_manifest_modules(workdir):
    mp = os.path.join(workdir, "manifest.json")
    try:
        with open(mp, encoding="utf-8") as f:
            return json.load(f).get("modules", {})
    except Exception:
        return {}


# ---------- 页面 ----------

@app.route("/")
def index():
    saved = load_config()
    return render_template("index.html", saved={
        "api_key_openai": saved.get("api_key_openai", ""),
        "api_key_gemini": saved.get("api_key_gemini", ""),
        "base_url": saved.get("base_url", ""),
    })


@app.route("/results")
def results():
    job_id = request.args.get("job_id", "")
    job = JOBS.get(job_id)
    if not job:
        abort(404)
    workdir = job["workdir"]
    rel = os.path.relpath(workdir, PRODUCTS_DIR)

    def fexists(name):
        return os.path.isfile(os.path.join(workdir, name))

    images = []
    final_dir = os.path.join(workdir, "final")
    if os.path.isdir(final_dir):
        for fn in sorted(os.listdir(final_dir)):
            if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append({"name": fn,
                               "url": f"/files/{rel}/final/{fn}"})

    docs = [
        ("copy.md", "主图文案 copy.md", "Amazon 五点 / 京东卖点 / 海报文案", "文"),
        ("ops_copy.md", "运营文案包 ops_copy.md", "搜索词 / A+ / 京东商详 / 上架 checklist", "营"),
        ("douyin_copy.md", "抖音文案 douyin_copy.md", "发布文案 / 口播脚本 / 评论区话术", "抖"),
        ("showcase.html", "套图展示页 showcase.html", "6 屏落地页式，按痛点型销售逻辑编排", "展"),
        ("CHECKLIST.md", "验收清单 CHECKLIST.md", "人工验收门：逐项打勾确认", "验"),
        ("manifest.json", "manifest.json", "产物清单与模块状态", "单"),
    ]
    docs = [{"file": f, "title": t, "desc": d, "ico": i,
             "exists": fexists(f),
             "url": f"/files/{rel}/{f}"} for f, t, d, i in docs]

    return render_template(
        "results.html",
        job_id=job_id,
        handle=job["handle"],
        season_label=SEASON_LABEL.get(job["season"], job["season"] or "-"),
        theme_label=THEME_LABEL.get(job["theme"], job["theme"] or "-"),
        modules=job["requested"],
        images=images,
        docs=docs,
        state=job["state"],
    )


@app.route("/files/<path:subpath>")
def files(subpath):
    base = os.path.realpath(PRODUCTS_DIR)
    target = os.path.realpath(os.path.join(base, subpath))
    if target != base and not target.startswith(base + os.sep):
        abort(403)
    if not os.path.isfile(target):
        abort(404)
    return send_file(target)


# ---------- API ----------

@app.route("/api/run", methods=["POST"])
def api_run():
    denied = check_same_origin()
    if denied:
        return denied
    f = request.form
    handle, site = parse_product_input(f.get("product_input", ""))
    if not handle:
        return jsonify({"error": "产品输入无效：请填 Shopify handle 或产品页 URL"}), 400
    if not is_valid_handle(handle):
        return jsonify({"error": "料号格式无效：只允许字母、数字、短横线"}), 400

    modules = [m for m in f.getlist("modules") if m in MODULE_ORDER]
    if not modules:
        return jsonify({"error": "至少勾选一个模块"}), 400

    season = f.get("season") or None
    theme = f.get("theme") or "manhattan"
    provider = f.get("provider") or None
    if provider == "openai_compatible":
        provider = "openai"  # 兼容地址走 openai 通道 + --base-url
    base_url = (f.get("base_url") or "").strip() or None
    dry_run = bool(f.get("dry_run"))

    workdir = os.path.join(PRODUCTS_DIR, handle)
    os.makedirs(workdir, exist_ok=True)

    cmd = (pipeline_cmd()
           + ["--handle", handle, "--site", site,
              "--workdir", workdir,
              "--modules", ",".join(modules),
              "--theme", theme]
           + (["--season", season] if season else [])
           + (["--provider", provider] if provider else [])
           + (["--base-url", base_url] if base_url else [])
           + (["--dry-run"] if dry_run else []))

    env = dict(os.environ)
    key_oa = (f.get("api_key_openai") or "").strip()
    key_ge = (f.get("api_key_gemini") or "").strip()
    if key_oa:
        env["OPENAI_API_KEY"] = key_oa
    if key_ge:
        env["GEMINI_API_KEY"] = key_ge
    if base_url:
        env["OPENAI_BASE_URL"] = base_url

    # Key 存本机用户目录配置，下次回填表单。
    # 注：os.chmod(0o600) 在 Windows 上是 no-op，实际靠用户目录 ACL 隔离保护。
    cfg = load_config()
    if key_oa:
        cfg["api_key_openai"] = key_oa
    if key_ge:
        cfg["api_key_gemini"] = key_ge
    if base_url:
        cfg["base_url"] = base_url
    if key_oa or key_ge or base_url:
        save_config(cfg)

    job_id = uuid.uuid4().hex[:12]
    job = {"job_id": job_id, "handle": handle, "site": site,
           "workdir": workdir, "requested": modules,
           "season": season, "theme": theme,
           "state": "running", "proc": None, "log": [],
           "cmd": cmd}
    with JOBS_LOCK:
        JOBS[job_id] = job
        # L2: JOBS 只增不减会缓慢吃内存；超过 20 个时删掉最老的已结束记录
        if len(JOBS) > 20:
            for _jid in list(JOBS):
                if len(JOBS) <= 20:
                    break
                if JOBS[_jid].get("state") in ("done", "failed"):
                    del JOBS[_jid]

    t = threading.Thread(target=_run_job, args=(job, env), daemon=True)
    t.start()
    return jsonify({"job_id": job_id, "workdir": workdir})


def _run_job(job, env):
    try:
        proc = subprocess.Popen(
            job["cmd"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", env=env, cwd=BASE_DIR)
        job["proc"] = proc
        for line in proc.stdout:
            job["log"].append(line.rstrip("\n"))
            if len(job["log"]) > 200:
                del job["log"][:100]
        rc = proc.wait()
        job["state"] = "done" if rc == 0 else "failed"
    except Exception as e:  # noqa: BLE001
        job["log"].append(f"[server] 启动失败: {e}")
        job["state"] = "failed"


@app.route("/api/status")
def api_status():
    job_id = request.args.get("job_id", "")
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "job 不存在"}), 404

    records = read_manifest_modules(job["workdir"])
    mods = {}
    seen_running = False
    done_count = 0
    for m in job["requested"]:
        rec = records.get(m)
        if rec:
            st = STATUS_NORM.get(rec.get("status", "done"), rec.get("status", "done"))
            if st in ("done", "skipped"):
                done_count += 1
        elif job["state"] == "running" and not seen_running:
            st = "running"
            seen_running = True
        else:
            st = "pending"
        mods[m] = {"status": st, "label": STATUS_LABEL.get(st, st),
                   "cls": st}

    total = len(job["requested"])
    pct = round(done_count / total * 100) if total else 0
    return jsonify({
        "state": job["state"],
        "modules": mods,
        "done_count": done_count,
        "total": total,
        "pct": pct,
        "log_tail": job["log"][-30:],
    })


# ---------- 启动 ----------

def find_port(start):
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1


def main(argv=None):
    # Windows 控制台默认编码常为 cp1252/cp936，直接 python app/server.py 跑时中文 print 会炸，
    # 这里同样切到 UTF-8（军师评审 L4；冻结模式下 launcher 已做过一次，重复执行无害）。
    for _s in (sys.stdout, sys.stderr):
        try:
            if _s is not None and hasattr(_s, "reconfigure"):
                _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="产品详情套图工具 · 本地网页服务")
    # L8: 只有未显式传 --port 时才自己找端口；launcher 已找好并通过 --port 传进来，不要重复找。
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args(argv)
    port = args.port if args.port is not None else find_port(5057)
    print(f"[server] http://127.0.0.1:{port}/  (项目根 {BASE_DIR})")
    app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
