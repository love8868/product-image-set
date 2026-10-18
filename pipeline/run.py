#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一调度器：模块单选/多选，依赖自动补齐，topo 排序执行，状态写入 manifest.json。

Usage:
  python3 pipeline/run.py --list
  python3 pipeline/run.py --handle <shopify-handle> --modules ingest,plan,copy
  python3 pipeline/run.py --handle <shopify-handle> --all --dry-run --season easter
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PIPELINE_DIR)

MODULES = {
    "ingest":   {"script": "ingest.py",   "deps": [],
                 "outputs": ["product_raw.json", "raw/"],
                 "desc": "S0 素材入库：Shopify .json → product_raw.json，图片下载"},
    "analyze":  {"script": "analyze.py",  "deps": ["ingest"],
                 "outputs": ["product.json"],
                 "desc": "S1 规则式分析 → product.json（事实分级）"},
    "plan":     {"script": "plan.py",     "deps": ["analyze"],
                 "outputs": ["plan.md", "plan.json"],
                 "desc": "S1b 策划：三型诊断→图位规划→视觉合同"},
    "copy":     {"script": "copy.py",     "deps": ["analyze"],
                 "outputs": ["copy.md"],
                 "desc": "S2 图上文案：Amazon bullets/京东卖点/海报文案"},
    "ops_copy": {"script": "ops_copy.py", "deps": ["analyze"],
                 "outputs": ["ops_copy.md", "ops-checklist.md"],
                 "desc": "运营文案包：search terms/A+/京东商详"},
    "douyin":   {"script": "douyin.py",   "deps": ["analyze", "plan"],
                 "outputs": ["douyin_copy.md"],
                 "desc": "抖音文案：发布文案/口播脚本/评论区话术"},
    "generate": {"script": "generate.py", "deps": ["plan"],
                 "outputs": ["prompts/", "draft/"],
                 "desc": "S3 底图生成（--dry-run 无 Key 跑通）"},
    "layout":   {"script": "layout.py",   "deps": ["generate", "copy"],
                 "outputs": ["final/"],
                 "desc": "S4 排版叠字 → final/"},
    "validate": {"script": "validate.py", "deps": ["layout"],
                 "outputs": ["manifest.json", "CHECKLIST.md"],
                 "desc": "S5 校验 → manifest.json + 验收清单"},
    "showcase": {"script": "showcase.py", "deps": ["layout", "copy"],
                 "outputs": ["showcase.html"],
                 "desc": "S6 套图展示页 → showcase.html（痛点/规格网格）"},
}


def args_for(module, a):
    """按模块需要透传参数（只传该脚本支持的参数）。"""
    w = ["--workdir", a.workdir]
    scene_style = (
        (["--scenes", a.scenes] if getattr(a, "scenes", None) else [])
        + sum((["--scene-add", t] for t in (getattr(a, "scene_add", None) or [])), [])
        + (["--style", a.style] if getattr(a, "style", None) else [])
        + (["--style-add", a.style_add] if getattr(a, "style_add", None) else [])
    )
    if module == "ingest":
        return ["--handle", a.handle, "--site", a.site] + w
    if module == "plan":
        return (w + ["--theme", a.theme]
                + (["--strategy", a.strategy] if a.strategy else [])
                + scene_style)
    if module == "generate":
        return (w + (["--dry-run"] if a.dry_run else [])
                + (["--season", a.season] if a.season else [])
                + (["--provider", a.provider] if a.provider else [])
                + (["--base-url", a.base_url] if a.base_url else [])
                + scene_style)
    if module == "layout":
        return w + ["--theme", a.theme] + (["--season", a.season] if a.season else [])
    if module == "validate":
        return w + (["--season", a.season] if a.season else [])
    if module == "showcase":
        return w + ["--theme", a.theme] + (["--season", a.season] if a.season else [])
    return w  # analyze, copy, ops_copy, douyin


def _module_cmd(script_name, args):
    """模块子进程命令。PyInstaller 冻结模式下 sys.executable 是 EXE 本体，
    不能直接当 python 用，改走 launcher 的 --pipeline-worker 垫片。"""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--pipeline-worker",
                "pipeline/" + script_name] + args
    return [sys.executable,
            os.path.join(PIPELINE_DIR, script_name)] + args


def resolve(requested):
    """依赖闭包 + topo 排序（注册表顺序即合法 topo 序）。"""
    seen = set()

    def visit(m):
        if m in seen:
            return
        for d in MODULES[m]["deps"]:
            visit(d)
        seen.add(m)

    for m in requested:
        visit(m)
    return [m for m in MODULES if m in seen]


def outputs_exist(workdir, outputs):
    # F4：ingest 做数量校验（product_raw.json 的 images 数 vs raw/*.jpg），
    # 不等视为缺失 → 重跑自动补齐，不用 --force 也能补
    if "raw/" in outputs:
        try:
            raw = json.load(open(os.path.join(workdir, "product_raw.json"),
                                 encoding="utf-8"))
            n_images = len(raw.get("images") or [])
            n_files = len([f for f in os.listdir(os.path.join(workdir, "raw"))
                           if f.lower().endswith(".jpg")])
            if n_images and n_files != n_images:
                return False
        except Exception:
            pass
    return all(os.path.exists(os.path.join(workdir, o)) for o in outputs)


