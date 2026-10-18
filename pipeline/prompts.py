# -*- coding: utf-8 -*-
"""Prompt template engine: pipeline/prompts/*.yaml -> prompt string.

Five-part assembly (order pinned in _base.yaml `assembly_order`):
  global_lock -> product_lock (1st) -> [Lane] marker -> scene+desc
  -> lock (2nd) -> no_text -> quality -> negative

Variables use string.Template ($var). A missing variable aborts with
template filename + variable name. Only product.json `official`-level
facts may feed $variables.

Layout:
  prompts/_base.yaml    全局：style_lock / no_drift / quality / negative /
                        no_text / desc_guard / 五段组装模板
  prompts/_locks.yaml   3C 锁定词（整表引用）
  prompts/slots/*.yaml  图位模板（scene_en / lane / provider / size /
                        layout_target / negative_add / trigger / order）
"""

import os
import re
import string
import sys

import yaml

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
SLOTS_DIR = os.path.join(PROMPTS_DIR, "slots")
STYLES_DIR = os.path.join(PROMPTS_DIR, "styles")

# $var / ${var} 引用扫描（预检缺失变量用；先去掉 $$ 转义）
_VAR_RE = re.compile(r"\$(?:{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))")


def _load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_base():
    return _load_yaml(os.path.join(PROMPTS_DIR, "_base.yaml"))


def load_locks():
    return _load_yaml(os.path.join(PROMPTS_DIR, "_locks.yaml"))


def load_slots():
    """Load slots/*.yaml sorted by `order`; each gains `_source_file`."""
    slots = []
    for fn in sorted(os.listdir(SLOTS_DIR)):
        if not fn.endswith((".yaml", ".yml")):
            continue
        s = _load_yaml(os.path.join(SLOTS_DIR, fn))
        s["_source_file"] = os.path.join("slots", fn)
        slots.append(s)
    slots.sort(key=lambda s: s.get("order", 999))
    return slots


def load_styles():
    """Load styles/*.yaml keyed by id; each gains `_source_file`."""
    styles = {}
    if not os.path.isdir(STYLES_DIR):
        return styles
    for fn in sorted(os.listdir(STYLES_DIR)):
        if not fn.endswith((".yaml", ".yml")):
            continue
        s = _load_yaml(os.path.join(STYLES_DIR, fn))
        s["_source_file"] = os.path.join("styles", fn)
        styles[s["id"]] = s
    return styles


def is_scene_slot(slot_id):
    """风格只注入场景类 slot（scene_* / season_poster / 场景池虚拟 slot），其余忽略 style。"""
    if slot_id.startswith("scene_") or slot_id == "season_poster":
        return True
    try:
        from recommend import SCENE_POOL
        return slot_id in SCENE_POOL
    except Exception:
        return False


def render(text, variables, source_file):
    """string.Template substitution ($var); missing var aborts with file + var name."""
    names = []
    for m in _VAR_RE.finditer(text.replace("$$", "")):
        names.append(m.group("braced") or m.group("plain"))
    missing = sorted({n for n in names if variables.get(n) is None})
    if missing:
        sys.exit(f"[prompts] 模板 {source_file} 缺少变量: "
                 + ", ".join(f"${n}" for n in missing)
                 + "；检查 build_variables / 调用方注入")
    try:
        return string.Template(text).substitute(variables)
    except ValueError as e:
        sys.exit(f"[prompts] 模板 {source_file} 变量语法错误: {e}")


def _official_value(facts, key):
    """official 层事实取值；缺失或非 official 返回 None（模板引用时 render 报错）。"""
    f = facts.get(key)
    if not f or f.get("level") != "official":
        return None
    v = f.get("value")
    return ", ".join(v) if isinstance(v, list) else v


def build_variables(product, season_scene=None, plan_slot=None):
    """Assemble $variables.

    - product.json official 层事实（缺失的 key 填 None，模板实际引用时 render 报错）
    - $season_scene: generate.py --season 注入
    - $scene_extra: plan.json 同 id slot 的 scene_extra（plan.py 拥有该字段；默认空串）
    """
    facts = product.get("facts", {})
    return {
        "pt": product.get("product_type_en", "product"),
        "pt_zh": product.get("product_type_zh", "产品"),
        "product_desc": product.get("product_desc_en", product.get("title", "product")),
        "brand": product.get("vendor", "Manhattan"),
        "ports": _official_value(facts, "ports_num"),
        "power": _official_value(facts, "power_w"),
        "season_scene": season_scene or "",
        "scene_extra": (plan_slot or {}).get("scene_extra", "") or "",
    }


