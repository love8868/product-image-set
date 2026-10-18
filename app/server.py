#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flask 本地服务：产品详情套图工具 Web UI。

双击 EXE（或 python3 app/server.py）启动，浏览器自动打开任务配置页。
任务在后台线程跑 pipeline/run.py，进度通过 /api/status 轮询。
"""

import argparse
import io
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, request, jsonify, render_template, send_file, abort, redirect, url_for

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
                "douyin", "generate", "layout", "validate", "showcase"]
# 模块中文名（结果页 .name 渲染用，.en 显示英文 id；设计稿对应关系）
MODULE_NAME_ZH = {"ingest": "素材入库", "analyze": "分析", "plan": "策划",
                  "copy": "文案", "ops_copy": "运营文案", "douyin": "抖音文案",
                  "generate": "生图", "layout": "排版", "validate": "校验",
                  "showcase": "展示页"}
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


def parse_product_input(text, theme="manhattan"):
    """料号 / handle / 产品页 URL 三态 → (handle, site)。

    - http 开头 → URL（原逻辑，从 /products/<handle> 提取）
    - 纯数字 → 料号：走 Shopify suggest.json 搜索（MANHATTAN 用 manhattanproducts.eu，
      INTELLINET 用 intellinetsolutions.com），取首个结果的 handle
    - 其他文本 → handle（site 按 theme 选站）
    查不到返回 (None, None)，由 api_run 给人话报错。
    """
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
    if re.fullmatch(r"[0-9]+", text):
        site = ("https://manhattanproducts.eu" if theme == "manhattan"
                else "https://intellinetsolutions.com")
        handle = resolve_sku(text, site)
        if not handle:
            return None, None
        return handle, site
    site = ("https://manhattanproducts.eu" if theme == "manhattan"
            else "https://intellinetsolutions.com")
    return text, site


def resolve_sku(sku, site):
    """料号 → handle：Shopify /search/suggest.json 搜产品，取首个结果的 URL 提 handle。
    查不到 / 异常一律返回 None（调用方给人话报错）。"""
    try:
        qs = urllib.parse.urlencode({"q": sku, "resources[type]": "product",
                                     "resources[limit]": 5})
        url = f"{site.rstrip('/')}/search/suggest.json?{qs}"
        req = urllib.request.Request(url,
                                     headers={"User-Agent": "product-image-set/1.0",
                                              "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        products = (data.get("resources", {}).get("results", {})
                    .get("products", []))
        if not products:
            return None
        m = re.search(r"/products/([a-z0-9\-]+)", products[0].get("url", ""))
        if not m:
            return None
        handle = m.group(1)
        return handle if is_valid_handle(handle) else None
    except Exception:
        return None


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

def _history_entries():
    """F1：扫描 products/*/manifest.json → 历史任务条目（按 handle 查盘）。"""
    entries = []
    if not os.path.isdir(PRODUCTS_DIR):
        return entries
    for handle in sorted(os.listdir(PRODUCTS_DIR)):
        workdir = os.path.join(PRODUCTS_DIR, handle)
        mp = os.path.join(workdir, "manifest.json")
        if not os.path.isdir(workdir) or not os.path.isfile(mp):
            continue
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            continue
        meta = m.get("meta", {}) or {}
        mods = m.get("modules", {}) or {}
        # 标题/SKU：读 product.json，try 保护
        title, sku = handle, ""
        pj = os.path.join(workdir, "product.json")
        try:
            p = json.load(open(pj, encoding="utf-8"))
            title = p.get("title") or handle
            sku = p.get("sku") or ""
        except Exception:
            pass
        # 状态：JOBS 有同 handle 运行中 → 运行中；任一 failed → 已失败；全 ok/skipped → 已完成
        state, state_label = "done", "已完成"
        with JOBS_LOCK:
            running = any(j.get("handle") == handle and j.get("state") == "running"
                          for j in JOBS.values())
        if running:
            state, state_label = "running", "运行中"
        elif any(r.get("status") == "failed" for r in mods.values()):
            state, state_label = "failed", "已失败"
        elif mods and not all(r.get("status") in ("ok", "skipped") for r in mods.values()):
            state, state_label = "running", "进行中"
        # 缩略图：hero_image 回退 raw/01.jpg
        thumb = None
        try:
            p = json.load(open(pj, encoding="utf-8"))
            hero = p.get("hero_image")
            if hero and os.path.isfile(os.path.join(workdir, hero)):
                thumb = f"/files/{handle}/{hero}"
        except Exception:
            pass
        if not thumb and os.path.isfile(os.path.join(workdir, "raw", "01.jpg")):
            thumb = f"/files/{handle}/raw/01.jpg"
        created = meta.get("created_at")
        if not created:
            try:
                created = datetime.fromtimestamp(
                    os.path.getmtime(workdir)).isoformat(timespec="seconds")
            except Exception:
                created = ""
        entries.append({
            "handle": handle, "title": title, "sku": sku,
            "created_at": created, "state": state, "state_label": state_label,
            "season": meta.get("season") or "", "theme": meta.get("theme") or "",
            "provider": meta.get("provider") or "", "thumb": thumb,
        })
    # 最新在前
    entries.sort(key=lambda e: e["created_at"] or "", reverse=True)
    return entries


@app.route("/")
def index():
    saved = load_config()
    # 场景池 / 风格列表动态读（零硬编码；草图 11 个 pills 换行排布已验证）
    try:
        sys.path.insert(0, resource_path("pipeline"))
        from recommend import SCENE_POOL
        from prompts import load_styles
        scenes = [(k, v["label_zh"]) for k, v in SCENE_POOL.items()]
        styles = [(s["id"], s["name_zh"]) for s in load_styles().values()]
    except Exception:
        scenes, styles = [], []
    return render_template("index.html", saved={
        "api_key_openai": saved.get("api_key_openai", ""),
        "api_key_gemini": saved.get("api_key_gemini", ""),
        "base_url": saved.get("base_url", ""),
    }, history=_history_entries(), scenes=scenes, styles=styles)


@app.route("/results")
def results():
    # F1：?handle= 从硬盘读（关页/重启不 404）；?job_id= 老链接兼容
    handle = request.args.get("handle", "")
    job_id = request.args.get("job_id", "")
    job = None
    if job_id:
        job = JOBS.get(job_id)
        if not job:
            abort(404, description="任务不存在（页面关过或服务重启过），请从首页历史任务进入")
        # 302 到按 handle 查盘的地址
        return redirect(url_for("results", handle=job["handle"]))
    if not handle or not is_valid_handle(handle):
        abort(404)
    workdir = os.path.join(PRODUCTS_DIR, handle)
    if not os.path.isdir(workdir):
        abort(404, description="该产品没有历史记录")

    try:
        m = json.load(open(os.path.join(workdir, "manifest.json"), encoding="utf-8"))
    except Exception:
        m = {}
    meta = m.get("meta", {}) or {}
    mods = m.get("modules", {}) or {}

    # 运行中状态：JOBS 里找同 handle 的 job（用于轮询）
    live_job_id, live_state = "", "done"
    with JOBS_LOCK:
        for jid, j in JOBS.items():
            if j.get("handle") == handle and j.get("state") == "running":
                live_job_id, live_state = jid, "running"
                break
    if not live_job_id:
        live_state = ("failed" if any(r.get("status") == "failed" for r in mods.values())
                      else "done")

    def fexists(name):
        return os.path.isfile(os.path.join(workdir, name))

    images = []
    final_dir = os.path.join(workdir, "final")
    if os.path.isdir(final_dir):
        for fn in sorted(os.listdir(final_dir)):
            if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append({"name": fn,
                               "url": f"/files/{handle}/final/{fn}"})

    docs = [
        ("copy.md", "主图文案", "Amazon 五点 / 京东卖点 / 海报文案 / 痛点解法", "文"),
        ("ops_copy.md", "运营文案包", "搜索词 / A+ / 京东商详 / 上架 checklist", "营"),
        ("douyin_copy.md", "抖音文案", "发布文案 / 口播脚本 / 评论区话术", "抖"),
        ("showcase.html", "套图展示页", "6 屏落地页式，按痛点型销售逻辑编排", "展"),
        ("CHECKLIST.md", "验收清单", "人工验收门：逐项打勾确认", "验"),
    ]
    # F2：文案走 /doc 渲染成页面，不再直接裸看 .md 源码
    doc_files = {"copy.md", "ops_copy.md", "ops-checklist.md",
                 "douyin_copy.md", "CHECKLIST.md", "plan.md"}
    docs = [{"file": f, "title": t, "desc": d, "ico": i,
             "exists": fexists(f),
             "url": (url_for("doc", handle=handle, file=f) if f in doc_files
                     else f"/files/{handle}/{f}")}
            for f, t, d, i in docs]

    # 模块状态归一化（manifest 里成功记 ok → done），供模板直接渲染
    mod_display, mod_label = {}, {}
    done_count = 0
    for k in (list(mods.keys()) or MODULE_ORDER):
        st = STATUS_NORM.get(mods.get(k, {}).get("status", "pending"),
                             mods.get(k, {}).get("status", "pending"))
        mod_display[k] = st
        mod_label[k] = STATUS_LABEL.get(st, st)
        if st in ("done", "skipped"):
            done_count += 1
    total = len(mod_display)
    pct = round(done_count / total * 100) if total else 0

    return render_template(
        "results.html",
        job_id=live_job_id,
        handle=handle,
        season_label=SEASON_LABEL.get(meta.get("season"), meta.get("season") or "-"),
        theme_label=THEME_LABEL.get(meta.get("theme"), meta.get("theme") or "-"),
        modules=list(mod_display.keys()),
        module_names=MODULE_NAME_ZH,
        module_status=mod_display,
        module_labels=mod_label,
        pct=pct, done_count=done_count, total=total,
        images=images,
        docs=docs,
        state=live_state,
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


@app.route("/prompts")
def prompts_page():
    """F5 提示词库 + F6 job 卡（下游区块）：三数据源合一，零硬编码。"""
    handle = request.args.get("handle", "")
    if not handle or not is_valid_handle(handle):
        abort(404)
    workdir = os.path.join(PRODUCTS_DIR, handle)
    if not os.path.isdir(workdir):
        abort(404, description="该产品没有历史记录")

    sys.path.insert(0, resource_path("pipeline"))
    from prompts import load_slots, build_variables, build_prompt, load_base, load_locks

    try:
        manifest = json.load(open(os.path.join(workdir, "manifest.json"), encoding="utf-8"))
    except Exception:
        manifest = {}
    used = manifest.get("templates", {}) or {}
    meta = manifest.get("meta", {}) or {}
    try:
        plan = json.load(open(os.path.join(workdir, "plan.json"), encoding="utf-8"))
    except Exception:
        plan = {}
    recommended = set(plan.get("recommended_templates") or [])

    product, variables, base, locks = None, None, None, None
    pj = os.path.join(workdir, "product.json")
    if os.path.isfile(pj):
        try:
            product = json.load(open(pj, encoding="utf-8"))
            season_scene = None
            if meta.get("season"):
                try:
                    from seasons import get_season
                    season_scene = get_season(meta["season"])["scene_en"]
                except Exception:
                    pass
            variables = build_variables(product, season_scene=season_scene)
            base, locks = load_base(), load_locks()
        except Exception:
            product = None

    def _img_url(job_key):
        # 终审调整点 2：收藏配图直接用 draft 直链；_placeholder 不展示
        for cand in (f"{job_key}.png",):
            pp = os.path.join(workdir, "draft", cand)
            if os.path.isfile(pp):
                return f"/files/{handle}/draft/{cand}".replace(os.sep, "/")
        return None

    templates = []
    for slot in load_slots():
        sid = slot["id"]
        prompt_text, negative = None, None
        if product and variables and base and locks:
            try:
                prompt_text = build_prompt(slot, variables, base=base, locks=locks)
                negative = base.get("negative", "")
                if slot.get("negative_add"):
                    negative += ", " + ", ".join(slot["negative_add"])
            except SystemExit:
                prompt_text = None  # 变量缺失：不阻断列表渲染
            except Exception:
                prompt_text = None
        templates.append({
            "id": sid,
            "name_zh": slot.get("name_zh") or sid,
            "version": slot.get("version"),
            "changelog": slot.get("changelog") or [],
            "trigger": slot.get("trigger"),
            "trigger_zh": {"always": "自动", "season": "季节",
                           "manual": "手动备查"}.get(slot.get("trigger"), ""),
            "scene": (slot.get("scene_en") or "")[:220],
            "recommended": sid in recommended,
            "used_version": (used.get(sid) or {}).get("version"),
            "image": _img_url(sid),
            "prompt": prompt_text,
            "negative": negative,
            "need_review": sid in ("comparison", "spec_sheet"),
        })
    # 推荐置顶，其余按 order（load_slots 已按 order 排好）
    templates.sort(key=lambda t: (0 if t["recommended"] else 1))

    # F6：muse 代跑 job 卡
    jobs = []
    jobs_dir = os.path.join(workdir, "jobs")
    if os.path.isdir(jobs_dir):
        for fn in sorted(os.listdir(jobs_dir)):
            if not fn.endswith(".json"):
                continue
            try:
                card = json.load(open(os.path.join(jobs_dir, fn), encoding="utf-8"))
            except Exception:
                continue
            jid = card.get("job_id", fn[:-5])
            img = None
            out = card.get("output") or f"draft/{jid}.png"
            if os.path.isfile(os.path.join(workdir, out)):
                img = f"/files/{handle}/{out}".replace(os.sep, "/")
            ref_urls = []
            for r in (card.get("ref_images") or []):
                if r and os.path.isfile(os.path.join(workdir, r)):
                    ref_urls.append(f"/files/{handle}/{r}".replace(os.sep, "/"))
            mask_url = None
            if card.get("mask") and os.path.isfile(os.path.join(workdir, card["mask"])):
                mask_url = f"/files/{handle}/{card['mask']}".replace(os.sep, "/")
            jobs.append({
                "job_id": jid,
                "template_id": card.get("template_id"),
                "template_version": card.get("template_version"),
                "lane": card.get("lane"),
                "size": card.get("size"),
                "status": card.get("status"),
                "status_zh": {"pending": "待回填", "filled": "已回填"}.get(
                    card.get("status"), card.get("status")),
                "prompt": card.get("prompt"),
                "negative": card.get("negative"),
                "image": img,
                "ref_urls": ref_urls,
                "mask_url": mask_url,
            })

    return render_template("prompts.html", handle=handle,
                           templates=templates, jobs=jobs,
                           has_jobs=os.path.isdir(jobs_dir),
                           theme=meta.get("theme") or "manhattan")


@app.route("/api/fill", methods=["POST"])
def api_fill():
    """F6：job 卡回填。try_fill_job 返回 (ok, msg) 元组，不抛 sys.exit。"""
    denied = check_same_origin()
    if denied:
        return denied
    handle = (request.form.get("handle") or "").strip()
    job_id = (request.form.get("job_id") or "").strip()
    if not handle or not is_valid_handle(handle):
        return jsonify({"ok": False, "msg": "产品无效"}), 400
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", job_id):
        return jsonify({"ok": False, "msg": "job_id 无效"}), 400
    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify({"ok": False, "msg": "请选择图片文件"}), 400
    workdir = os.path.join(PRODUCTS_DIR, handle)
    jobs_dir = os.path.join(workdir, "jobs")
    if not os.path.isdir(jobs_dir):
        return jsonify({"ok": False, "msg": "该产品没有代跑 job 卡"}), 400
    # 保留原扩展名（fill_job 按扩展名校验 jpg/png）
    ext = os.path.splitext(f.filename)[1].lower() or ".tmp"
    tmp = os.path.join(jobs_dir, f"_upload_{job_id}{ext}")
    f.save(tmp)
    try:
        sys.path.insert(0, resource_path("pipeline"))
        from providers.muse import fill_job
        ok, msg = fill_job(workdir, job_id, tmp)
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    return jsonify({"ok": ok, "msg": msg})


@app.route("/api/package")
def api_package():
    """打包下载：一键拿 8 张成品图 + 文案 + showcase 的 ZIP。"""
    handle = request.args.get("handle", "")
    if not handle or not is_valid_handle(handle):
        return jsonify({"error": "产品无效"}), 400
    workdir = os.path.join(PRODUCTS_DIR, handle)
    if not os.path.isdir(workdir):
        return jsonify({"error": "该产品没有历史记录"}), 400
    base = os.path.realpath(workdir)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        def _add(src_rel, arc):
            # 防穿越：realpath 必须在 workdir 内（同 /files/ 模式）
            src = os.path.realpath(os.path.join(workdir, src_rel))
            if (src == base or src.startswith(base + os.sep)) and os.path.isfile(src):
                z.write(src, arc)
        final_dir = os.path.join(workdir, "final")
        if os.path.isdir(final_dir):
            for fn in sorted(os.listdir(final_dir)):
                if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    _add(os.path.join("final", fn), f"final/{fn}")
        for doc in ("copy.md", "ops_copy.md", "ops-checklist.md",
                    "douyin_copy.md", "CHECKLIST.md", "showcase.html"):
            _add(doc, doc)  # 缺失文件静默跳过
    buf.seek(0)
    # Werkzeug ≥2.0 按 RFC 5987 编码 filename*，中文文件名安全
    fname = f"套图_{handle}_{datetime.now().strftime('%Y%m%d')}.zip"
    return send_file(buf, mimetype="application/zip",
                     as_attachment=True, download_name=fname)


# ---------- F2: 文案渲染成页面 ----------

DOC_WHITELIST = {"copy.md", "ops_copy.md", "ops-checklist.md",
                 "douyin_copy.md", "CHECKLIST.md", "plan.md"}


def render_doc(workdir, filename):
    """Markdown → HTML + section 后处理加 class（可信源：本机管线生成，不做 XSS 过滤）。"""
    import markdown
    text = open(os.path.join(workdir, filename), encoding="utf-8").read()
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    # 按 h2 切 section，包 div + 语义 class
    parts = re.split(r"<h2>(.*?)</h2>", html)
    out = [parts[0]]
    for i in range(1, len(parts), 2):
        title = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        plain = re.sub(r"<[^>]+>", "", title)
        cls = "doc-sec"
        if "NEEDS-REVIEW" in plain or "推断" in plain:
            cls += " sec-review"      # 虚线警示框
        elif any(k in plain for k in ("Bullets", "卖点", "痛点", "解法")):
            cls += " sec-cards"       # 编号卡片
        elif "海报" in plain or "Banner" in plain:
            cls += " sec-quote"       # 引用条
        out.append(f'<div class="{cls}"><div class="sec-head"><h2>{title}</h2>'
                   f'<button class="copy-btn" data-sec="{i}">复制本节</button></div>'
                   f"{body}</div>")
    return "".join(out)


@app.route("/doc")
def doc():
    handle = request.args.get("handle", "")
    filename = request.args.get("file", "")
    if not handle or not is_valid_handle(handle) or filename not in DOC_WHITELIST:
        abort(403)
    workdir = os.path.join(PRODUCTS_DIR, handle)
    if not os.path.isfile(os.path.join(workdir, filename)):
        abort(404)
    body = render_doc(workdir, filename)
    return render_template("doc.html", handle=handle, filename=filename, body=body)


# ---------- API ----------

@app.route("/api/run", methods=["POST"])
def api_run():
    denied = check_same_origin()
    if denied:
        return denied
    f = request.form
    raw_input = (f.get("product_input") or "").strip()
    if not raw_input:
        return jsonify({"error": "请输入产品料号、产品链接或编号"}), 400
    theme = f.get("theme") or "manhattan"
    handle, site = parse_product_input(raw_input, theme)
    if not handle:
        return jsonify({"error": "无产品信息，可能是页面不对（请检查料号/链接）"}), 400
    if not is_valid_handle(handle):
        return jsonify({"error": "料号格式无效：只允许字母、数字、短横线"}), 400

    modules = [m for m in f.getlist("modules") if m in MODULE_ORDER]
    if not modules:
        return jsonify({"error": "至少勾选一个模块"}), 400

    season = f.get("season") or None
    provider = f.get("provider") or None
    if provider == "openai_compatible":
        provider = "openai"  # 兼容地址走 openai 通道 + --base-url
    base_url = (f.get("base_url") or "").strip() or None
    dry_run = bool(f.get("dry_run"))
    strategy = (f.get("strategy") or "").strip() or None
    force = bool(f.get("force"))
    # v0.3.0 场景 / 风格选择
    scenes = [s for s in f.getlist("scenes") if s]
    scene_add = (f.get("scene_add") or "").strip() or None
    style = (f.get("style") or "").strip() or None
    style_add = (f.get("style_add") or "").strip() or None

    workdir = os.path.join(PRODUCTS_DIR, handle)
    try:
        os.makedirs(workdir, exist_ok=True)
    except OSError:
        # B7：无权限时给人话报错而不是 500
        return jsonify({"error": f"目录无法写入：{workdir}，请换个解压位置"}), 400

    cmd = (pipeline_cmd()
           + ["--handle", handle, "--site", site,
              "--workdir", workdir,
              "--modules", ",".join(modules),
              "--theme", theme]
           + (["--season", season] if season else [])
           + (["--provider", provider] if provider else [])
           + (["--base-url", base_url] if base_url else [])
           + (["--dry-run"] if dry_run else [])
           + (["--strategy", strategy] if strategy else [])
           + (["--force"] if force else [])
           + (["--scenes", ",".join(scenes)] if scenes else [])
           + (["--scene-add", scene_add] if scene_add else [])
           + (["--style", style] if style else [])
           + (["--style-add", style_add] if style_add else []))

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
        if rc != 0 and not job["log"]:
            # B11：子进程崩溃无输出时，日志给一句兜底，不留空
            job["log"].append(f"[server] 子进程退出码 {rc}（无输出）")
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
