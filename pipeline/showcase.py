#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S6 套图展示页：product.json + plan.json + copy.md + final/*.jpg
→ showcase.html（六屏落地页式，按痛点型销售逻辑编排）。

数据源：
- 02 痛点 / 03 解法：copy.md 的 "## 痛点" / "## 解法" 小节（F7 copy.py 新增）
- 04 规格参数：product.json official facts
- 图片：final/*.jpg 存在的才渲染，相对路径 final/xxx.jpg
模板占位符用 @@VAR@@ 风格（CSS 里全是 {}，避开 string.Template）。

Usage:
  python3 pipeline/showcase.py --workdir products/<handle> [--theme manhattan] [--season christmas]
"""

import argparse
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPEC_LABELS = {
    "ports_num": "接口",
    "power_w": "单口功率",
    "max_device_size": "兼容尺寸",
    "connector": "接口类型",
    "use_cases": "适用场景",
    "cables_included": "附带线缆",
    "product_name": "产品名称",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>六屏展示页 · @@TITLE@@</title>
<style>
:root{--primary:#017AC3;--headline:#005485;--accent:#E8730C;--bg:#F4F6F8;--muted:#6B7A8D}
*{box-sizing:border-box}body{margin:0;font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#fff;color:#1F2933}
.topbar{border-bottom:1px solid #E5EAF0;padding:14px 0}.topbar-inner{max-width:1100px;margin:0 auto;padding:0 20px}
.logo{font-weight:800;color:var(--headline);font-size:20px}.sub{color:var(--muted);font-size:12px;margin-left:10px;letter-spacing:2px}
.page{max-width:1100px;margin:0 auto;padding:0 20px 60px}
.page-head{padding:44px 0 8px}.page-head h1{font-size:30px;font-weight:800;color:var(--headline)}
.page-head .ver{font-size:13px;color:var(--muted);font-weight:400}
.orange-rule{width:64px;height:4px;background:var(--accent);margin:12px 0}
.sec-kicker{display:flex;align-items:center;gap:14px;margin:56px 0 6px}
.sec-num{display:inline-flex;width:44px;height:44px;border-radius:50%;background:var(--accent);color:#fff;font-weight:800;align-items:center;justify-content:center}
.sec-kicker h2{font-size:24px;font-weight:800;color:var(--headline);margin:0}
.sec-lead{color:var(--muted);font-size:14px;margin:6px 0 18px}
.shot-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:18px;margin-top:6px}
.shot{border:1px solid #E5EAF0;border-radius:12px;overflow:hidden;background:#fff}
.shot .thumb img{width:100%;display:block}
.shot .fname{padding:10px 14px;font-size:13px}
/* 增补五：痛点 / 规格改网格，不再单列堆 */
.point-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.pain-card{border:1px solid #E5EAF0;border-radius:12px;padding:20px;background:#fff;box-shadow:0 2px 8px rgba(0,84,133,.06)}
.pain-num{display:inline-flex;width:34px;height:34px;border-radius:50%;background:var(--accent);color:#fff;font-weight:800;align-items:center;justify-content:center;font-size:14px}
.pain-card b{display:block;margin:12px 0 6px;font-size:16px;color:var(--headline)}
.pain-card p{margin:0;color:var(--muted);font-size:13px;line-height:1.7}
.spec-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.spec-row{display:flex;gap:12px;border:1px solid #E5EAF0;border-radius:10px;padding:14px 16px;background:var(--bg)}
.spec-k{flex:0 0 88px;color:var(--muted);font-size:13px}
.spec-v{font-size:14px;font-weight:600;color:var(--headline)}
.review{border:1px dashed var(--accent);border-radius:10px;padding:10px 14px;color:var(--accent);font-size:13px;margin-top:12px}
footer{border-top:1px solid #E5EAF0;margin-top:60px;padding:24px 20px;text-align:center;color:var(--muted);font-size:13px}
</style>
</head>
<body>
<header class="topbar"><div class="topbar-inner">
<span class="logo">套图工坊</span><span class="sub">MANHATTAN · INTELLINET</span>
</div></header>
<div class="page">
<div class="page-head">
<div class="crumb">任务结果 / 六屏展示页</div>
<h1>六屏展示页 <span class="ver">由管线自动生成</span></h1>
<div class="orange-rule"></div>
<p>@@TITLE@@ · @@SKU@@</p>
</div>

<div class="sec-kicker"><span class="sec-num">01</span><h2>主图</h2></div>
<p class="sec-lead">第一眼：产品是什么，一句话卖点。</p>
<div class="shot-grid">@@SHOTS_MAIN@@</div>

<div class="sec-kicker"><span class="sec-num">02</span><h2>痛点</h2></div>
<p class="sec-lead">说中用户的麻烦。</p>
<div class="point-grid">@@PAIN_CARDS@@</div>
@@PAIN_REVIEW@@

<div class="sec-kicker"><span class="sec-num">03</span><h2>解法</h2></div>
<p class="sec-lead">@@SOLUTION_LEAD@@</p>
<div class="shot-grid">@@SHOTS_SOLUTION@@</div>

<div class="sec-kicker"><span class="sec-num">04</span><h2>规格参数</h2></div>
<p class="sec-lead">理性背书：接口、功率、尺寸，一目了然。</p>
<div class="spec-grid">@@SPEC_ROWS@@</div>

<div class="sec-kicker"><span class="sec-num">05</span><h2>节日行动号召</h2></div>
<p class="sec-lead">氛围 + 促销：一句话让人下单。</p>
<div class="shot-grid">@@SHOTS_SEASON@@</div>

<div class="sec-kicker"><span class="sec-num">06</span><h2>多端展示</h2></div>
<p class="sec-lead">官网横幅 + 手机端，一套图全覆盖。</p>
<div class="shot-grid">@@SHOTS_MULTI@@</div>
</div>
<footer><div>套图工坊 · 文案 + 设计 + 策划 + 运营 + 提示词 + 优化，一站式。</div></footer>
</body>
</html>
"""


def parse_section(md, title):
    """取 copy.md 里 "## <title>" 到下一个 "##" 之间的编号条目列表。"""
    m = re.search(r"^##\s*" + re.escape(title) + r"\s*$", md, re.M)
    if not m:
        return []
    tail = md[m.end():]
    tail = tail.split("\n## ")[0]
    items = []
    for line in tail.splitlines():
        line = line.strip()
        mm = re.match(r"^\d+\.\s*(.+)$", line)
        if mm:
            items.append(mm.group(1).strip())
    return items


def shot_cell(fname, label):
    return (f'<div class="shot"><div class="thumb">'
            f'<img src="final/{fname}" alt="{label}" loading="lazy"></div>'
            f'<div class="fname"><b>{label}</b></div></div>')


def pain_card(i, text):
    # 标题取首句（≤10 字），剩余作描述；NEEDS-REVIEW 的标虚线警示
    title = re.split(r"[，,。；;：:]", text)[0][:10] or text[:10]
    review = "[NEEDS-REVIEW]" in text
    cls = ' class="review"' if review else ""
    return (f'<div class="pain-card"{cls}><span class="pain-num">{i:02d}</span>'
            f"<b>{title}</b><p>{text}</p></div>")


def main():
    ap = argparse.ArgumentParser(description="S6: showcase.html")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--theme", default="manhattan", choices=["manhattan", "intellinet"])
    ap.add_argument("--season", default=None)
    args = ap.parse_args()

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir}")
    p = json.load(open(pj, encoding="utf-8"))

    copy_md = ""
    cp = os.path.join(args.workdir, "copy.md")
    if os.path.exists(cp):
        copy_md = open(cp, encoding="utf-8").read()

    pains = parse_section(copy_md, "痛点（3 条，供 showcase 用）")
    solutions = parse_section(copy_md, "解法（3 条，供 showcase 用）")

    final_dir = os.path.join(args.workdir, "final")
    existing = set(os.listdir(final_dir)) if os.path.isdir(final_dir) else set()

    def shots(*pairs):
        return "".join(shot_cell(f, label) for f, label in pairs if f in existing)

    facts = p.get("facts", {})
    spec_rows = []
    for key, label in SPEC_LABELS.items():
        f = facts.get(key)
        if not f:
            continue
        v = f.get("value")
        if v in (None, "", "?"):
            continue
        v = ", ".join(v) if isinstance(v, list) else str(v)
        spec_rows.append(
            f'<div class="spec-row"><span class="spec-k">{label}</span>'
            f'<span class="spec-v">{v}</span></div>')

    season_files = sorted(f for f in existing
                          if f.startswith("season_") and f.endswith(".jpg"))
    season_label = ""
    if season_files:
        m = re.match(r"season_(.+)\.jpg", season_files[0])
        if m:
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from seasons import SEASONS
                season_label = SEASONS.get(m.group(1), {}).get("label_zh", m.group(1))
            except Exception:
                season_label = m.group(1)

    pain_review = ""
    if any("[NEEDS-REVIEW]" in t for t in pains):
        pain_review = ('<div class="review">部分痛点为规则生成待人工核对，'
                       "确认后更新 copy.md 重跑 showcase。</div>")

    solution_lead = "产品出场：" + (solutions[0] if solutions else "一站式解决。")

    html = TEMPLATE
    html = html.replace("@@TITLE@@", p.get("title", ""))
    html = html.replace("@@SKU@@", "SKU: " + str(p.get("sku", "")))
    html = html.replace("@@SHOTS_MAIN@@", shots(
        ("amazon_main.jpg", "Amazon 主图"), ("jd_main.jpg", "京东主图")))
    html = html.replace("@@PAIN_CARDS@@",
                        "".join(pain_card(i, t) for i, t in enumerate(pains, 1)))
    html = html.replace("@@PAIN_REVIEW@@", pain_review)
    html = html.replace("@@SOLUTION_LEAD@@", solution_lead)
    html = html.replace("@@SHOTS_SOLUTION@@", shots(
        ("amazon_extra_1.jpg", "场景图"), ("amazon_extra_2.jpg", "信息图")))
    html = html.replace("@@SPEC_ROWS@@", "".join(spec_rows))
    html = html.replace("@@SHOTS_SEASON@@", "".join(
        shot_cell(f, f"{season_label}海报" if season_label else "季节海报")
        for f in season_files))
    html = html.replace("@@SHOTS_MULTI@@", shots(
        ("web_banner.jpg", "官网首页大图"), ("mobile.jpg", "手机端")))

    out = os.path.join(args.workdir, "showcase.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[showcase] -> {out} "
          f"({len(pains)} 痛点, {len(spec_rows)} 规格, {len(existing)} final 图)")


if __name__ == "__main__":
    main()
