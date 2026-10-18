# -*- coding: utf-8 -*-
"""Muse 内置生图代跑 provider（不调网、不需要 API key）。

流程：generate() 不生成图片，而是把每个 job 写成 job 卡
jobs/<job_id>.json（含 prompt / negative / size / ref 图 / mask /
template_id+version / lane），orchestrator（Muse）按卡用内置生图能力
逐张执行；人工把图准备好后，用 --fill 回填进 draft/，再继续 layout。

Usage:
  python3 pipeline/generate.py --workdir products/<handle> --provider muse [--season X]
  # ... Muse 按 jobs/*.json 生图 ...
  python3 pipeline/generate.py --workdir products/<handle> --fill <job_id> <image_path>
  python3 pipeline/layout.py --workdir products/<handle>   # 继续
"""

import datetime
import json
import os
import shutil
import sys


class MuseProvider:
    """Job-card provider: generate() 只写卡，不调网；不需要 API key。"""

    name = "muse"

    def __init__(self, workdir=None, api_key=None, base_url=None, model=None):
        if not workdir:
            raise RuntimeError("[muse] 需要 workdir 才能写 job 卡（generate.py 会传入）")
        self.workdir = workdir
        self.jobs_dir = os.path.join(workdir, "jobs")

    def map_size(self, size):
        # 代跑不调 API：尺寸原样记录，回填时按此校验
        return tuple(size)

    def generate(self, prompt, ref_images=None, mask=None, size=(1024, 1024), **kwargs):
        """写 job 卡，返回 None（不调网）。"""
        job_id = kwargs.get("job_id") or "job"

        def _rel(p):
            if not p:
                return None
            return os.path.relpath(p, self.workdir) if os.path.isabs(p) else p

        card = {
            "job_id": job_id,
            "status": "pending",
            "prompt": prompt,
            "negative": kwargs.get("negative"),
            "size": [int(size[0]), int(size[1])],
            "ref_images": [_rel(p) for p in (ref_images or [])],
            "mask": _rel(mask),
            "template_id": kwargs.get("template_id"),
            "template_version": kwargs.get("template_version"),
            "lane": kwargs.get("lane"),
            "output": f"draft/{job_id}.png",
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        os.makedirs(self.jobs_dir, exist_ok=True)
        path = os.path.join(self.jobs_dir, f"{job_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        print(f"[muse] job 卡 -> {path}")
        return None


def fill_job(workdir, job_id, image_path):
    """回填：校验图片存在、jpg/png 格式、尺寸与 job 一致（±2px 容差）；
    通过则拷入 draft/<job 输出名>，并把 job 卡标为 filled。失败时报错说明原因。"""
    from PIL import Image

    card_path = os.path.join(workdir, "jobs", f"{job_id}.json")
    if not os.path.exists(card_path):
        sys.exit(f"[muse --fill] job 卡不存在: {card_path}")
    card = json.load(open(card_path, encoding="utf-8"))

    if not os.path.exists(image_path):
        sys.exit(f"[muse --fill] 图片不存在: {image_path}")
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        sys.exit(f"[muse --fill] 只接受 jpg/png，收到: {ext or '(无后缀)'}")

    try:
        with Image.open(image_path) as img:
            img.load()
            w, h = img.size
    except Exception as e:  # noqa: BLE001 - 损坏/非图片文件
        sys.exit(f"[muse --fill] 图片损坏或无法读取: {e}")
    ew, eh = card["size"]
    if abs(w - ew) > 2 or abs(h - eh) > 2:
        sys.exit(f"[muse --fill] 尺寸不符: 图片 {w}x{h}，job 要求 {ew}x{eh}（容差 ±2px）")

    dest = os.path.join(workdir, card["output"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(image_path, dest)

    card["status"] = "filled"
    card["filled_from"] = image_path
    card["filled_time"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
    print(f"[muse --fill] {job_id} -> {dest}（{w}x{h} 校验通过）")