def save_records(workdir, records, meta=None):
    """meta 章节首次写入（向后兼容）：handle/site/season/theme/provider/
    dry_run/strategy/created_at/modules_requested + 场景风格选择。"""
    mp = os.path.join(workdir, "manifest.json")
    m = {}
    if os.path.exists(mp):
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            m = {}
    if meta and "meta" not in m:
        meta = dict(meta)
        meta.setdefault("created_at",
                        datetime.datetime.now().isoformat(timespec="seconds"))
        m["meta"] = meta
    mods = m.get("modules", {})
    mods.update(records)
    m["modules"] = mods
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def print_list():
    print(f"{'模块':<10}{'依赖':<22}{'输出':<32}说明")
    print("-" * 100)
    for name, m in MODULES.items():
        deps = ",".join(m["deps"]) or "-"
        outs = ",".join(m["outputs"])
        print(f"{name:<10}{deps:<22}{outs:<32}{m['desc']}")


def main():
    ap = argparse.ArgumentParser(description="统一调度器：模块单选/多选按需执行")
    ap.add_argument("--handle", help="Shopify product handle")
    ap.add_argument("--site", default="https://manhattanproducts.eu")
    ap.add_argument("--modules", help="逗号分隔，如 ingest,plan,copy")
    ap.add_argument("--all", action="store_true", help="跑全部模块")
    ap.add_argument("--list", action="store_true", help="打印模块表，不执行")
    ap.add_argument("--season", default=None, help="e.g. christmas")
    ap.add_argument("--theme", default="manhattan", choices=["manhattan", "intellinet"])
    ap.add_argument("--strategy", default=None, help="plan.py 人工覆盖配比")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--provider", default=None, choices=["openai", "gemini", "muse"])
    ap.add_argument("--base-url", default=None,
                    help="OpenAI-compatible base URL（透传给 generate）")
    ap.add_argument("--force", action="store_true", help="已有产物也重跑")
    ap.add_argument("--workdir", help="覆盖默认 products/<handle>/")
    ap.add_argument("--scenes", default=None, help="逗号分隔的场景 slot id（透传 plan/generate）")
    ap.add_argument("--scene-add", default=None, action="append",
                    help="自定义场景自由文本，可多次传入（透传 plan/generate）")
    ap.add_argument("--style", default=None, help="风格预设 id（透传 plan/generate）")
    ap.add_argument("--style-add", default=None, help="自定义风格自由文本（透传 plan/generate）")
    args = ap.parse_args()

    if args.list:
        print_list()
        return

    if args.all:
        requested = list(MODULES)
    elif args.modules:
        requested = [m.strip() for m in args.modules.split(",") if m.strip()]
        unknown = [m for m in requested if m not in MODULES]
        if unknown:
            sys.exit(f"[run] 未知模块: {unknown}（用 --list 查看）")
    else:
        sys.exit("[run] 需要 --modules / --all / --list 之一")

    if not args.handle and not args.workdir:
        sys.exit("[run] 需要 --handle（或 --workdir 覆盖）")
    handle = args.handle or os.path.basename(os.path.normpath(args.workdir))
    workdir = args.workdir or os.path.join(BASE_DIR, "products", handle)
    args.workdir = workdir
    args.handle = handle

    ordered = resolve(requested)
    print(f"[run] 执行顺序: {', '.join(ordered)}  (workdir={workdir})")
    os.makedirs(workdir, exist_ok=True)

    meta = {
        "handle": handle,
        "site": args.site,
        "season": args.season,
        "theme": args.theme,
        "provider": args.provider,
        "dry_run": args.dry_run,
        "strategy": args.strategy,
        "modules_requested": requested,
        "scenes": args.scenes,
        "scene_add": args.scene_add,
        "style": args.style,
        "style_add": args.style_add,
    }

    records = {}
    for m in ordered:
        outs = MODULES[m]["outputs"]
        if not args.force and outputs_exist(workdir, outs):
            print(f"[run] skip {m}（产物已存在，加 --force 重跑）")
            records[m] = {"status": "skipped",
                          "time": datetime.datetime.now().isoformat(timespec="seconds"),
                          "outputs": outs}
            save_records(workdir, records, meta)
            continue
        cmd = _module_cmd(MODULES[m]["script"], args_for(m, args))
        print(f"[run] >>> {' '.join(cmd)}")
        r = subprocess.run(cmd)
        if r.returncode != 0:
            records[m] = {"status": "failed",
                          "time": datetime.datetime.now().isoformat(timespec="seconds"),
                          "outputs": outs}
            save_records(workdir, records, meta)
            sys.exit(f"[run] {m} 失败，中止")
        records[m] = {"status": "ok",
                      "time": datetime.datetime.now().isoformat(timespec="seconds"),
                      "outputs": outs}
        save_records(workdir, records, meta)

    print(f"[run] 完成: {len(ordered)} 个模块")


if __name__ == "__main__":
    main()
