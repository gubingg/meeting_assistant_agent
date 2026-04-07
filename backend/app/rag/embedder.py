from __future__ import annotations

import math
import re
from collections import Counter

from app.services.llm_service import OpenAICompatibleClient

TOKEN_RE = re.compile(r'[\u4e00-\u9fffA-Za-z0-9_]{2,}')


class Embedder:
    def __init__(self) -> None:
        self.client = OpenAICompatibleClient()

    def embed(self, text: str, dims: int = 128) -> list[float]:
        remote = self.client.embed_text(text, dimensions=dims)
        if remote is not None:
            return remote
        counts = Counter(TOKEN_RE.findall(text) or [text[:32]])
        vector = [0.0] * dims
        for token, weight in counts.items():
            vector[abs(hash(token)) % dims] += float(weight)
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]
