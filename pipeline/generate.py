#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S3 底图生成：组装 prompt -> 调 provider（或 --dry-run 跑完全流程）。

--dry-run（无 Key 也可跑）：prompt 原样写入 prompts/；Pillow 生成渐变背景 +
产品图（lazy 导入 rembg 抠图，可选；失败则回退为原图直贴）合成占位底图 -> draft/。
所有占位图文件名带 _placeholder 后缀，明确标识非 AI 成图。

Tier 1（Lane M，非 dry-run）：白底 + 产品抠图居中做 base，build_mask() 生成
产品保护蒙版（产品区不透明=保护，其余透明=可编辑），只重绘背景。
Lane P：prompt-lock 创意 lane，每场景最多重试 MAX_ATTEMPTS(3) 次，失败转人工。

Usage:
  python3 pipeline/generate.py --workdir products/<handle> --dry-run [--season christmas]
  python3 pipeline/generate.py --workdir products/<handle> [--provider openai] [--season winter]
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompts import load_slots, build_variables, build_prompt, load_base, load_locks  # noqa: E402
from seasons import get_season  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_ATTEMPTS = 3  # Lane P 每场景最多抽卡次数，超了转人工


def load_plan_slots(workdir):
    """plan.json 的 slots 按 key 建索引（供 $scene_extra；缺失则空）。"""
    pj = os.path.join(workdir, "plan.json")
    if not os.path.exists(pj):
        return {}
    try:
        plan = json.load(open(pj, encoding="utf-8"))
    except Exception:
        return {}
    return {s.get("key"): s for s in plan.get("slots", []) if s.get("key")}


def build_jobs(season=None):
    """从 slots/*.yaml 扫描任务：trigger=always 自动纳入；
    trigger=season 仅 --season 时纳入（job key = season_<key>）；manual 跳过。"""
    jobs = []
    for slot in load_slots():
        trig = slot.get("trigger", "always")
        if trig == "always":
            jobs.append({"key": slot["id"], "slot": slot,
                         "size": tuple(slot["size"]), "lane": slot.get("lane", "M"),
                         "provider": slot.get("provider", "openai")})
        elif trig == "season" and season:
            jobs.append({"key": f"season_{season}", "slot": slot,
                         "size": tuple(slot["size"]), "lane": slot.get("lane", "M"),
                         "provider": slot.get("provider", "openai")})
    return jobs


def cutout_product(image_path):
    """rembg lazy/可选抠图；失败回退原图。返回 RGBA Image 或 None。"""
    from PIL import Image
    try:
        from rembg import remove  # lazy import, optional dependency
        img = Image.open(image_path).convert("RGB")
        return remove(img)
    except Exception as e:  # noqa: BLE001 - ImportError / model download fail -> fallback
        print(f"[generate] rembg unavailable ({e}); fallback: paste raw image")
        try:
            return Image.open(image_path).convert("RGBA")
        except Exception:
            return None


def placeholder_background(size, seed=0):
    """Pillow 渐变背景占位（dry-run 用）。"""
    from PIL import Image, ImageDraw
    w, h = size
    base = [(244, 246, 248), (226, 232, 238), (214, 222, 230)]
    c0 = base[seed % len(base)]
    c1 = base[(seed + 1) % len(base)]
    img = Image.new("RGB", size, c0)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        draw.line([(0, y), (w, y)],
                  fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)))
    return img


