#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S5 校验：尺寸/比例/格式/文件大小/sRGB/主图纯白度 -> manifest.json + CHECKLIST.md。

Usage:
  python3 pipeline/validate.py --workdir products/<handle>
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import layout  # TEMPLATES 画布尺寸：尺寸交叉检查的真源
from prompts import load_slots

# 期望规格：name -> (width, height, max_bytes|None)
SPECS = {
    "amazon_main": ((2000, 2000), 10 * 1024 * 1024),
    "amazon_extra_1": ((2000, 2000), 10 * 1024 * 1024),
    "amazon_extra_2": ((2000, 2000), 10 * 1024 * 1024),
    "jd_main": ((1200, 1200), 1 * 1024 * 1024),
    "jd_detail": ((750, 1000), 3 * 1024 * 1024),
    "web_banner": ((2000, 440), 10 * 1024 * 1024),
    "mobile": ((1000, 900), 10 * 1024 * 1024),
}
# 7 个固定期望文件（缺失即 FAIL）；季节海报按 --season 点名
EXPECTED_FIXED = ["amazon_main", "amazon_extra_1", "amazon_extra_2", "jd_main",
                  "jd_detail", "web_banner", "mobile"]
SEASON_SIZE, SEASON_MAX = (1080, 1440), 10 * 1024 * 1024


def check_white_corners(img, thresh=252, sample=40):
    """主图纯白度：四角采样，RGB 均值 >= thresh 判 pass（JPEG 压缩留余量）。"""
    w, h = img.size
    px = img.load()
    vals = []
    for (x0, y0) in ((0, 0), (w - sample, 0), (0, h - sample), (w - sample, h - sample)):
        for dx in range(sample):
            for dy in range(sample):
                r, g, b = px[x0 + dx, y0 + dy][:3]
                vals.append((r + g + b) / 3)
    mean = sum(vals) / len(vals)
    return mean >= thresh, round(mean, 1)


def check_slot_sizes():
    """尺寸交叉检查：slot 的 size（生成尺寸）vs layout TEMPLATES（排版画布）。

    以 layout.py 为真源；两者宽高比必须一致（相对偏差 ≤15%），绝对尺寸允许
    upscale（如 1024 生成 -> 2000 画布）。不一致直接报错。
    """
    for s in load_slots():
        lt = s.get("layout_target")
        if not lt:
            sys.exit(f"[validate] slot {s['id']} 缺少 layout_target 字段")
        if lt not in layout.TEMPLATES:
            sys.exit(f"[validate] slot {s['id']} 的 layout_target={lt!r} "
                     f"在 layout.TEMPLATES 中不存在")
        sw, sh = s["size"]
        cw, ch = layout.TEMPLATES[lt]
        rel = abs(sw / sh - cw / ch) / (cw / ch)
        if rel > 0.15:
            sys.exit(f"[validate] 尺寸打架: slot {s['id']} size={tuple(s['size'])} "
                     f"vs layout.{lt}={(cw, ch)}（宽高比偏差 {rel:.0%} > 15%）")
    print("[validate] slot 尺寸交叉检查通过（宽高比一致）")


def check_template_drift(manifest):
    """模板版本 drift：只警告不失败。"""
    records = manifest.get("templates", {})
    if not records:
        return
    current = {s["id"]: s.get("version") for s in load_slots()}
    for job_key, rec in records.items():
        tid = rec.get("template_id")
        if tid in current and rec.get("version") != current[tid]:
            print(f"[validate] WARNING: 模板 {tid} 已更新为 v{current[tid]}，"
                  f"但 {job_key} 是用 v{rec.get('version')} 生成的（drift，仅警告）")


