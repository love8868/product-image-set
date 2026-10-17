#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1b 策划：product.json -> plan.md（人可读可改）+ plan.json（下游读取）。

三型卖点诊断（规则式关键词匹配）→ 图位用途规划（12 图位）→ 视觉合同 STYLE LOCK。
--strategy 可人工覆盖配比，格式：pain:60,visual:30,emotion:10（总和须为 100）。
下游 generate.py / layout.py 可读取 plan.json 中的用途与合同（当前版本未强制接入，接口预留）。

Usage:
  python3 pipeline/plan.py --workdir products/<handle> [--theme manhattan] [--strategy ...]
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import THEMES  # noqa: E402  主题变量唯一来源（转录自 brand-visual-guide.md）
from prompts import style_lock_product  # noqa: E402  产品规范块

# ---- 三型诊断关键词（规则式）----
STRATEGY_KEYWORDS = {
    "visual": ["design", "color", "finish", "premium", "sleek", "modern",
               "material", "aluminum", "texture", "appearance",
               "外观", "质感", "颜值", "材质", "做工"],
    "pain": ["no need", "without", "clutter", "easy", "save", "solve",
             "problem", "hassle", "neat", "organize", "protect",
             "痛点", "解决", "省心", "麻烦", "杂乱", "告别"],
    "emotion": ["lifestyle", "enjoy", "love", "perfect", "ideal", "home",
               "family", "情感", "生活", "热爱", "氛围"],
}
STRATEGY_ZH = {"visual": "视觉型", "pain": "痛点型", "emotion": "情感型"}
STRATEGY_TAGLINE = {
    "pain": "先问问题，再给解法",
    "visual": "靠颜值与质感",
    "emotion": "靠身份与情绪",
}

# ---- 12 图位：8 个已产出 + 4 个扩展预留 ----
SLOTS = [
    ("amazon_main", "白底主图", "合规主图（纯白底实拍，Tier 0）", "visual", "produced", "amazon_main.jpg"),
    ("amazon_extra_1", "场景图", "结论先行 + 场景证据", "pain", "produced", "amazon_extra_1.jpg"),
    ("amazon_extra_2", "信息图", "卖点证据陈列（一句话一条）", "pain", "produced", "amazon_extra_2.jpg"),
    ("jd_main", "京东主图", "干净首图 + 卖点徽章", "visual", "produced", "jd_main.jpg"),
    ("jd_detail", "京东详情", "卖点 + 规格说明", "pain", "produced", "jd_detail.jpg"),
    ("web_banner", "官网首页", "品牌主张传达", "visual", "produced", "web_banner.jpg"),
    ("mobile", "手机端", "小屏快速传达（拇指区）", "pain", "produced", "mobile.jpg"),
    ("season_poster", "季节海报", "节日氛围 + 行动召唤", "emotion", "produced", "season_{season}.jpg"),
    ("amazon_extra_3", "细节特写", "做工 / 材质证据", "visual", "planned", "amazon_extra_3.jpg"),
    ("amazon_extra_4", "尺寸参照", "规格可视化", "pain", "planned", "amazon_extra_4.jpg"),
    ("jd_detail_2", "参数规格表", "完整参数陈列", "pain", "planned", "jd_detail_2.jpg"),
    ("season_poster_2", "节日变体", "多节日覆盖", "emotion", "planned", "season_{season}_2.jpg"),
]

THEME_TONE = {
    "manhattan": {
        "tone": "中性偏冷，明亮通透",
        "lighting": "柔和明亮的自然光 / 影棚柔光，产品下极淡自然阴影，无戏剧化暗角",
        "composition": "对称稳定，大留白（≥30%），标题左上 + 橙色短下划线，产品按真实比例陈列",
    },
    "intellinet": {
        "tone": "冷，深色科技",
        "lighting": "戏剧化边缘光 / rim light，产品带地面反射，背景有明暗层次",
        "composition": "产品居中 hero，对角线引导（光 streak），橙色 pill 做型号 / 参数标注",
    },
}


def diagnose(p, workdir):
    """规则式三型打分：关键词在标题/描述/事实/官网正文中的命中数 → 配比。
    官网 body_html 纳入语料（最丰富的官方表述）；+2 平滑避免单次误命中导致 100% 偏斜。"""
    raw_path = os.path.join(workdir, "product_raw.json")
    body = ""
    if os.path.exists(raw_path):
        try:
            with open(raw_path, encoding="utf-8") as f:
                raw = json.load(f)
            body = re.sub(r"<[^>]+>", " ", raw.get("body_html", "") or "")
        except Exception:
            pass
    corpus = " ".join([
        p.get("title", ""), p.get("product_desc_en", ""),
        " ".join(str(v.get("value", "")) for v in p.get("facts", {}).values()),
        " ".join(p.get("target_scenes", [])),
        body,
    ]).lower()
    scores = {}
    for k, words in STRATEGY_KEYWORDS.items():
        scores[k] = 2 + sum(len(re.findall(re.escape(w.lower()), corpus)) for w in words)
    total = sum(scores.values())
    return {k: round(v / total * 100) for k, v in scores.items()}


def parse_strategy(s):
    parts = {}
    for chunk in s.split(","):
        k, v = chunk.split(":")
        k, v = k.strip(), int(v.strip())
        if k not in STRATEGY_KEYWORDS:
            raise ValueError(f"unknown strategy type: {k}")
        parts[k] = v
    if sum(parts.values()) != 100:
        raise ValueError(f"--strategy 总和须为 100，当前 {sum(parts.values())}")
    return parts


