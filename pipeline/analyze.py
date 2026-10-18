#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1 分析：规则式提取 body_html -> product.json（事实分级 official/visible/inferred）。

--vision 预留 gpt-4o 视觉分析对接口（stub：无 Key 时提示去 README）。
文案出口唯一在 copy.py（本文件不生成 selling_points）。
Usage:
  python3 pipeline/analyze.py --workdir products/<handle> [--vision]
"""

import argparse
import html
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 规则式提取（official 层：全部来自官网 JSON）----

PATTERNS = [
    ("ports", re.compile(r"(\d+)\s*[-–]?\s*ports?\b", re.I), "端口数"),
    ("power_per_port", re.compile(r"(\d+)\s*W\s*per\s*port", re.I), "单口功率"),
    ("max_device_size", re.compile(r"up to\s*(\d+)\s*(?:inch|in\.?)\b", re.I), "最大兼容设备尺寸"),
    ("connector", re.compile(r"\b(USB-C|USB C|Type-C)\b", re.I), "接口类型"),
]

# (匹配 pattern, 展示英文, 展示中文) —— 匹配用 pattern，展示用完整词
USE_CASES = [
    ("school", "school", "学校"),
    ("hotel", "hotel", "酒店"),
    ("office", "office", "办公室"),
    ("restaurant", "restaurant", "餐厅"),
    ("gym", "gym", "健身房"),
    ("hospital", "hospital", "医院"),
    ("doctor", "doctor", "诊所"),
    (r"universit(?:y|ies)", "university", "大学"),
    ("classroom", "classroom", "教室"),
    ("church", "church", "教堂"),
]
USE_CASE_ZH = {en: zh for _, en, zh in USE_CASES}

PRODUCT_TYPES = [
    (r"charging\s+cabinet", "Charging Cabinet", "充电柜"),
    (r"charging\s+cart", "Charging Cart", "充电推车"),
    (r"charging\s+kiosk", "Charging Kiosk", "充电柜"),
    (r"charging\s+station", "Charging Station", "充电站"),
]


def fact(value, level, note=""):
    return {"value": value, "level": level, "note": note}


def detect_product_type(title):
    for pat, en, zh in PRODUCT_TYPES:
        if re.search(pat, title, re.I):
            return en, zh
    return "Product", "产品"


def extract(title, body_html):
    text = f"{title}\n{html.unescape(re.sub(r'<[^>]+>', ' ', body_html or ''))}"
    facts = {}
    for key, pat, _label in PATTERNS:
        m = pat.search(text)
        if m:
            val = m.group(0).strip()
            if key == "max_device_size":
                val = f"{m.group(1)} inch"  # 去掉 "up to" 前缀，模板里统一加
            facts[key] = fact(val, "official", "regex from title/body_html")
    # use cases（展示用完整英文词）
    found = sorted({en for pat, en, _zh in USE_CASES if re.search(pat, text, re.I)})
    if found:
        facts["use_cases"] = fact(found, "official", "keywords found in body_html")
    # cables included?
    if re.search(r"includ\w*\s+USB-C\s+charging\s+cables?", text, re.I):
        facts["cables_included"] = fact(True, "official", "body_html mentions included cables")
    facts["product_name"] = fact(title.strip(), "official", "JSON title")
    return facts


def build_product_json(raw):
    title = raw.get("title", "")
    facts = extract(title, raw.get("body_html", ""))

    def val(key, default=None):
        f = facts.get(key)
        return f["value"] if f else default

    # inferred 层：明确标注，禁止直接进文案数字
    inferred = {
        "color": fact("black (typical for this line)", "inferred",
                      "verify against raw/01.jpg before use"),
        "form": fact("desktop cabinet with front-facing ports", "inferred",
                     "verify against raw images"),
    }

    # 归一化数字事实（供文案/排版直接用，避免 "10-Port 口" 这类拼接重复）
    ports_raw = val("ports", "") or ""
    m = re.search(r"(\d+)", ports_raw)
    if m:
        facts["ports_num"] = fact(m.group(1), "official", "digits extracted from ports")
    pow_raw = val("power_per_port", "") or ""
    m = re.search(r"(\d+\s*W)", pow_raw, re.I)
    if m:
        facts["power_w"] = fact(m.group(1).upper().replace(" ", ""), "official",
                                "normalized from power_per_port")

    images = [f"raw/{i:02d}.jpg" for i in range(1, len(raw.get("images", [])) + 1)]
    pt_en, pt_zh = detect_product_type(title)

    return {
        "handle": raw.get("handle"),
        "title": title,
        "vendor": raw.get("vendor"),
        "sku": (raw.get("variants") or [{}])[0].get("sku"),
        "product_type_en": pt_en,
        "product_type_zh": pt_zh,
        "facts": facts,
        "inferred": inferred,
        "target_scenes": ["office desk", "classroom", "hotel lobby", "home study"],
        "visual_keywords": ["black metal cabinet", "front USB-C ports",
                            "LED indicators", "ventilated slots"],
        "images": images,
        "hero_image": images[0] if images else None,
        "product_desc_en": f"{title} -- {pt_en.lower()}",
    }


def main():
    ap = argparse.ArgumentParser(description="S1: rule-based analysis -> product.json")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--vision", action="store_true",
                    help="reserved: gpt-4o vision analysis (stub)")
    args = ap.parse_args()

    raw_path = os.path.join(args.workdir, "product_raw.json")
    if not os.path.exists(raw_path):
        sys.exit(f"product_raw.json not found in {args.workdir} (run ingest.py first)")
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)

    if args.vision:
        # STUB: wire OPENAI_API_KEY + gpt-4o vision here (see README)
        print("[analyze] --vision requested but no API key wired yet "
              "(see README 'API Key 对接方法'). Falling back to rule-based extraction.")

    product = build_product_json(raw)
    out = os.path.join(args.workdir, "product.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(product, f, ensure_ascii=False, indent=2)
    n_off = sum(1 for v in product["facts"].values() if v["level"] == "official")
    print(f"[analyze] facts: {n_off} official, "
          f"{len(product['inferred'])} inferred (NEEDS-REVIEW before copy)")
    print(f"[analyze] -> {out}")


if __name__ == "__main__":
    main()