def build_lock(identity, locks, keep_extra=None):
    """Six-step product lock block from _locks.yaml."""
    keep = list(locks["keep_base"])
    if keep_extra:
        keep.extend(keep_extra)
    return render(locks["lock_template"], {
        "keep_list": ", ".join(keep),
        "do_not_list": ", ".join(locks["do_not_base"]),
        "identity": identity,
    }, "_locks.yaml")


def style_lock_product(product_desc_en, lock_extra=None):
    """STYLE LOCK 产品规范块：保真 prompt 的落点（plan.py 兼容入口）。"""
    return "PRODUCT SPEC LOCK -- " + build_lock(
        f"same {product_desc_en}", load_locks(), keep_extra=lock_extra)


def assert_prompt_structure(prompt, slot, negative_full, base=None):
    """Step 2 回归断言（build_prompt 内每次调用；失败直接抛错）。"""
    base = base or load_base()
    sid = slot["id"]
    for marker in ("Keep EXACT same:", "DO NOT change:", "You may ONLY change:"):
        n = prompt.count(marker)
        assert n == 2, f"[prompts] {sid}: lock 标记 {marker!r} 出现 {n} 次（期望 2）"
    assert prompt.index(base["no_text"]) < prompt.index(base["quality"]), \
        f"[prompts] {sid}: no_text 必须出现在 quality 之前"
    assert prompt.rstrip().endswith("Negative prompt: " + negative_full), \
        f"[prompts] {sid}: negative 必须在末尾"
    assert f"[Lane {slot.get('lane', 'M')}]" in prompt, \
        f"[prompts] {sid}: [Lane] 标记丢失"


def build_prompt(slot, variables, lane=None, base=None, locks=None, style=None):
    """Five-part assembly. Returns the final prompt string.

    style: styles/*.yaml 的一条（或 {"style_en": ...} 片段）。仅场景类 slot
    （scene_*/season_poster）生效：替换 style_lock 的 palette/lighting/mood，
    并把 style_en 追加到 scene 段。无 style 时行为零变化。
    """
    base = base or load_base()
    locks = locks or load_locks()
    lane = lane or slot.get("lane", "M")

    sl = base["style_lock"]
    palette = ", ".join(sl["palette"])
    lighting = sl["lighting"]
    mood = sl["mood"]
    style_en_extra = ""
    if style and is_scene_slot(slot["id"]):
        palette = ", ".join(style.get("palette") or sl["palette"])
        lighting = style.get("lighting") or lighting
        mood = style.get("mood") or mood
        if style.get("style_en"):
            style_en_extra = " " + style["style_en"]

    global_lock = render(sl["template"], {
        "brand": variables["brand"],
        "palette": palette,
        "lighting": lighting,
        "mood": mood,
    }, "_base.yaml") + " " + base["no_drift"]

    desc = variables["product_desc"]
    product_lock = "PRODUCT SPEC LOCK -- " + build_lock(f"same {desc}", locks)
    scene = render(slot["scene_en"], variables, slot["_source_file"]) + style_en_extra
    guarded = render(base["desc_guard"], {"product_desc": desc}, "_base.yaml")
    lane_scene = f"[Lane {lane}] {scene} Featuring {guarded}."
    lock = build_lock("same device, same branding, same details", locks)
    negative = base["negative"]
    if slot.get("negative_add"):
        # 冲突规则 4：slot 可追加 negative，不许删 base 保命项
        negative += ", " + ", ".join(slot["negative_add"])

    parts = {
        "global_lock": global_lock,
        "product_lock": product_lock,
        "lane_scene": lane_scene,
        "lock": lock,
        "no_text": base["no_text"],
        "quality": base["quality"],
        "negative": negative,
    }
    out = base["assembly_template"]
    for key in base["assembly_order"]:
        out = out.replace("$" + key, parts[key])
    if "$" in out:  # 残留未替换的 $key
        i = out.index("$")
        sys.exit(f"[prompts] {slot['_source_file']}: assembly 后残留未替换变量 "
                 f"{out[i:i+24]!r}")
    assert_prompt_structure(out, slot, negative, base)
    return out
