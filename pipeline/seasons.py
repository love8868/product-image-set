# -*- coding: utf-8 -*-
"""Season / holiday configuration.

Each entry: English scene prompt fragment (for image generation) + palette hints
(for Pillow text overlay) + Chinese label. Covers four seasons + major European holidays.

Poster fields (for layout.py season_poster, per design/layout-design-specs.md §6):
- poster_bg: [top, bottom] gradient for the title zone (节日氛围只做标题区/行动区)
- poster_text: headline text color on the title zone
- poster_accent: small-area accent color (gold/orange)
- poster_title_zh / poster_title_en / poster_sub_zh / poster_sub_en:
  subtitle templates support {ports} {power} {pt_zh} {pt_en} placeholders.
"""

SEASONS = {
    "spring": {
        "label_zh": "春季",
        "scene_en": (
            "fresh spring scene, soft morning light, light green leaves and subtle "
            "blossom petals in the blurred background, airy and clean composition"
        ),
        "palette": ["#F4F8F4", "#2E7D4F", "#1F2933"],
        "accent_zh": "清新绿",
        "poster_bg": ["#E8F5E9", "#C8E6C9"],
        "poster_text": "#1F2933",
        "poster_accent": "#7CB342",
        "poster_title_zh": "春日焕新 · 高效充电",
        "poster_title_en": "Spring Refresh, Power Up",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "summer": {
        "label_zh": "夏季",
        "scene_en": (
            "bright summer scene, crisp daylight, light blue tones with a hint of "
            "sunlit warmth, clean minimal background, energetic and fresh"
        ),
        "palette": ["#F2F7FB", "#2F80ED", "#1F2933"],
        "accent_zh": "清凉蓝",
        "poster_bg": ["#E1F5FE", "#B3E5FC"],
        "poster_text": "#1F2933",
        "poster_accent": "#039BE5",
        "poster_title_zh": "夏日清凉 · 一站充电",
        "poster_title_en": "Cool Summer Charging Hub",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "autumn": {
        "label_zh": "秋季",
        "scene_en": (
            "warm autumn scene, golden-hour side light, blurred warm amber and maple "
            "tones in the background, cozy yet professional"
        ),
        "palette": ["#FAF5EC", "#B7791F", "#1F2933"],
        "accent_zh": "暖金",
        "poster_bg": ["#FFF8E1", "#FFECB3"],
        "poster_text": "#1F2933",
        "poster_accent": "#E65100",
        "poster_title_zh": "秋季收纳 · 充电有方",
        "poster_title_en": "Tidy Autumn Power",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "winter": {
        "label_zh": "冬季",
        "scene_en": (
            "clean winter scene, cool soft light, faint snow bokeh in the blurred "
            "background, calm and premium minimalism"
        ),
        "palette": ["#F4F6F8", "#5B7C99", "#1F2933"],
        "accent_zh": "雾蓝灰",
        "poster_bg": ["#F4F6F8", "#E3EAF1"],
        "poster_text": "#1F2933",
        "poster_accent": "#5B7C99",
        "poster_title_zh": "冬日暖心 · 随时满电",
        "poster_title_en": "Winter-Ready Power",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "christmas": {
        "label_zh": "圣诞节",
        "scene_en": (
            "festive Christmas scene, warm bokeh lights and subtle pine branches in "
            "the blurred background, deep green and warm gold accents, premium "
            "holiday atmosphere without clutter"
        ),
        "palette": ["#0F2E23", "#C9A227", "#F5F1E8"],
        "accent_zh": "圣诞绿+鎏金",
        "poster_bg": ["#0F4D2E", "#0A3D24"],
        "poster_text": "#FFFFFF",
        "poster_accent": "#C9A227",
        "poster_title_zh": "圣诞季 · 一站式充电",
        "poster_title_en": "Christmas Power Hub",
        "poster_sub_zh": "{ports}口USB-C{pt_zh} · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C {pt_en} · {power} per Port",
    },
    "easter": {
        "label_zh": "复活节",
        "scene_en": (
            "light Easter scene, soft pastel tones, delicate spring flowers blurred "
            "in the background, fresh and gentle morning light"
        ),
        "palette": ["#FBF7EF", "#E8A0BF", "#7FB069"],
        "accent_zh": "粉彩",
        "poster_bg": ["#FBF7EF", "#F3E9D8"],
        "poster_text": "#1F2933",
        "poster_accent": "#7FB069",
        "poster_title_zh": "复活节 · 春日新能量",
        "poster_title_en": "Easter Fresh Energy",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "halloween": {
        "label_zh": "万圣节",
        "scene_en": (
            "moody Halloween scene, dark background with warm orange accent lighting, "
            "subtle festive atmosphere, dramatic but still product-focused"
        ),
        "palette": ["#1A1210", "#E8641B", "#F5F1E8"],
        "accent_zh": "南瓜橙",
        "poster_bg": ["#2A1A4E", "#1A1030"],
        "poster_text": "#FFFFFF",
        "poster_accent": "#EB711F",
        "poster_title_zh": "万圣节 · 能量满格",
        "poster_title_en": "Halloween Full Power",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "black_friday": {
        "label_zh": "黑五",
        "scene_en": (
            "high-impact Black Friday sale scene, dark premium background with bold "
            "red and gold accent lighting, dynamic and promotional"
        ),
        "palette": ["#141414", "#E4393C", "#C9A227"],
        "accent_zh": "黑+红+金",
        "poster_bg": ["#0A0A0A", "#1C1C1C"],
        "poster_text": "#FFFFFF",
        "poster_accent": "#C9A227",
        "poster_title_zh": "黑五大促 · 充电装备",
        "poster_title_en": "Black Friday Power Deals",
        "poster_sub_zh": "{ports}口USB-C{pt_zh} · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C {pt_en} · {power} per Port",
    },
    "new_year": {
        "label_zh": "新年",
        "scene_en": (
            "New Year celebration scene, elegant midnight-blue background with soft "
            "golden fireworks bokeh, festive and premium"
        ),
        "palette": ["#101C33", "#C9A227", "#F5F1E8"],
        "accent_zh": "午夜蓝+金",
        "poster_bg": ["#0A1E3C", "#061224"],
        "poster_text": "#FFFFFF",
        "poster_accent": "#C9A227",
        "poster_title_zh": "新年新气象 · 满电出发",
        "poster_title_en": "New Year, Fully Charged",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
    "valentine": {
        "label_zh": "情人节",
        "scene_en": (
            "romantic Valentine's scene, soft rose tones and gentle bokeh hearts "
            "blurred in the background, warm and elegant"
        ),
        "palette": ["#FBF2F4", "#C94F6D", "#1F2933"],
        "accent_zh": "玫瑰粉",
        "poster_bg": ["#FCE4EC", "#F8BBD0"],
        "poster_text": "#1F2933",
        "poster_accent": "#D81B60",
        "poster_title_zh": "为爱充电",
        "poster_title_en": "Charge with Love",
        "poster_sub_zh": "{ports}口USB-C · 单口{power}",
        "poster_sub_en": "{ports}-Port USB-C · {power} per Port",
    },
}


def get_season(key):
    if key not in SEASONS:
        raise KeyError(f"unknown season/holiday: {key!r}. available: {', '.join(SEASONS)}")
    return SEASONS[key]


def list_seasons():
    return [(k, v["label_zh"]) for k, v in SEASONS.items()]
