#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4 排版叠字：Pillow 确定性合成（底图 + 产品 + 文字 + 安全区）。

设计规范：design/layout-design-specs.md + design/brand-visual-guide.md
- 主题变量 THEMES（Manhattan 浅色 / Intellinet 深色参数预留）
- 字号体系按图高百分比（TYPE_SCALE），安全区 5%，文字压图罩规则，产品占比表
- 文字一律后期叠加，不让生图模型画字。

Usage:
  python3 pipeline/layout.py --workdir products/<handle>
      [--font-zh /path/to/CJK.ttf] [--font-en /path/to/Latin.ttf]
      [--season christmas] [--theme manhattan|intellinet]
缺 CJK 字体时警告（中文可能显示为方框），流程继续。
"""

import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

# ---- 主题变量（源自 design/brand-visual-guide.md §4，实测采样色值）----
THEMES = {
    "manhattan": {  # 浅色亲和：MVP 产品（Manhattan 充电柜）用此主题
        "background": "#FFFFFF",
        "bg_alt": "#F4F6F8",
        "text": "#1F2933",
        "text_secondary": "#5A646E",
        "primary": "#017AC3",      # 品牌蓝：徽章、图标底
        "headline": "#005485",     # 大标题深青蓝
        "accent": "#E8730C",       # 强调橙：仅点缀，≤10% 面积
        "deep": "#0A2A43",
        "banner_bg": ["#F4F6F8", "#E8EDF3"],
        "dark": False,
    },
    # Intellinet 深色主题：参数表预留；版式结构复用 manhattan（设计文档 §7 实现顺序）。
    # --theme intellinet 时颜色自动切换，布局细节以后续设计评审为准。
    "intellinet": {
        "background": "#022D5C",
        "bg_alt": "#0166AA",
        "text": "#FFFFFF",
        "text_secondary": "#8A93A4",
        "primary": "#0166AA",
        "headline": "#FFFFFF",
        "accent": "#EB711F",       # 橙：pill 徽章、分隔点、下划线
        "deep": "#022D5C",
        "banner_bg": ["#022D5C", "#01407E"],
        "dark": True,
    },
}

# ---- 实现参数表（design/layout-design-specs.md §7）----
SAFE = 0.05                      # 安全区（相对短边）
TYPE_SCALE = {"h1": 0.09, "h2": 0.045, "body": 0.032, "cap": 0.026}
LINE_H = 1.3
SCRIM = 0.5                      # 文字压图黑罩不透明度
LIGHT_SCRIM = 0.3                # 浅底场景白罩
PILL_R = 0.5                     # pill 圆角 = 高 × 0.5
PRODUCT_MAIN_MIN = 0.85          # 主图产品最小占比（合规红线）

TEMPLATES = {
    "amazon_main": (2000, 2000),    # Tier 0: 白底实拍直出
    "amazon_extra": (2000, 2000),   # 场景图 / 信息图 + 叠字
    "jd_main": (1200, 1200),        # 白底实拍 + 标题 + 徽章
    "jd_detail": (750, 1000),       # 750 宽详情图
    "web_banner": (2000, 440),      # 官网首页
    "mobile": (1000, 900),          # 手机端
    "season_poster": (1080, 1440),  # 3:4 季节海报
}

COMMON_FONTS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# Windows 上没有上面的 Linux 路径，也没有 fc-list；把系统自带中文字体排在最前面，
# 否则中文叠字全部渲染成方框（军师评审 H1）。
if os.name == "nt":
    COMMON_FONTS = [
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑 Bold
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
    ] + COMMON_FONTS


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def vgrad(size, top, bottom):
    """垂直渐变背景。"""
    w, h = size
    c0, c1 = hex2rgb(top), hex2rgb(bottom)
    img = Image.new("RGB", size, c0)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)))
    return img


def hgrad(size, left, right):
    """水平渐变背景。"""
    w, h = size
    c0, c1 = hex2rgb(left), hex2rgb(right)
    img = Image.new("RGB", size, c0)
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / max(w - 1, 1)
        d.line([(x, 0), (x, h)],
               fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)))
    return img


_CJK_NAME_HINTS = ("CJK", "Noto", "msyh", "simhei", "simsun", "pingfang",
                  "songti", "heit", "kaiti", "wqy", "sourcehan")


def _looks_cjk(path):
    pl = path.lower()
    return any(h.lower() in pl for h in _CJK_NAME_HINTS)


def find_font(explicit, want_cjk):
    if explicit and os.path.exists(explicit):
        return explicit, True
    for p in COMMON_FONTS:
        if os.path.exists(p):
            return p, _looks_cjk(p)
    try:
        out = subprocess.run(["fc-list", ":lang=zh", "file"], capture_output=True,
                             text=True, timeout=10).stdout
        for line in out.splitlines():
            path = line.split(":")[0].strip()
            if path and os.path.exists(path):
                return path, True
    except Exception:
        pass
    return None, False


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def fit_font(draw, text, font_path, start_size, max_width, min_size=12):
    """从 start_size 向下找能塞进 max_width 的字号（防溢出）。"""
    size = start_size
    while size > min_size:
        f = load_font(font_path, size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 2
    return load_font(font_path, min_size)


def dtext(draw, xy, s, font, fill, weight=400, anchor="la"):
    """按字重绘制文字（600+ 用 stroke 加粗模拟）。"""
    sw = max(0, (weight - 400) // 200)
    draw.text(xy, s, font=font, fill=fill, anchor=anchor,
              stroke_width=sw, stroke_fill=fill)


def draw_wrapped(draw, xy, text, font, fill, max_width, weight=400, line_h=LINE_H):
    """换行绘制；返回占用的总高度。"""
    x, y = xy
    has_cjk = any(ord(c) > 0x2E7F for c in text)
    tokens = list(text) if has_cjk else text.split(" ")
    sep = "" if has_cjk else " "
    lines, line = [], ""
    for tok in tokens:
        trial = line + sep + tok if line else tok
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            lines.append(line)
            line = tok
    if line:
        lines.append(line)
    step = int(font.size * line_h)
    for ln in lines:
        dtext(draw, (x, y), ln, font, fill, weight=weight)
        y += step
    return y - xy[1]


def text_size(draw, s, font):
    l, t, r, b = draw.textbbox((0, 0), s, font=font)
    return r - l, b - t


def pill(draw, box, fill, text, font, text_fill, weight=700):
    """pill 徽章：圆角矩形 + 居中文字。"""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=int((y1 - y0) * PILL_R), fill=fill)
    dtext(draw, ((x0 + x1) / 2, (y0 + y1) / 2), text, font, text_fill,
          weight=weight, anchor="mm")


def accent_underline(draw, x, y, width, color, thickness):
    """品牌橙短下划线（点缀，≤10% 面积原则）。"""
    draw.rectangle([x, y, x + width, y + thickness], fill=color)


def add_scrim(canvas, box, color=(10, 20, 30), alpha=0.5):
    """半透明罩：保证文字在底图上可读。"""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle(
        box, fill=color + (int(255 * alpha),))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def cover_image(img, size):
    """Center-crop cover (for banners)."""
    img = img.convert("RGB")
    r = max(size[0] / img.width, size[1] / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = (img.width - size[0]) // 2
    y = (img.height - size[1]) // 2
    return img.crop((x, y, x + size[0], y + size[1]))


# ---- 信息图用白色线性图标（画在品牌色圆底上）----

def _icon_bolt(d, cx, cy, r, w):
    s = r * 0.55
    pts = [(cx + s * 0.3, cy - s), (cx - s * 0.5, cy + s * 0.2),
           (cx - s * 0.05, cy + s * 0.2), (cx - s * 0.3, cy + s),
           (cx + s * 0.5, cy - s * 0.2), (cx + s * 0.05, cy - s * 0.2)]
    d.line(pts + [pts[0]], fill="white", width=w, joint="curve")


def _icon_ports(d, cx, cy, r, w):
    bw, bh = r * 0.32, r * 0.7
    for i in (-1, 0, 1):
        x = cx + i * r * 0.55
        d.rectangle([x - bw / 2, cy - bh / 2, x + bw / 2, cy + bh / 2],
                    outline="white", width=w)


def _icon_sync(d, cx, cy, r, w):
    d.arc([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5],
          start=30, end=300, fill="white", width=w)
    d.polygon([(cx + r * 0.55, cy - r * 0.25), (cx + r * 0.2, cy - r * 0.15),
               (cx + r * 0.42, cy + r * 0.12)], fill="white")


def _icon_device(d, cx, cy, r, w):
    d.rounded_rectangle([cx - r * 0.45, cy - r * 0.6, cx + r * 0.45, cy + r * 0.6],
                        radius=int(r * 0.15), outline="white", width=w)
    d.line([(cx - r * 0.45, cy + r * 0.3), (cx + r * 0.45, cy + r * 0.3)],
           fill="white", width=w)


ICONS = {"bolt": _icon_bolt, "ports": _icon_ports,
         "sync": _icon_sync, "device": _icon_device}


def main():
    ap = argparse.ArgumentParser(description="S4: Pillow layout + text overlay")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--font-zh", default=None)
    ap.add_argument("--font-en", default=None)
    ap.add_argument("--season", default=None,
                    help="季节/节日海报（不传则不生成 season_poster；B8 与 generate 对齐）")
    ap.add_argument("--theme", default="manhattan", choices=["manhattan", "intellinet"])
    args = ap.parse_args()

    theme = THEMES[args.theme]
    if args.theme == "intellinet":
        print("[layout] NOTE: intellinet 主题参数已接入，版式结构复用 manhattan"
              "（设计文档 §7 实现顺序），深色细节以后续设计评审为准。")
    T = {k: hex2rgb(v) if isinstance(v, str) and v.startswith("#") else v
         for k, v in theme.items() if k not in ("dark", "banner_bg")}
    dark = theme["dark"]

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir}")
    with open(pj, encoding="utf-8") as f:
        p = json.load(f)

    font_zh, cjk_ok = find_font(args.font_zh, True)
    font_en, _ = find_font(args.font_en, False)
    if not cjk_ok:
        print("[layout] WARNING: no CJK font found — "
              "Chinese text may render as boxes. Pass --font-zh explicitly.")
    else:
        print(f"[layout] CJK font: {font_zh}")
    fmain = font_en or font_zh

    def F(path, size):
        return load_font(path or fmain, size)

    def FS(size_pct, H):
        """字号体系：按图高百分比（TYPE_SCALE）。"""
        return max(12, int(H * size_pct))

    final_dir = os.path.join(args.workdir, "final")
    os.makedirs(final_dir, exist_ok=True)
    draft_dir = os.path.join(args.workdir, "draft")

    def draft(name):
        for cand in (f"{name}.png", f"{name}_placeholder.png"):
            pp = os.path.join(draft_dir, cand)
            if os.path.exists(pp):
                return pp
        return None

    hero_path = os.path.join(args.workdir, p.get("hero_image") or "")
    hero = Image.open(hero_path).convert("RGB") if os.path.exists(hero_path) else None
    facts = p.get("facts", {})
    pt_en = p.get("product_type_en", "Product")
    pt_zh = p.get("product_type_zh", "产品")

    def fval(k):
        f = facts.get(k)
        return f["value"] if f else "?"

    def freq(k, label):
        v = fval(k)
        if v in ("?", "", None):
            sys.exit(f"[layout] 缺少 {label}（product.json facts.{k}），先检查 analyze")
        return v

    ports, power = freq("ports_num", "端口数"), freq("power_w", "功率")
    size = fval("max_device_size")
    outputs = {}

    def save(img, name):
        path = os.path.join(final_dir, f"{name}.jpg")
        img.convert("RGB").save(path, "JPEG", quality=85)
        outputs[name] = path
        print(f"[layout] -> {path} {img.size}")
        return path

    def safe_margin(sz):
        return int(min(sz) * SAFE)

    # ============ amazon_main / jd_main：Tier 0 白底实拍直出 ============
    if hero is not None:
        # amazon 主图：零文字（平台硬性规则）
        W, H = TEMPLATES["amazon_main"]
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        prod = hero.copy()
        target = int(W * 0.88)  # ≥ PRODUCT_MAIN_MIN(0.85)，留余量
        r = min(target / prod.width, target / prod.height)
        prod = prod.resize((int(prod.width * r), int(prod.height * r)), Image.LANCZOS)
        canvas.paste(prod, ((W - prod.width) // 2, (H - prod.height) // 2))
        save(canvas, "amazon_main")

        # jd 主图：纯白底 + 产品 70% + 顶部短标题 + 底部 pill 徽章（≤3 文字元素）
        W, H = TEMPLATES["jd_main"]
        m = safe_margin((W, H))
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        title = f"{ports}口USB-C{pt_zh}"
        tf = fit_font(draw, title, fmain, FS(TYPE_SCALE["h2"], H), W - 2 * m)
        tw, th = text_size(draw, title, tf)
        dtext(draw, ((W - tw) / 2, m), title, tf, T["text"], weight=700)
        prod = hero.copy()
        target = int(W * 0.70)
        r = min(target / prod.width, target / prod.height)
        prod = prod.resize((int(prod.width * r), int(prod.height * r)), Image.LANCZOS)
        py = m + th + 24 + max(0, (H - (m + th + 24) - 200 - m - prod.height) // 2)
        canvas.paste(prod, ((W - prod.width) // 2, py))
        pill_h = int(H * 0.06)
        cap_f = F(fmain, FS(TYPE_SCALE["cap"], H))
        labels = [f"单口{power}快充", f"{ports}口同充"]
        widths = [draw.textlength(t, font=cap_f) + int(W * 0.06) for t in labels]
        gap = int(W * 0.03)
        x = (W - sum(widths) - gap) // 2
        y = H - m - pill_h
        for t, wpx in zip(labels, widths):
            if y < py + prod.height + int(H * 0.03):
                break  # 徽章不遮挡产品
            pill(draw, (x, y, x + wpx, y + pill_h), T["primary"], t, cap_f, (255, 255, 255))
            x += wpx + gap
        save(canvas, "jd_main")

    # ============ amazon_extra_1：场景图（设计文档 §1）============
    # 全幅场景底图；文字区左上（≤55%W，≤35%H）；H1 9%H + 橙下划线；H2 4.5%H
    # v0.3.0：按 plan.json 的 selected_scenes 顺序取第一个存在的 draft
    # （用户取消勾选 office/classroom、只选自定义场景时仍能出图）
    try:
        _plan = json.load(open(os.path.join(args.workdir, "plan.json"), encoding="utf-8"))
        _sel = _plan.get("selected_scenes") or ["scene_office", "scene_classroom"]
        _custom = [f"scene_custom_{i}" for i in range(len(_plan.get("custom_scenes", [])))]
    except Exception:
        _sel, _custom = ["scene_office", "scene_classroom"], []
    d = None
    for _cand in list(_sel) + _custom:
        d = draft(_cand)
        if d:
            break
    if d:
        W, H = TEMPLATES["amazon_extra"]
        canvas = cover_image(Image.open(d), (W, H))
        zx = (0, 0, int(W * 0.58), int(H * 0.38))
        canvas = add_scrim(canvas, zx, color=(255, 255, 255) if not dark else (10, 20, 30),
                           alpha=LIGHT_SCRIM if not dark else SCRIM)
        draw = ImageDraw.Draw(canvas)
        m = safe_margin((W, H))
        h1 = f"Charge {ports} Devices at Once."
        f1 = fit_font(draw, h1, fmain, FS(TYPE_SCALE["h1"], H), int(W * 0.52))
        dtext(draw, (m, m), h1, f1, T["headline"], weight=800)
        tw, _ = text_size(draw, h1, f1)
        accent_underline(draw, m, m + f1.size + 10, int(tw * 0.25),
                         T["accent"], max(6, int(H * 0.006)))
        h2 = f"{power} per port · USB-C PD"
        f2 = F(fmain, FS(TYPE_SCALE["h2"], H))
        draw_wrapped(draw, (m, m + f1.size + 40), h2, f2, T["text_secondary"],
                     int(W * 0.52), weight=600)
        save(canvas, "amazon_extra_1")
    else:
        print("[layout] skip amazon_extra_1: no scene draft")

    # ============ amazon_extra_2：信息图（设计文档 §2）============
    # 浅底；左 45% 产品白底直贴；右 55% 卖点列表（icon 圆 + 关键词 + 说明）；顶部小标题 + 分隔线
    W, H = TEMPLATES["amazon_extra"]
    m = safe_margin((W, H))
    if not dark:
        bg = vgrad((W, H), theme["bg_alt"], "#FFFFFF")
    else:
        bg = vgrad((W, H), theme["deep"], theme["primary"])
    draw = ImageDraw.Draw(bg)
    tf = F(fmain, FS(TYPE_SCALE["h2"], H))
    dtext(draw, (m, m), "Why you'll love it", tf, T["headline"], weight=700)
    _, th = text_size(draw, "Why you'll love it", tf)
    draw.line([(m, m + th + 18), (W - m, m + th + 18)],
              fill=T["text_secondary"], width=max(2, int(H * 0.005)))
    top = m + th + 40
    if hero is not None:
        lw = int(W * 0.45)
        pad = int(lw * 0.08)
        card = Image.new("RGB", (lw - 2 * m, H - top - m), (255, 255, 255))
        prod = hero.copy()
        prod.thumbnail((card.width - 2 * pad, card.height - 2 * pad), Image.LANCZOS)
        card.paste(prod, ((card.width - prod.width) // 2, (card.height - prod.height) // 2))
        bg.paste(card, (m, top))
    points = [
        ("ports", f"{ports}× USB-C Ports",
         f"Up to {power} per port — full speed for every device"),
        ("bolt", "No AC Adapters",
         "USB-C direct connection cuts cable clutter"),
        ("sync", "Smart Power Delivery",
         "Negotiates the optimal power for each device"),
        ("device", f"Fits up to {size}",
         "Phones, tablets and laptops — made for shared spaces"),
    ]
    rx = int(W * 0.47)
    rw = W - rx - m
    n = len(points)
    area_h = H - top - m
    slot = area_h / n
    for i, (icon, kw, desc) in enumerate(points):
        cy = top + slot * i + slot / 2
        cr = int(H * 0.03)
        dcol = T["primary"] if not dark else T["accent"]
        draw.ellipse([rx, cy - cr, rx + 2 * cr, cy + cr], fill=dcol)
        ICONS[icon](draw, rx + cr, cy, cr, w=max(4, int(cr * 0.18)))
        tx = rx + 2 * cr + int(W * 0.02)
        kf = F(fmain, FS(0.035, H))
        dtext(draw, (tx, cy - cr), kw, kf,
              T["primary"] if not dark else (255, 255, 255), weight=700)
        df = F(fmain, FS(TYPE_SCALE["body"], H))
        draw_wrapped(draw, (tx, cy - cr + kf.size + 10), desc, df,
                     T["text_secondary"], rw - (tx - rx), weight=500)
    save(bg, "amazon_extra_2")

    # ============ jd_detail：750 宽（主题色 + 字号体系）============
    if hero is not None:
        W, H = TEMPLATES["jd_detail"]
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        prod = hero.copy()
        prod.thumbnail((660, 500), Image.LANCZOS)
        canvas.paste(prod, ((W - prod.width) // 2, 24))
        y = 24 + prod.height + 36
        y += draw_wrapped(draw, (60, y), f"{ports} 口 USB-C {pt_zh}",
                          F(font_zh, FS(TYPE_SCALE["h2"], H)), T["text"], 630, weight=700)
        y += 28
        for line in (f"单口 {power}，多设备同时快充",
                     "USB-C 直连，无需 AC 适配器",
                     "PD 智能协商功率，高效可靠"):
            y += draw_wrapped(draw, (60, y), "· " + line,
                              F(font_zh, FS(TYPE_SCALE["body"], H)),
                              T["text_secondary"], 630, weight=500)
            y += 14
        save(canvas, "jd_detail")

    # ============ web_banner 2000×440（设计文档 §4：左文右图）============
    W, H = TEMPLATES["web_banner"]
    m = safe_margin((W, H))
    canvas = hgrad((W, H), theme["banner_bg"][0], theme["banner_bg"][1])
    draw = ImageDraw.Draw(canvas)
    card = [int(W * 0.50), m, W - m, H - m]
    draw.rounded_rectangle(card, radius=24, fill=(255, 255, 255))
    if hero is not None:
        prod = hero.copy()
        th = int((card[3] - card[1]) * 0.92)
        r = th / prod.height
        prod = prod.resize((int(prod.width * r), th), Image.LANCZOS)
        if prod.width > (card[2] - card[0]) * 0.94:
            r2 = (card[2] - card[0]) * 0.94 / prod.width
            prod = prod.resize((int(prod.width * r2), int(prod.height * r2)), Image.LANCZOS)
        canvas.paste(prod, ((card[0] + card[2] - prod.width) // 2,
                            (card[1] + card[3] - prod.height) // 2))
    tx = int(W * 0.10)
    twmax = int(W * 0.36)
    h1 = f"Charge {ports} Devices at Once."
    f1 = fit_font(draw, h1, fmain, int(H * 0.17), twmax)
    h2 = f"{power} per port · USB-C Power Delivery"
    f2 = F(fmain, int(H * 0.07))
    block = f1.size + 18 + int(H * 0.01) + 26 + f2.size
    y0 = (H - block) // 2
    dtext(draw, (tx, y0), h1, f1, T["headline"], weight=800)
    accent_underline(draw, tx, y0 + f1.size + 18, int(W * 0.18),
                     T["accent"], max(3, int(H * 0.01)))
    draw_wrapped(draw, (tx, y0 + f1.size + 18 + int(H * 0.01) + 26),
                 h2, f2, T["text_secondary"], twmax, weight=600)
    save(canvas, "web_banner")

    # ============ mobile 1000×900（设计文档 §5：上文下图）============
    if hero is not None:
        W, H = TEMPLATES["mobile"]
        m = safe_margin((W, H))
        canvas = Image.new("RGB", (W, H), hex2rgb(theme["bg_alt"]))
        draw = ImageDraw.Draw(canvas)
        f1 = fit_font(draw, f"{ports}口USB-C{pt_zh}", fmain, FS(0.10, H), W - 2 * m)
        w1, _ = text_size(draw, f"{ports}口USB-C{pt_zh}", f1)
        dtext(draw, ((W - w1) / 2, int(H * 0.06)), f"{ports}口USB-C{pt_zh}",
              f1, T["text"], weight=800)
        f2 = F(fmain, FS(0.05, H))
        sub = f"单口{power} · 一次充{ports}台"
        w2, _ = text_size(draw, sub, f2)
        dtext(draw, ((W - w2) / 2, int(H * 0.06) + f1.size + 18),
              sub, f2, T["text_secondary"], weight=600)
        pill_h = int(H * 0.07)
        cap_f = F(fmain, FS(TYPE_SCALE["cap"], H))
        plabel = "多设备同时快充"
        pw = int(draw.textlength(plabel, font=cap_f) + W * 0.08)
        pill_y = int(H * 0.06) + f1.size + 18 + f2.size + 24
        pill(draw, ((W - pw) / 2, pill_y, (W + pw) / 2, pill_y + pill_h),
             T["primary"], plabel, cap_f, (255, 255, 255))
        prod = hero.copy()
        target_h = int(H * 0.60)
        r = target_h / prod.height
        prod = prod.resize((int(prod.width * r), target_h), Image.LANCZOS)
        if prod.width > W - 2 * m:
            r2 = (W - 2 * m) / prod.width
            prod = prod.resize((int(prod.width * r2), int(prod.height * r2)), Image.LANCZOS)
        canvas.paste(prod, ((W - prod.width) // 2, H - m - prod.height))
        save(canvas, "mobile")

    # ============ season_poster 1080×1440（设计文档 §6：上中下三段）============
    # B8：--season 为空时整块跳过（与 generate 对齐）
    if args.season:
        from seasons import get_season
        W, H = TEMPLATES["season_poster"]
        m = safe_margin((W, H))
        s = get_season(args.season)
        title_h, prod_h = int(H * 0.28), int(H * 0.47)
        trans_h = int(H * 0.03)
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        tz = vgrad((W, title_h), s["poster_bg"][0], s["poster_bg"][1])
        canvas.paste(tz, (0, 0))
        draw = ImageDraw.Draw(canvas)
        tc = hex2rgb(s["poster_text"])
        t1 = s["poster_title_zh"].format(ports=ports, power=power, pt_zh=pt_zh, pt_en=pt_en)
        f1 = fit_font(draw, t1, fmain, FS(TYPE_SCALE["h1"], H), W - 2 * m)
        w1, _ = text_size(draw, t1, f1)
        dtext(draw, ((W - w1) / 2, int(title_h * 0.18)), t1, f1, tc, weight=800)
        t2 = s["poster_title_en"].format(ports=ports, power=power, pt_zh=pt_zh, pt_en=pt_en)
        f2 = F(fmain, FS(0.04, H))
        w2, _ = text_size(draw, t2, f2)
        dtext(draw, ((W - w2) / 2, int(title_h * 0.18) + f1.size + 20),
              t2, f2, tc, weight=600)
        tr = vgrad((W, trans_h), s["poster_bg"][1], theme["bg_alt"])
        canvas.paste(tr, (0, title_h))
        draw = ImageDraw.Draw(canvas)
        pz0 = title_h + trans_h
        draw.rectangle([0, pz0, W, pz0 + prod_h], fill=hex2rgb(theme["bg_alt"]))
        if hero is not None:
            prod = hero.copy()
            th = int(prod_h * 0.70)
            r = th / prod.height
            prod = prod.resize((int(prod.width * r), th), Image.LANCZOS)
            canvas.paste(prod, ((W - prod.width) // 2, pz0 + (prod_h - prod.height) // 2))
            draw = ImageDraw.Draw(canvas)
        az0 = pz0 + prod_h
        draw.rectangle([0, az0, W, H], fill=hex2rgb(s["poster_bg"][0]))
        pts = [f"{ports}口USB-C · 单口{power}",
               "无需AC适配器 · 桌面整洁",
               "教室 / 办公室 / 酒店多场景适用"]
        bf = F(fmain, FS(TYPE_SCALE["body"], H))
        y = az0 + 34
        for pt in pts:
            wpt, _ = text_size(draw, pt, bf)
            dtext(draw, ((W - wpt) / 2, y), pt, bf, tc, weight=500)
            y += int(bf.size * LINE_H) + 10
        pill_h = int(H * 0.045)
        cap_f = F(fmain, FS(TYPE_SCALE["cap"], H))
        plabel = f"{power} PD快充"
        pw = int(draw.textlength(plabel, font=cap_f) + 90)
        pill(draw, ((W - pw) / 2, y + 8, (W + pw) / 2, y + 8 + pill_h),
             hex2rgb(s["poster_accent"]), plabel, cap_f, (255, 255, 255))
        save(canvas, f"season_{args.season}")

    print(f"[layout] done: {len(outputs)} files in final/ "
          f"(theme={args.theme})")


if __name__ == "__main__":
    main()
