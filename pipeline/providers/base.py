# -*- coding: utf-8 -*-
"""Provider abstraction: generate(prompt, ref_images, mask, size) -> image bytes.

API 预留、后续对接：具体实现 stub 化。无 Key 时抛清晰错误，指引去 README 看对接方法。
"""

import base64
import io
import json
import os
import urllib.error
import urllib.request


class ImageProvider:
    """Abstract image-generation provider."""

    name = "base"
    env_key_var = None  # e.g. "OPENAI_API_KEY"

    def __init__(self, api_key=None):
        self.api_key = api_key or (os.environ.get(self.env_key_var) if self.env_key_var else None)
        if not self.api_key:
            raise RuntimeError(
                f"[{self.name}] missing API key. Set env var {self.env_key_var} "
                f"(see product-image-set/README.md -> 'API Key 对接方法'). "
                f"Or run generate.py with --dry-run to walk the full pipeline without a key."
            )

    def generate(self, prompt, ref_images=None, mask=None, size=(1024, 1024), **kwargs):
        """Return image bytes (PNG/JPEG). ref_images: list of image file paths.

        mask: path to a same-size PNG mask (transparent = editable area), or None.
        """
        raise NotImplementedError

    def map_size(self, size):
        """Map a requested (w, h) to the closest API-legal size.

        Default: passthrough. Override per provider; illegal sizes must be
        snapped or rejected here, never passed raw to the API.
        """
        return tuple(size)


def _encode_multipart(fields, files, boundary):
    """Minimal multipart/form-data encoder (stdlib only)."""
    buf = io.BytesIO()
    for k, v in fields.items():
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        buf.write(f"{v}\r\n".encode())
    for name, (filename, data, ctype) in files:
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        buf.write(f"Content-Type: {ctype}\r\n\r\n".encode())
        buf.write(data)
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue()


class OpenAICompatibleClient(ImageProvider):
    """OpenAI 兼容模式 HTTP 客户端（stdlib urllib，无第三方依赖）。

    - 无 ref/mask：POST {base_url}/images/generations（JSON: model/prompt/size/n）
    - 有 ref/mask：POST {base_url}/images/edits（multipart: image[] + mask + prompt + size + n）
    base_url 默认 https://api.openai.com/v1；可用 --base-url 参数或
    OPENAI_BASE_URL 环境变量覆盖（官方地址或任何 OpenAI-compatible 中转/代理）。
    返回解析兼容两种格式：data[0].b64_json / data[0].url。
    """

    name = "openai_compatible"
    env_key_var = "OPENAI_API_KEY"
    env_base_url_var = "OPENAI_BASE_URL"
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-image-1.5"

    def __init__(self, api_key=None, base_url=None, model=None):
        key = api_key or (os.environ.get(self.env_key_var) if self.env_key_var else None)
        if not key:
            raise RuntimeError(
                f"[{self.name}] missing API key. Set env var {self.env_key_var} "
                f"(see product-image-set/README.md -> 'API Key 对接方法'). "
                f"Or run generate.py with --dry-run to walk the full pipeline without a key."
            )
        self.api_key = key
        self.base_url = (base_url or os.environ.get(self.env_base_url_var)
                         or self.default_base_url).rstrip("/")
        self.model = model or self.default_model

    def extra_edits_fields(self):
        """子类可追加 edits 表单字段（如 OpenAI 官方的 input_fidelity）。"""
        return {}

    def _post_json(self, url, payload):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"[{self.name}] HTTP {e.code}: {body[:2000]}")

    def _post_multipart(self, url, fields, files):
        boundary = "----pimgset-boundary"
        body = _encode_multipart(fields, files, boundary)
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"[{self.name}] HTTP {e.code}: {body[:2000]}")

    @staticmethod
    def _extract_image(payload):
        data = (payload.get("data") or [{}])[0]
        if data.get("b64_json"):
            return base64.b64decode(data["b64_json"])
        if data.get("url"):
            with urllib.request.urlopen(data["url"], timeout=180) as resp:
                return resp.read()
        raise RuntimeError(f"[openai_compatible] no image data in API response "
                           f"(expected data[0].b64_json or data[0].url)")

    def generate(self, prompt, ref_images=None, mask=None, size=(1024, 1024), **kwargs):
        w, h = self.map_size(size)
        if ref_images or mask:
            return self._edits(prompt, ref_images or [], mask, (w, h))
        return self._generations(prompt, (w, h))

    def _generations(self, prompt, size):
        w, h = size
        payload = self._post_json(
            f"{self.base_url}/images/generations",
            {"model": self.model, "prompt": prompt, "size": f"{w}x{h}", "n": 1},
        )
        return self._extract_image(payload)

    def _edits(self, prompt, ref_images, mask, size):
        w, h = size
        fields = {"model": self.model, "prompt": prompt,
                  "size": f"{w}x{h}", "n": "1"}
        fields.update(self.extra_edits_fields())
        files = []
        for i, path in enumerate(ref_images):
            with open(path, "rb") as f:
                data = f.read()
            ext = os.path.splitext(path)[1].lower()
            ctype = "image/png" if ext == ".png" else "image/jpeg"
            files.append(("image", (f"ref{i}{ext}", data, ctype)))
        if mask:
            with open(mask, "rb") as f:
                files.append(("mask", ("mask.png", f.read(), "image/png")))
        payload = self._post_multipart(f"{self.base_url}/images/edits", fields, files)
        return self._extract_image(payload)


def get_provider(name, api_key=None, base_url=None, workdir=None):
    """Factory: 'openai' -> OpenAIImageProvider, 'gemini' -> GeminiImageProvider,
    'muse' -> MuseProvider（内置代跑 job 卡，不调网、不需要 key）。"""
    if name == "openai":
        from .openai import OpenAIImageProvider
        return OpenAIImageProvider(api_key=api_key, base_url=base_url)
    if name == "gemini":
        from .gemini import GeminiImageProvider
        return GeminiImageProvider(api_key=api_key)
    if name == "muse":
        from .muse import MuseProvider
        return MuseProvider(workdir=workdir)
    raise ValueError(f"unknown provider: {name!r} (expected 'openai', 'gemini' or 'muse')")