def main():
    ap = argparse.ArgumentParser(description="S5: validate final images")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--season", default=None,
                    help="also expect season_<key>.jpg (e.g. christmas)")
    args = ap.parse_args()

    final_dir = os.path.join(args.workdir, "final")
    if not os.path.isdir(final_dir):
        sys.exit(f"final/ not found in {args.workdir} (run layout.py first)")

    check_slot_sizes()

    manifest = {"files": [], "all_pass": True}

    def check_one(name, path):
        """校验单个文件；返回 entry。"""
        if name.startswith("season_"):
            spec_size, spec_max = SEASON_SIZE, SEASON_MAX
        else:
            spec = SPECS.get(name)
            if not spec:
                return None
            spec_size, spec_max = spec
        img = Image.open(path)
        entry = {"file": os.path.basename(path), "checks": {}}
        c = entry["checks"]
        c["dimensions"] = {"expected": spec_size, "actual": img.size,
                           "pass": img.size == spec_size}
        c["format"] = {"expected": "JPEG", "actual": img.format,
                       "pass": img.format == "JPEG"}
        size_b = os.path.getsize(path)
        c["file_size"] = {"max_bytes": spec_max, "actual_bytes": size_b,
                          "pass": size_b <= spec_max}
        c["mode_rgb"] = {"actual": img.mode, "pass": img.mode == "RGB"}
        if name in ("amazon_main", "jd_main"):
            ok, mean = check_white_corners(img.convert("RGB"))
            c["pure_white_bg"] = {"corner_mean": mean, "threshold": 252, "pass": ok}
        entry["pass"] = all(v["pass"] for v in c.values())
        return entry

    found = {}
    for fname in sorted(os.listdir(final_dir)):
        if not fname.lower().endswith(".jpg"):
            continue
        entry = check_one(fname[:-4], os.path.join(final_dir, fname))
        if entry:
            found[fname[:-4]] = entry

    expected = list(EXPECTED_FIXED)
    if args.season:
        expected.append(f"season_{args.season}")

    for name in expected:
        if name in found:
            entry = found[name]
        else:
            entry = {"file": f"{name}.jpg",
                     "checks": {"exists": {"pass": False, "note": "file missing"}},
                     "pass": False}
        if not entry["pass"]:
            manifest["all_pass"] = False
        manifest["files"].append(entry)
        status = "PASS" if entry["pass"] else "FAIL"
        detail = ""
        if entry["pass"]:
            img_size = entry["checks"]["dimensions"]["actual"]
            img_kb = entry["checks"]["file_size"]["actual_bytes"] // 1024
            detail = f" {img_size} {img_kb}KB"
        print(f"[validate] {status} {entry['file']}{detail}")

    # manifest.json 合并写入：保留 run.py 的 modules 章节与 generate.py 的
    # templates 章节，只更新 files / all_pass（旧版直接覆盖会清空它们）
    mp = os.path.join(args.workdir, "manifest.json")
    merged = {}
    if os.path.exists(mp):
        try:
            merged = json.load(open(mp, encoding="utf-8"))
        except Exception:
            merged = {}
    merged["files"] = manifest["files"]
    merged["all_pass"] = manifest["all_pass"]
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    check_template_drift(merged)

    # S6 人工验收门：打勾清单
    cl = [
        "# 人工验收清单（S6）\n",
        "> Tier 2（prompt-lock 生图）必过；Tier 1 抽查；Tier 0（实拍直出）可跳过。\n",
        "## 产品保真",
        "- [ ] 轮廓/外形与官网原图一致，无变形",
        "- [ ] 比例正确（多产品同框时各产品相对比例符合真实尺寸）",
        "- [ ] 颜色/表面材质与原图一致",
        "- [ ] Logo 与机身印刷文字逐字正确、清晰可读",
        "- [ ] 接口数量/位置正确（如 10 个 USB-C 口，一个不多一个不少）",
        '- [ ] 阴影/反光自然，无"贴纸感"',
        "## 文案与排版",
        "- [ ] 无错别字，中英术语一致",
        "- [ ] 数字/规格与官网一致（功率/端口数/尺寸）",
        "- [ ] 文字无溢出、无遮挡产品主体",
        "- [ ] 各图风格统一（配色/光影/字体）",
        "## 合规",
        "- [ ] Amazon 主图：纯白底、无文字、无水印",
        "- [ ] 无虚假宣传表述（功效/认证需有依据）",
        "- [ ] 字体有商用授权",
        "",
        "验收人：________  日期：________",
    ]
    with open(os.path.join(args.workdir, "CHECKLIST.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(cl) + "\n")
    print(f"[validate] all_pass={manifest['all_pass']} -> manifest.json, CHECKLIST.md")


if __name__ == "__main__":
    main()
