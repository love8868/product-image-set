# -*- coding: utf-8 -*-
"""Gemini (Nano Banana) provider (stub, API 预留）。

Call structure: POST
  https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent?key=<KEY>
  JSON body: {"contents": [{"parts": [{"text": prompt}, {"inline_data": {...}}, ...]}],
              "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {...}}}
Model: gemini-2.5-flash-image series / Nano Banana 2.1 (see README; verify the exact
model id against current ai.google.dev docs when wiring the key).
Reference images are passed as inline_data parts; mask-based editing (2.1) passes the
mask as an additional image part with an instruction to edit only the masked region.

STUB STATUS: structure implemented, requires GEMINI_API_KEY. Verify the exact
endpoint/params against current docs when wiring the key (README -> 'API Key 对接方法').
"""

import base64
import json
import os
import urllib.error
import urllib.request

from .base import ImageProvider

# Nano Banana 2.1（GA 2026-10-06），model id 经官方文档核实：
# https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/nano-banana-2-1
# generateContent 对该模型保持可用。接 Key 前若文档有变，以 ai.google.dev 为准。
DEFAULT_MODEL = "gemini-nano-banana-2.1"

# 2.1 支持的宽高比（官方文档）；分辨率 1K/2K/4K
ASPECT_RATIOS = ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4",
                 "9:16", "16:9", "21:9", "1:4", "4:1", "1:8", "8:1", "9:21"]


class GeminiImageProvider(ImageProvider):
    name = "gemini"
    env_key_var = "GEMINI_API_KEY"

    def __init__(self, api_key=None, model=DEFAULT_MODEL):
        super().__init__(api_key=api_key)
        self.model = model or DEFAULT_MODEL

    def _part_for_file(self, path):
        with open(path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        return {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}

    def map_size(self, size):
        # 2.1 接受任意尺寸；宽高比映射到官方支持档，分辨率按长边分档
        return tuple(size)

    def _image_config(self, size):
        w, h = tuple(size)
        long_edge = max(w, h)
        image_size = "1K" if long_edge <= 1024 else ("2K" if long_edge <= 2048 else "4K")
        target = w / max(h, 1)

        def _val(r):
            a, b = r.split(":")
            return int(a) / int(b)

        best = min(ASPECT_RATIOS, key=lambda r: abs(_val(r) - target))
        if best != f"{w}:{h}":
            print(f"[gemini] aspect {(w, h)} mapped to {best}, imageSize {image_size}")
        return {"aspectRatio": best, "imageSize": image_size}

    def generate(self, prompt, ref_images=None, mask=None, size=(1024, 1024), **kwargs):
        parts = [{"text": prompt}]
        for i, path in enumerate(ref_images or []):
            parts.append({"text": f"[Reference image {i+1}: product photo, keep product identical]"})
            parts.append(self._part_for_file(path))
        if mask:
            parts.append({"text": "[Mask: edit ONLY the transparent/masked region, "
                                   "keep the unmasked product area pixel-identical]"})
            parts.append(self._part_for_file(mask))

        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": self._image_config(size),
            },
        }
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"[gemini] HTTP {e.code}: {body_text[:2000]}")
        # official response: candidates[0].content.parts[] with inlineData
        for part in payload["candidates"][0]["content"]["parts"]:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline:
                return base64.b64decode(inline["data"])
        raise RuntimeError("[gemini] no image data in API response")
