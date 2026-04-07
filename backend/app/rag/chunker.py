from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Iterable

from app.services.transcript_parser import UtterancePayload


@dataclass
class IndexedChunk:
    chunk_id: str
    text: str
    title: str
    chunk_index: int


class TextChunker:
    def chunk_meeting(self, title: str, utterances: list[UtterancePayload]) -> list[IndexedChunk]:
        chunks: list[IndexedChunk] = []
        buffer: list[str] = []
        chunk_index = 0
        for item in utterances:
            buffer.append(f'[{item.speaker}] {item.text}')
            if len('\n'.join(buffer)) >= 500:
                chunks.append(IndexedChunk(chunk_id=f'chunk_{uuid.uuid4().hex[:16]}', text='\n'.join(buffer), title=title, chunk_index=chunk_index))
                chunk_index += 1
                buffer = []
        if buffer:
            chunks.append(IndexedChunk(chunk_id=f'chunk_{uuid.uuid4().hex[:16]}', text='\n'.join(buffer), title=title, chunk_index=chunk_index))
        return chunks

    def chunk_document(self, title: str, paragraphs: Iterable[str]) -> list[IndexedChunk]:
        chunks: list[IndexedChunk] = []
        current = ''
        chunk_index = 0
        for paragraph in [item.strip() for item in paragraphs if item and item.strip()]:
            candidate = f'{current}\n{paragraph}'.strip()
            if len(candidate) > 700 and current:
                chunks.append(IndexedChunk(chunk_id=f'chunk_{uuid.uuid4().hex[:16]}', text=current, title=title, chunk_index=chunk_index))
                chunk_index += 1
                current = paragraph
            else:
                current = candidate
        if current:
            chunks.append(IndexedChunk(chunk_id=f'chunk_{uuid.uuid4().hex[:16]}', text=current, title=title, chunk_index=chunk_index))
        return chunks
