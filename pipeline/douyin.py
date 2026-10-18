#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抖音文案：product.json（official 层）+ plan.json（三型策略）→ douyin_copy.md。

模板范例：products/manhattan-en-10-port-usb-c-desktop-charging-cabinet-30w-per-port-181488/douyin_copy.md
三型策略决定钩子角度：痛点型→痛点钩子开场，视觉型→颜值/质感开场，情感型→身份/场景开场。

Usage:
  python3 pipeline/douyin.py --workdir products/<handle>
"""

import argparse
import json
import os
import re
import sys

VENDOR_ZH = {"Manhattan": "曼哈顿", "Intellinet": "英特奈特"}
SCENE_ZH = {
    "office desk": "办公室", "classroom": "教室", "hotel lobby": "酒店",
    "home study": "书房", "doctor": "诊所", "gym": "健身房",
    "hospital": "医院", "hotel": "酒店", "office": "办公室",
    "restaurant": "餐厅", "school": "学校", "university": "大学",
}


def official(facts, key):
    f = facts.get(key, {})
    if f.get("level") != "official" or not f.get("value"):
        sys.exit(f"[douyin] 缺少 official 事实: {key}，先检查 analyze.py 输出")
    return f["value"]


def zh_inch(v):
    return re.sub(r"\s*inch\b", " 英寸", str(v)).strip()


def scene_zh(s):
    return SCENE_ZH.get(str(s).strip().lower(), str(s))


def main():
    ap = argparse.ArgumentParser(description="douyin copy: product.json + plan.json -> douyin_copy.md")
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir} (run analyze.py first)")
    p = json.load(open(pj, encoding="utf-8"))
    facts = p.get("facts", {})

    n = official(facts, "ports_num")          # "10"
    power = official(facts, "power_w")        # "30W"
    connector = official(facts, "connector")  # "USB-C"
    size_zh = zh_inch(official(facts, "max_device_size"))  # "14 英寸"
    use_cases = official(facts, "use_cases")  # list
    scenes = [scene_zh(s) for s in use_cases[:3]]
    while len(scenes) < 3:
        scenes.append(scenes[0] if scenes else "办公室")

    type_zh = p.get("product_type_zh") or "充电设备"
    vendor = p.get("vendor", "")
    brand_zh = VENDOR_ZH.get(vendor, vendor)
    sku = p.get("sku", "")
    conn_tag = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", connector)

    plan_path = os.path.join(args.workdir, "plan.json")
    strategy = "痛点型"
    if os.path.exists(plan_path):
        strategy = json.load(open(plan_path, encoding="utf-8")).get("primary_strategy", "痛点型")

    # ---- 钩子（按三型策略） ----
    if strategy == "视觉型":
        hook_a = f"开箱！这个{type_zh}颜值直接拉满，{n}台设备一次充完⚡"
        hook_b = f"{brand_zh}{type_zh}，把充电这件事做成了艺术品✨"
        s0_3s = f"看这个{type_zh}的颜值，放在桌面上就是一件艺术品！"
        s3_10s = "全金属机身，做工整齐划一，指示灯一亮，科技感直接拉满。"
    elif strategy == "情感型":
        hook_a = f"{scenes[0]}人的桌面，都该有这样一个{type_zh}💼"
        hook_b = f"高效人士的标配：{n}台设备，一个{type_zh}全搞定🔌"
        s0_3s = f"{scenes[0]}的高效人士，桌面都长这样！"
        s3_10s = "每天一到工位，设备往里一放，电量焦虑？不存在的。"
    else:  # 痛点型（默认）
        hook_a = f"{scenes[0]}{n}台设备，怎么充电才不乱？答案是一个{type_zh}全搞定🔌"
        hook_b = f"{scenes[0]}、{scenes[1]}、{scenes[2]}都在用的充电神器，一台顶{n}台充电头⚡"
        s0_3s = f"你敢信？{scenes[0]}的设备充电，全靠这一个{type_zh}！"
        s3_10s = "以前啊，每台设备配一个充电头，插座不够用，线缠成一团，收一次充电器就得半小时。"

    tags = f"#{type_zh} #{scenes[0]}装备 #{scenes[1]}好物 #{conn_tag}快充 #桌面收纳"

    md = f"""# 抖音文案：{p.get('title', '')}

> 基于官网事实：{n} 个 {connector} 口、单口 {power}、{type_zh}、兼容 {size_zh}以下手机/平板/笔记本，适用{'/'.join(scenes)}。主打{strategy}（plan 诊断）。

---

## 一、发布文案（标题 + 话题）

**版本 A（{strategy}钩子）**
```
{hook_a}
{n}口{connector}同时快充，单口{power}，不用抢插座，桌面告别蜘蛛网
{tags}
```

**版本 B（场景种草）**
```
{hook_b}
{tags}
```

---

## 二、口播脚本（30 秒版）

| 时间 | 画面 | 口播 |
|---|---|---|
| 0–3s | {strategy}钩子画面 | "{s0_3s}" |
| 3–10s | 痛点/质感画面 | "{s3_10s}" |
| 10–22s | {type_zh}特写：{n} 个 {connector} 口，逐台插入设备，指示灯亮起 | "看，{n}口{connector}，单口{power}，{n}台设备同时满速充。不用 AC 适配器，一根线进，桌面干干净净。{size_zh}以下的手机、平板、笔记本全兼容。" |
| 22–30s | 整洁桌面 + {type_zh}全景，字幕引导评论 | "{'、'.join(scenes)}都适用。评论区聊聊，你们那儿是怎么给设备充电的？" |

---

## 三、口播脚本（15 秒极速版）

| 时间 | 画面 | 口播 |
|---|---|---|
| 0–3s | {type_zh}开箱/全景 | "{n}台设备同时充电，只需要这一个{type_zh}。" |
| 3–10s | 插线演示快剪 | "{n}口{connector}，单口{power}，告别充电头大战。" |
| 10–15s | 整洁桌面定格 | "{brand_zh}{type_zh}，{scenes[0]}{scenes[1]}标配。" |

---

## 四、评论区维护话术

- 问价格："这款是商用级的，具体可以看官网 {sku} 这个型号，私信发你链接"
- 问兼容："{size_zh}以下的手机、平板、笔记本都兼容，{connector}口即插即充"
- 抬杠"太贵了"："商用场景算的是人工和安全账，省下的时间和精力，你品品"

---

*数字/规格全部来自官网 official 层；inferred 层数据未使用。上架前按 ops-checklist 复核。*
"""

    out = os.path.join(args.workdir, "douyin_copy.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[douyin] 策略={strategy} -> {out}")


if __name__ == "__main__":
    main()
