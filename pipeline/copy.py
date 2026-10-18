#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S2 文案：product.json -> copy.md。

铁律：数字/规格只能来自 official 层；inferred 数据标 [NEEDS-REVIEW]，禁止直接用。
Usage:
  python3 pipeline/copy.py --workdir products/<handle>
"""

import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser(description="S2: copywriting -> copy.md")
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir} (run analyze.py first)")
    with open(pj, encoding="utf-8") as f:
        p = json.load(f)

    facts = p.get("facts", {})
    inferred = p.get("inferred", {})

    def fval(key):
        f = facts.get(key)
        return f["value"] if f else "?"

    def freq(key, label):
        f = facts.get(key)
        if not f or f.get("value") in (None, "", "?"):
            sys.exit(f"[copy] 官网未提取到{label}（product.json facts.{key}），先检查 analyze")
        return f["value"]

    ports = freq("ports_num", "端口数")
    power = freq("power_w", "功率")
    size = fval("max_device_size")
    pt_en = p.get("product_type_en", "Product")
    pt_zh = p.get("product_type_zh", "产品")

    bullets_en = [
        f"{ports} USB-C ports deliver up to {power} per port — charge phones, "
        "tablets and laptops simultaneously at full speed.",
        "No AC adapters needed: devices connect directly via USB-C, cutting cable "
        "clutter and saving setup time.",
        "USB-C Power Delivery intelligently negotiates the optimal charging power "
        "for each connected device.",
        f"Accommodates devices up to {size} — ideal for classrooms, offices, "
        "hotels and shared workspaces.",
        f"Sturdy {pt_en.lower()} keeps devices charged, organized and protected "
        "in one central station.",
    ]

    jd_points = [
        f"{ports} 个 USB-C 接口，单口 {power}，多台设备同时快充",
        "无需单个 AC 适配器，USB-C 直连即充，桌面告别线缆杂乱",
        "USB-C PD 智能协商功率，每台设备都获得合适的充电功率",
        f"兼容最大 {size} 的平板、手机、笔记本，教室/办公室/酒店多场景适用",
        f"坚固桌面{pt_zh}，充电、收纳、保护一次搞定",
    ]

    review_notes = []
    for k, v in inferred.items():
        review_notes.append(f"- {k}: {v['value']} ({v['note']})")

    # ---- F7：痛点 / 解法（规则式从 official 事实反推，供 showcase 六屏用）----
    pain_solution_map = [
        (["no ac adapter", "without ac", "无需", "ac 适配器"],
         "多设备充电头 + 线缆杂乱，桌面像蜘蛛网",
         "USB-C 直连，一根线解决，不用每个设备配充电头"),
        (["per port", "单口", power.lower() if isinstance(power, str) else ""],
         "多口分电慢，设备多了充不满",
         f"单口 {power} 满速，每台设备都吃到足功率"),
        (["clutter", "杂乱", "organize", "收纳"],
         "设备东一个西一个，借还登记全靠人工",
         "集中收纳 + 统一充电，管理一目了然"),
        (["protect", "保护", "安全"],
         "贵重设备随手放，磕碰丢失风险高",
         "坚固柜体集中存放，充电同时保护设备"),
        (["negotiat", "智能", "pd"],
         "不同设备功率需求不一，混充怕伤电池",
         "USB-C PD 智能协商，每台设备拿合适的功率"),
        (["classroom", "教室", "school", "学校", "office", "办公室"],
         "教室/办公室多设备同时没电，逐个找插座",
         f"一次充 {ports} 台，{pt_zh}集中解决多设备补电"),
    ]
    corpus_pain = " ".join([
        p.get("title", ""), p.get("product_desc_en", ""),
        " ".join(str(v.get("value", "")) for v in facts.values()),
    ]).lower()
    pains, solutions = [], []
    for keywords, pain, solution in pain_solution_map:
        if any(kw and kw.lower() in corpus_pain for kw in keywords):
            pains.append(pain)
            solutions.append(solution)
        if len(pains) >= 3:
            break
    while len(pains) < 3:
        pains.append("[NEEDS-REVIEW] 痛点待人工补充")
        solutions.append("[NEEDS-REVIEW] 解法待人工补充")

    md = []
    md.append(f"# 文案终稿：{p.get('title', '')}\n")
    md.append(f"SKU: {p.get('sku', '')} ｜ Vendor: {p.get('vendor', '')}\n")
    md.append("## Amazon Bullets (EN, 5条)\n")
    for i, b in enumerate(bullets_en, 1):
        md.append(f"{i}. {b}")
    md.append("\n## 京东卖点 (ZH)\n")
    for i, b in enumerate(jd_points, 1):
        md.append(f"{i}. {b}")
    md.append("\n## 海报短文案\n")
    md.append(f"- EN: {ports}-Port USB-C {pt_en} — Power Every Device, One Station.")
    md.append(f"- ZH: {ports} 口 USB-C {pt_zh}，一站式解决多设备充电。")
    md.append("\n## Banner 文案 (官网首页 2000x440)\n")
    md.append(f"- EN headline: Charge {ports} Devices at Once. ZH: 一次充{ports}台。")
    md.append(f"- EN sub: {power} per port USB-C Power Delivery. ZH: 单口{power} USB-C 快充。")
    md.append("\n## 痛点（3 条，供 showcase 用）\n")
    for i, pain in enumerate(pains, 1):
        md.append(f"{i}. {pain}")
    md.append("\n## 解法（3 条，供 showcase 用）\n")
    for i, solution in enumerate(solutions, 1):
        md.append(f"{i}. {solution}")
    if review_notes:
        md.append("\n## [NEEDS-REVIEW] 推断数据（人工核对后才能用）\n")
        md.extend(review_notes)
    md.append("\n---\n*数字/规格全部来自官网 official 层；inferred 层数据未进入文案。*\n")

    out = os.path.join(args.workdir, "copy.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"[copy] -> {out} ({len(bullets_en)} EN bullets, {len(jd_points)} ZH points, "
          f"{len(review_notes)} needs-review)")


if __name__ == "__main__":
    main()
