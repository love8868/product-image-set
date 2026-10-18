# -*- coding: utf-8 -*-
"""产品类型 → 场景 / 风格 / 模板推荐映射表（v0.3.0）。

照抄 seasons.py 模式：纯数据 + recommend()。
关键词扫 product.json 的 title + product_desc_en + facts 文本（含英文），
命中多条取并集去重，啥都没命中走默认。

recommend(product) -> (scenes, styles, templates) 三元组。
"""

# ---- 场景池：id -> {label_zh, scene_en} ----
SCENE_POOL = {
    "office": {
        "label_zh": "办公室",
        "scene_en": "modern office desk scene, product on a clean desk next to laptop",
    },
    "classroom": {
        "label_zh": "教室",
        "scene_en": "bright classroom scene, rows of desks, product on teacher's desk",
    },
    "hotel_desk": {
        "label_zh": "酒店前台",
        "scene_en": "hotel front desk scene, warm lobby lighting, product on reception counter",
    },
    "meeting_room": {
        "label_zh": "会议室",
        "scene_en": "conference room scene, long meeting table, product at the center",
    },
    "home_desk": {
        "label_zh": "居家书桌",
        "scene_en": "cozy home office desk scene, warm daylight, product beside monitor",
    },
    "gaming_setup": {
        "label_zh": "电竞桌",
        "scene_en": "gaming setup scene, RGB ambient glow, product on gaming desk",
    },
    "server_room": {
        "label_zh": "机房",
        "scene_en": "server room scene, rack cabinets with blinking LEDs, product on rack shelf",
    },
    "network_closet": {
        "label_zh": "弱电间",
        "scene_en": "network closet scene, patch panels and cable management, product mounted",
    },
}

# ---- 产品类型 → 推荐 ----
# 每个条目：关键词列表（小写子串匹配）+ 推荐的场景/风格/模板 id
PRODUCT_SCENES = {
    "charging_cabinet": {
        "keywords": ["charging", "cabinet", "充电"],
        "scenes": ["office", "classroom", "hotel_desk", "meeting_room"],
    },
    "screen_cleaner": {
        "keywords": ["clean", "清洁"],
        "scenes": ["office", "home_desk", "gaming_setup"],
    },
    "switch": {
        "keywords": ["switch", "交换机", "network"],
        "scenes": ["server_room", "office", "network_closet"],
    },
}

PRODUCT_STYLES = {
    "charging_cabinet": {
        "keywords": ["charging", "cabinet", "充电"],
        "styles": ["modern", "nordic", "light_luxury"],
    },
    "screen_cleaner": {
        "keywords": ["clean", "清洁"],
        "styles": ["modern", "nordic", "japandi"],
    },
    "switch": {
        "keywords": ["switch", "交换机", "network"],
        "styles": ["industrial", "tech_future", "dark_premium"],
    },
}

PRODUCT_TEMPLATES = {
    "charging_cabinet": {
        "keywords": ["charging", "cabinet", "充电"],
        "templates": ["detail_ports", "comparison", "spec_sheet"],
    },
    "screen_cleaner": {
        "keywords": ["clean", "清洁"],
        "templates": ["comparison", "usage_steps"],
    },
    "switch": {
        "keywords": ["switch", "交换机", "network"],
        "templates": ["detail_ports", "spec_sheet"],
    },
}

DEFAULT_SCENES = ["office"]
DEFAULT_STYLES = ["modern"]


def _corpus(product):
    """推荐用的匹配语料：title + desc + facts 值，全部小写。"""
    facts = product.get("facts", {})
    fact_text = " ".join(
        str(v.get("value", "")) for v in facts.values() if isinstance(v, dict)
    )
    return " ".join([
        product.get("title", ""),
        product.get("product_desc_en", ""),
        product.get("product_type_en", ""),
        product.get("product_type_zh", ""),
        fact_text,
    ]).lower()


def _match(table, corpus, field):
    out = []
    for _key, entry in table.items():
        if any(kw.lower() in corpus for kw in entry["keywords"]):
            out.extend(entry[field])
    # 去重保序
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def recommend(product):
    """product: product.json dict。返回 (scenes, styles, templates) 三元组。"""
    corpus = _corpus(product)
    scenes = _match(PRODUCT_SCENES, corpus, "scenes") or list(DEFAULT_SCENES)
    styles = _match(PRODUCT_STYLES, corpus, "styles") or list(DEFAULT_STYLES)
    templates = _match(PRODUCT_TEMPLATES, corpus, "templates")  # 可为空：全列表按 order 展示
    return scenes, styles, templates


def list_scenes():
    return [(k, v["label_zh"]) for k, v in SCENE_POOL.items()]
