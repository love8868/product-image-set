# -*- coding: utf-8 -*-
"""OpenAI GPT-Image provider（OpenAICompatibleClient 的薄子类）。

行为与之前一致：走官方 {base_url}/images/edits（multipart），附带
input_fidelity=high；尺寸映射到官方三档 LEGAL_SIZES。
base_url 默认 https://api.openai.com/v1，可用 --base-url 参数或
OPENAI_BASE_URL 环境变量覆盖为 OpenAI-compatible 中转/代理地址。

Models: gpt-image-1.5 (current) / gpt-image-2. Note: gpt-image-1 deprecated 2026-10-23.
"""

from .base import OpenAICompatibleClient

DEFAULT_MODEL = "gpt-image-1.5"

# GPT-Image 1.5 /images/edits 仅接受这三档（+ auto）；其余尺寸调用前必须映射
LEGAL_SIZES = [(1024, 1024), (1536, 1024), (1024, 1536)]


class OpenAIImageProvider(OpenAICompatibleClient):
    name = "openai"
    env_key_var = "OPENAI_API_KEY"
    env_base_url_var = "OPENAI_BASE_URL"
    default_base_url = "https://api.openai.com/v1"
    default_model = DEFAULT_MODEL

    def map_size(self, size):
        """非法尺寸映射到最近合法档（按宽高比），避免 API 400。"""
        w, h = tuple(size)
        if (w, h) in LEGAL_SIZES:
            return (w, h)
        target = w / max(h, 1)
        best = min(LEGAL_SIZES, key=lambda s: abs(s[0] / s[1] - target))
        print(f"[openai] size {(w, h)} not API-legal, snapped to {best}")
        return best

    def extra_edits_fields(self):
        # 与旧版行为一致：官方 edits 附加字段
        return {"input_fidelity": "high", "response_format": "b64_json"}