def place_cutout(size, cutout, scale=0.55):
    """cutout(RGBA) 按比例居中摆到 size 画布上的几何；返回 ((x, y), resized)。"""
    from PIL import Image
    w, h = size
    cw = int(w * scale)
    ch = int(cutout.height * cw / max(cutout.width, 1))
    if ch > h:  # 极端竖长产品：改按高度适配
        ch = h
        cw = int(cutout.width * ch / max(cutout.height, 1))
    return ((w - cw) // 2, (h - ch) // 2), cutout.resize((cw, ch), Image.LANCZOS)


def build_mask(cutout, size):
    """Tier 1 蒙版：产品区不透明=保护区，其余透明=可编辑区（OpenAI mask 语义）。"""
    from PIL import Image
    mask = Image.new("RGBA", size, (0, 0, 0, 0))
    (x, y), prod = place_cutout(size, cutout)
    mask.paste(prod, (x, y), prod)  # cutout 自带 alpha：产品不透明，背景透明
    return mask


def build_lane_m_base(cutout, size):
    """Lane M base 图：白底 + 产品居中（与 mask 同几何），供 inpaint 重绘背景。"""
    from PIL import Image
    base = Image.new("RGB", size, (255, 255, 255))
    (x, y), prod = place_cutout(size, cutout)
    base.paste(prod.convert("RGB"), (x, y), prod)
    return base


def record_templates(workdir, records):
    """manifest.json `templates` 章节：合并写入（不覆盖 modules/files）。"""
    mp = os.path.join(workdir, "manifest.json")
    m = {}
    if os.path.exists(mp):
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            m = {}
    tpl = m.get("templates", {})
    tpl.update(records)
    m["templates"] = tpl
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def job_negative(slot, base):
    """与 prompts.build_prompt 一致的 negative 组装（供 muse job 卡记录）。"""
    neg = base.get("negative", "") if isinstance(base, dict) else ""
    if slot.get("negative_add"):
        neg += ", " + ", ".join(slot["negative_add"])
    return neg


def main():
    ap = argparse.ArgumentParser(description="S3: prompt assembly + generation")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--provider", default=None, choices=["openai", "gemini", "muse"],
                    help="override per-job provider for all jobs "
                         "(default: use each job's own provider)")
    ap.add_argument("--base-url", default=None,
                    help="OpenAI-compatible base URL 覆盖 "
                         "(default https://api.openai.com/v1；或设 OPENAI_BASE_URL)")
    ap.add_argument("--fill", nargs=2, metavar=("JOB_ID", "IMAGE_PATH"), default=None,
                    help="muse 代跑回填：校验图片后拷入 draft/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--season", default=None, help="e.g. christmas (adds a season job)")
    args = ap.parse_args()

    if args.fill:
        from providers.muse import fill_job
        job_id, image_path = args.fill
        fill_job(args.workdir, job_id, image_path)
        return

    pj = os.path.join(args.workdir, "product.json")
    if not os.path.exists(pj):
        sys.exit(f"product.json not found in {args.workdir}")
    with open(pj, encoding="utf-8") as f:
        p = json.load(f)

    prompts_dir = os.path.join(args.workdir, "prompts")
    draft_dir = os.path.join(args.workdir, "draft")
    os.makedirs(prompts_dir, exist_ok=True)
    os.makedirs(draft_dir, exist_ok=True)

    jobs = build_jobs(season=args.season)
    season_scene = get_season(args.season)["scene_en"] if args.season else None
    plan_slots = load_plan_slots(args.workdir)
    base, locks = load_base(), load_locks()

    from providers.base import get_provider
    provider_cache = {}

    def provider_for(job):
        name = args.provider or job.get("provider") or "openai"
        if name not in provider_cache:
            # 无 Key 时抛 RuntimeError（muse 代跑除外，不需要 key）
            provider_cache[name] = get_provider(name, base_url=args.base_url,
                                                workdir=args.workdir)
        return provider_cache[name]

    hero = os.path.join(args.workdir, p.get("hero_image") or "")
    cutout = cutout_product(hero) if args.dry_run and os.path.exists(hero) else None

    template_records = {}
    muse_jobs = 0
    for i, job in enumerate(jobs):
        slot = job["slot"]
        variables = build_variables(
            p,
            season_scene=season_scene if slot.get("trigger") == "season" else None,
            plan_slot=plan_slots.get(slot["id"]),
        )
        prompt = build_prompt(slot, variables, lane=job["lane"],
                              base=base, locks=locks)
        with open(os.path.join(prompts_dir, f"{job['key']}.txt"), "w", encoding="utf-8") as f:
            f.write(prompt)
        template_records[job["key"]] = {
            "template_id": slot["id"],
            "version": slot.get("version"),
            "source": slot["_source_file"],
            "variables": {k: v for k, v in variables.items() if v is not None},
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
        }

        if args.dry_run:
            # dry-run：无网络调用，重试计数 stub（此分支不触发重试逻辑）
            from PIL import Image
            bg = placeholder_background(job["size"], seed=i)
            if cutout is not None:
                (x, y), prod = place_cutout(job["size"], cutout)
                bg.paste(prod.convert("RGB"), (x, y), prod)
            out = os.path.join(draft_dir, f"{job['key']}_placeholder.png")
            bg.save(out)
            print(f"[generate] dry-run draft -> {out}")
            continue

        provider = provider_for(job)
        api_size = provider.map_size(job["size"])  # 非法尺寸在调用前映射/报错
        mask_path, ref_paths = None, [hero] if os.path.exists(hero) else None
        if job["lane"] == "M":
            if not os.path.exists(hero):
                raise RuntimeError(f"[generate] {job['key']}: hero image 缺失，转人工处理")
            cut = cutout_product(hero)
            if cut is None:
                raise RuntimeError("[generate] Lane M 需要 rembg 抠图："
                                   "pip install rembg 后重试（或先用 --dry-run）")
            base_path = os.path.join(draft_dir, f"{job['key']}_base.png")
            mask_path = os.path.join(draft_dir, f"{job['key']}_mask.png")
            build_lane_m_base(cut, api_size).save(base_path)
            build_mask(cut, api_size).save(mask_path)
            ref_paths = [base_path]
            print(f"[generate] Lane M base/mask -> {base_path}, {mask_path}")

        if provider.name == "muse":
            # 内置代跑：只写 job 卡，不调网；人工生图后 --fill 回填
            provider.generate(
                prompt, ref_images=ref_paths, mask=mask_path, size=api_size,
                job_id=job["key"], template_id=slot["id"],
                template_version=slot.get("version"), lane=job["lane"],
                negative=job_negative(slot, base),
            )
            muse_jobs += 1
            continue

        max_attempts = MAX_ATTEMPTS if job["lane"] == "P" else 1
        data, last_err = None, None
        for attempt in range(1, max_attempts + 1):
            try:
                data = provider.generate(prompt, ref_images=ref_paths,
                                         mask=mask_path, size=api_size)
                break
            except Exception as e:  # noqa: BLE001 - 报错后重试或转人工
                last_err = e
                if attempt < max_attempts:
                    print(f"[generate] {job['key']} retry {attempt}/{max_attempts}: {e}")
        if data is None:
            raise RuntimeError(f"[generate] {job['key']} 生图失败，转人工处理: {last_err}")
        out = os.path.join(draft_dir, f"{job['key']}.png")
        with open(out, "wb") as f:
            f.write(data)
        print(f"[generate] {provider.name} -> {out}")

    record_templates(args.workdir, template_records)
    if muse_jobs:
        print(f"[generate] muse 代跑：{muse_jobs} 个 job 卡已写入 jobs/；"
              f"人工按卡生图后用 --fill <job_id> <image> 回填，再跑 layout 继续")
    print(f"[generate] done: {len(jobs)} prompts written to prompts/; "
          f"templates recorded to manifest.json")


if __name__ == "__main__":
    main()
