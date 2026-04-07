from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from app.services.transcript_parser import UtterancePayload

STOPWORDS = {
    '我们', '你们', '这个', '那个', '以及', '需要', '进行', '今天', '会议', '一下', '已经', '如果', '因为', '所以',
    '然后', '可以', '目前', '一个', '没有', '这次', '后续', '相关', '项目', '确认', '讨论', '安排'
}
TOKEN_RE = re.compile(r'[\u4e00-\u9fffA-Za-z0-9_]{2,}')


@dataclass
class ChunkPayload:
    chunk_uuid: str
    text: str
    source_type: str
    turn_start: int | None
    turn_end: int | None
    start_time_sec: int | None
    end_time_sec: int | None
    speaker_list: list[str]
    topic_hint: str
    summary_short: str
    keywords: list[str]


class ChunkService:
    def extract_keywords(self, text: str, limit: int = 8) -> list[str]:
        tokens = [token for token in TOKEN_RE.findall(text) if token not in STOPWORDS]
        counts = Counter(tokens)
        return [item for item, _ in counts.most_common(limit)]

    def build_topic_hint(self, text: str) -> str:
        snippet = re.split(r'[。！？\n]', text.strip())[0][:28].strip()
        return snippet or '会议讨论片段'

    def build_summary_short(self, text: str) -> str:
        compact = re.sub(r'\s+', ' ', text.strip())
        return compact[:80]

    def build_from_utterances(self, utterances: list[UtterancePayload], source_type: str) -> list[ChunkPayload]:
        chunks: list[ChunkPayload] = []
        if not utterances:
            return chunks

        index = 0
        while index < len(utterances):
            end = min(index + 4, len(utterances))
            selected = utterances[index:end]
            text = '\n'.join(f'[{item.speaker}] {item.text}' for item in selected)
            while len(text) < 300 and end < len(utterances) and len(selected) < 6:
                selected.append(utterances[end])
                end += 1
                text = '\n'.join(f'[{item.speaker}] {item.text}' for item in selected)
            chunks.append(
                ChunkPayload(
                    chunk_uuid=f'c_{uuid.uuid4().hex[:16]}',
                    text=text,
                    source_type=source_type,
                    turn_start=selected[0].turn_index,
                    turn_end=selected[-1].turn_index,
                    start_time_sec=selected[0].start_time_sec,
                    end_time_sec=selected[-1].end_time_sec,
                    speaker_list=list(dict.fromkeys(item.speaker for item in selected)),
                    topic_hint=self.build_topic_hint(text),
                    summary_short=self.build_summary_short(text),
                    keywords=self.extract_keywords(text),
                )
            )
            if end >= len(utterances):
                break
            index = max(end - 1, index + 1)
        return chunks

    def build_from_paragraphs(self, paragraphs: Iterable[str], source_type: str) -> list[ChunkPayload]:
        chunks: list[ChunkPayload] = []
        buffer: list[str] = []
        current_size = 0
        items = [item.strip() for item in paragraphs if item.strip()]
        for item in items:
            buffer.append(item)
            current_size += len(item)
            if current_size >= 500:
                text = '\n'.join(buffer)
                chunks.append(
                    ChunkPayload(
                        chunk_uuid=f'c_{uuid.uuid4().hex[:16]}',
                        text=text,
                        source_type=source_type,
                        turn_start=None,
                        turn_end=None,
                        start_time_sec=None,
                        end_time_sec=None,
                        speaker_list=[],
                        topic_hint=self.build_topic_hint(text),
                        summary_short=self.build_summary_short(text),
                        keywords=self.extract_keywords(text),
                    )
                )
                buffer = buffer[-1:]
                current_size = sum(len(part) for part in buffer)
        if buffer:
            text = '\n'.join(buffer)
            chunks.append(
                ChunkPayload(
                    chunk_uuid=f'c_{uuid.uuid4().hex[:16]}',
                    text=text,
                    source_type=source_type,
                    turn_start=None,
                    turn_end=None,
                    start_time_sec=None,
                    end_time_sec=None,
                    speaker_list=[],
                    topic_hint=self.build_topic_hint(text),
                    summary_short=self.build_summary_short(text),
                    keywords=self.extract_keywords(text),
                )
            )
        return chunks

    def embed_text(self, text: str, dims: int = 128) -> list[float]:
        vector = [0.0] * dims
        for token in self.extract_keywords(text, limit=32) or [text[:32]]:
            idx = abs(hash(token)) % dims
            vector[idx] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

