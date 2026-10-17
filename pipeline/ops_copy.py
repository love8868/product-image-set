#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S2b 运营文案包：product.json -> ops_copy.md + ops-checklist.md。

与 copy.py 分工：copy.py 负责"图上文案"（bullets/卖点/海报/banner）；
本文件负责"运营文案"（search terms / A+ / 京东商详 / 上架 checklist）。
铁律：数字/规格只能来自 official 层；缺失事实直接报错，不编造。

Usage:
  python3 pipeline/ops_copy.py --workdir products/<handle>
"""

import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser(description="S2b: 运营文案包")
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir} (run analyze.py first)")
    with open(pj, encoding="utf-8") as f:
        p = json.load(f)

    facts = p.get("facts", {})
    vendor = p.get("vendor", "Manhattan") or "Manhattan"
    pt_en = p.get("product_type_en", "Charging Cabinet")
    pt_zh = p.get("product_type_zh", "充电柜")
    title = p.get("title", "")

    def fval(k):
        f = facts.get(k)
        return f["value"] if f else "?"

    def freq(k, label):
        v = fval(k)
        if v in ("?", "", None):
            sys.exit(f"[ops_copy] 官网未提取到{label}（product.json facts.{k}），先检查 analyze")
        return v

    ports = freq("ports_num", "端口数")
    power = freq("power_w", "功率")
    size = fval("max_device_size")
    use_cases = fval("use_cases")
    use_cases = use_cases if isinstance(use_cases, list) else []

    md = [f"# 运营文案包：{title}\n"]
    md.append(f"SKU: {p.get('sku', '')} ｜ Vendor: {vendor}\n")

    # ---- Amazon 后台 search terms（250 字节规则，字节安全截断）----
    terms = [
        f"{ports}-port usb-c charging cabinet",
        f"{power} per port", "usb-c charging station",
        f"desktop {pt_en.lower()}", vendor.lower(),
        "tablet charging cart", "usb-c power delivery",
        "no ac adapter", "classroom charging station",
    ] + [u.replace("_", " ") for u in use_cases[:6]]
    seen, uniq = set(), []
    for t in terms:
        t = t.strip().lower()
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    joined, buf = "", ""
    for t in uniq:  # 字节安全截断：Amazon 上限 250 bytes
        cand = (buf + " " + t).strip() if buf else t
        if len(cand.encode("utf-8")) > 250:
            break
        buf = cand
    joined = buf
    md.append("## Amazon 后台 Search Terms（≤250 bytes）\n")
    md.append(f"`{joined}`\n")
    md.append(f"字节数：{len(joined.encode('utf-8'))} / 250\n")
    md.append("⚠️ [NEEDS-REVIEW] 请结合竞品评论高频词人工补充后再填入后台。\n")

    # ---- A+ 页面文案（4 模块）----
    md.append("\n## A+ 页面文案（4 模块）\n")
    md.append(f"### 模块 1：品牌故事\n{vendor} —— Life just got easier. "
              f"这款 {ports} 口 USB-C {pt_zh} 为多设备场景而生："
              "教室、办公室、酒店、共享空间，一台设备解决所有充电与收纳。\n")
    md.append("### 模块 2：功能横幅\n"
              f"**一次充 {ports} 台，告别适配器杂乱。**\n"
              f"- {ports} 个 USB-C 接口，单口 {power}，多台设备同时满速\n"
              "- USB-C 直连，无需单个 AC 适配器\n"
              "- PD 智能协商，每台设备都拿到合适的功率\n")
    md.append("### 模块 3：对比表\n")
    md.append("|  | 本产品 | 传统排插 + 适配器 |")
    md.append("|---|---|---|")
    md.append(f"| 接口 | {ports}× USB-C | 需自备多个适配器 |")
    md.append(f"| 单口功率 | {power} PD 快充 | 参差不齐 |")
    md.append("| 收纳 | 一体柜体，整洁保护 | 线缆杂乱 |")
    md.append("| 适用 | 教室/办公/酒店 | 家用为主 |")
    md.append("\n### 模块 4：场景图配文\n")
    md.append("- 教室：课间 10 分钟，30 台平板同时回血\n"
              "- 办公室：共享工位不再抢插座\n"
              "- 酒店前台：客人借充电，像借雨伞一样简单\n")

    # ---- 京东商详长文案（五段式：全貌→证据→场景→规格→保障）----
    md.append("\n## 京东商详长文案（五段式）\n")
    md.append(f"### 一、全貌（结论）\n{ports} 口 USB-C {pt_zh}，单口 {power}，"
              "一台解决多设备充电、收纳、保护。\n")
    md.append("### 二、证据\n"
              f"- {ports} 个 USB-C 接口，单口 {power} PD 快充，多台同时满速\n"
              "- USB-C 直连：不需要单个 AC 适配器，桌面告别线缆杂乱\n"
              "- PD 智能协商功率，每台设备自动匹配\n")
    md.append("### 三、场景\n- 学校教室：平板统一充电管理\n"
              "- 办公室：共享设备集中补给\n- 酒店/健身房：公用设备随时可用\n")
    md.append("### 四、规格\n"
              f"- 端口：{ports}× USB-C，单口 {power}\n"
              f"- 兼容：最大 {size} 设备\n"
              f"- 形态：桌面{pt_zh}\n"
              "（完整规格以官网 Specifications 页为准，上架前逐项核对）\n")
    md.append("### 五、保障\n- 坚固柜体，设备集中保护\n"
              "- 品牌售后支持\n- 规格真实，参数以官网为准\n")
    md.append("\n---\n*数字/规格全部来自官网 official 层；[NEEDS-REVIEW] 项须人工核对后使用。*\n")

    out = os.path.join(args.workdir, "ops_copy.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"[ops_copy] -> {out}")

    # ---- 上架规范 checklist ----
    ck = [f"# 上架规范 Checklist：{title}\n",
          "## Amazon 主图规范复核（官方 Seller Central）",
          "- [ ] 长边 ≥1000px（推荐 2000px），有缩放功能",
          "- [ ] 纯白底 RGB(255,255,255)，无偏灰/米白",
          "- [ ] 产品占画面 ≥85%，无文字/logo/水印/边框",
          "- [ ] 只展示实际在售商品，无道具、无多余配件",
          "- [ ] 格式 JPEG（首选）/TIFF/PNG，非动态 GIF；禁用 WebP",
          "- [ ] sRGB 色彩；单张 ≤10MB",
          "- [ ] 文件名含产品标识（ASIN/UPC/EAN）",
          "- [ ] 无 Amazon 徽标/Prime/Alexa 字样，无 Best Seller 类徽章",
          "",
          "## 京东规范复核（社区通行值，上架前请在商家后台复核最新值）",
          "- [ ] 主图 800×800 起步（推荐 1200×1200），1:1，JPEG ≤1MB",
          "- [ ] 白底为主、居中完整展示，多张主图不同角度",
          "- [ ] 无与所售商品无关的物体；无非等比拉伸变形",
          "- [ ] 详情图宽 750，JPG/PNG/GIF，单张 ≤3MB，静态图",
          "",
          "## 文件命名规范",
          "- [ ] 格式：`项目名-日期-版本号`（如 manhattan-181488-20261018-v1）",
          "- [ ] 确认版锁定后不覆盖，改版递增版本号",
          "- [ ] 分层源文件 / 可编辑稿单独归档",
          "",
          "## 文案终审",
          "- [ ] 数字/规格与官网 Specifications 页逐项核对",
          "- [ ] [NEEDS-REVIEW] 项已人工确认或删除",
          "- [ ] 无功效/认证承诺性表述（避免虚假宣传风险）",
          ]
    ckout = os.path.join(args.workdir, "ops-checklist.md")
    with open(ckout, "w", encoding="utf-8") as f:
        f.write("\n".join(ck) + "\n")
    print(f"[ops_copy] -> {ckout}")


if __name__ == "__main__":
    main()