def main():
    ap = argparse.ArgumentParser(description="S1b: 策划 -> plan.md + plan.json")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--theme", default="manhattan", choices=["manhattan", "intellinet"])
    ap.add_argument("--strategy", default=None,
                    help="人工覆盖配比，如 pain:60,visual:30,emotion:10")
    args = ap.parse_args()

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir} (run analyze.py first)")
    with open(pj, encoding="utf-8") as f:
        p = json.load(f)

    pt_zh = p.get("product_type_zh", "产品")
    desc_en = p.get("product_desc_en", p.get("title", "product"))

    # ---- 三型诊断 ----
    mix = parse_strategy(args.strategy) if args.strategy else diagnose(p, args.workdir)
    primary = max(mix, key=mix.get)
    taglines = {"pain": f"这款{pt_zh}，靠痛点卖。",
                "visual": f"这款{pt_zh}，靠质感赢。",
                "emotion": f"这款{pt_zh}，靠场景打动人。"}

    # ---- 视觉合同（12 张共享，逐条可改）----
    th = THEMES[args.theme]
    tone = THEME_TONE[args.theme]
    style_lock = [
        {"id": "01", "item": "配色",
         "value": (f"背景 {th['background']}（主）/ {th['bg_alt']}（辅助）；正文 {th['text']}；"
                   f"主色 {th['primary']}；标题 {th['headline']}；强调橙 {th['accent']}（仅点缀，≤10% 面积）"),
         "editable": True},
        {"id": "02", "item": "色调", "value": tone["tone"], "editable": True},
        {"id": "03", "item": "光影系统", "value": tone["lighting"], "editable": True},
        {"id": "04", "item": "布局构成", "value": tone["composition"], "editable": True},
        {"id": "05", "item": "产品规范", "value": style_lock_product(desc_en), "editable": True},
        {"id": "06", "item": "字体系统",
         "value": ("大标题 800 / 正文 500 / 数据 600 三级；英文粗无衬线，中文思源黑体系；"
                   "当前管线临时用 Noto Sans CJK，商用授权待确认后锁定"),
         "editable": True},
        {"id": "07", "item": "通用铁律",
         "value": ("底色≥70%、主色~20%、强调橙≤10%；产品本身不参与主题配色；"
                   "浅底用深字、深底用白字，压图加 40–60% 罩；同一产品整套图字体/字重/配色比例全程一致"),
         "editable": True},
        {"id": "08", "item": "文字规范",
         "value": "无字底图 + Pillow 后期叠字（模型不画字）；最小字号不低于 2%H，低于则删文案",
         "editable": True},
    ]

    slots = []
    for key, name, purpose, stype, status, outfile in SLOTS:
        slots.append({
            "key": key, "name_zh": name, "purpose": purpose,
            "strategy_type": STRATEGY_ZH[stype],
            "primary_match": (stype == primary),
            "status": status, "output": outfile,
            # scene_extra: prompt 模板 $scene_extra 变量的来源（plan.py 拥有该字段）；
            # 规则生成，当前无规则填空字符串；人工可在 plan.md 改完后同步到此处
            "scene_extra": "",
        })

    plan = {
        "handle": p.get("handle"),
        "theme": args.theme,
        "strategy_mix": {STRATEGY_ZH[k]: v for k, v in mix.items()},
        "primary_strategy": STRATEGY_ZH[primary],
        "primary_tagline": taglines[primary],
        "slots": slots,
        "style_lock": style_lock,
        "note": "下游 generate.py / layout.py 可读取本 plan.json（当前版本未强制接入，接口预留）",
    }
    with open(os.path.join(args.workdir, "plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    # ---- plan.md（人可读可改）----
    md = [f"# 策划案：{p.get('title', '')}\n"]
    md.append(f"主题：{args.theme} ｜ SKU：{p.get('sku', '')}\n")
    md.append("## 三型卖点诊断（规则式，可 --strategy 覆盖）\n")
    for k in ("visual", "pain", "emotion"):
        bar = "█" * (mix[k] // 5) + "░" * (20 - mix[k] // 5)
        md.append(f"- {STRATEGY_ZH[k]} {mix[k]}% {bar}（{STRATEGY_TAGLINE[k]}）")
    md.append(f"\n**主打策略：{taglines[primary]}**\n")
    md.append("## 图位用途规划（12 图位）\n")
    md.append("| 图位 | 用途 | 策略类型 | 状态 | 输出文件 |")
    md.append("|---|---|---|---|---|")
    for s in slots:
        star = " ★主打" if s["primary_match"] else ""
        md.append(f"| {s['name_zh']} | {s['purpose']} | {s['strategy_type']}{star} "
                  f"| {s['status']} | {s['output']} |")
    md.append("\n## 视觉合同 STYLE LOCK（12 张共享，逐条可改）\n")
    for e in style_lock:
        md.append(f"**{e['id']} {e['item']}**：{e['value']}\n")
    md.append("---\n*plan.md 可人工修改后重跑下游；plan.json 供脚本读取。*\n")
    with open(os.path.join(args.workdir, "plan.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"[plan] mix={mix} primary={primary}")
    print(f"[plan] -> {args.workdir}/plan.md + plan.json "
          f"({len(slots)} slots, {len(style_lock)} lock entries)")


if __name__ == "__main__":
    main()
