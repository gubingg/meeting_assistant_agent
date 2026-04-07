from __future__ import annotations

from typing import Any

import chromadb

from app.core.config import get_settings
from app.services.chunk_service import ChunkPayload, ChunkService
from app.services.llm_service import OpenAICompatibleClient


class VectorStoreService:
    def __init__(self) -> None:
        settings = get_settings()
        self.chunk_service = ChunkService()
        self.llm_client = OpenAICompatibleClient()
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection)

    def _embed_text(self, text: str) -> list[float]:
        embedding = self.llm_client.embed_text(text)
        if embedding is not None:
            return embedding
        return self.chunk_service.embed_text(text)

    def upsert_chunks(self, chunks: list[ChunkPayload], meeting_id: int | None, source_doc_id: int | None) -> None:
        ids = [item.chunk_uuid for item in chunks]
        documents = [item.text for item in chunks]
        embeddings = [self._embed_text(item.text) for item in chunks]
        metadatas: list[dict[str, Any]] = []
        for item in chunks:
            metadatas.append(
                {
                    'chunk_id': item.chunk_uuid,
                    'meeting_id': meeting_id if meeting_id is not None else -1,
                    'source_type': item.source_type,
                    'source_doc_id': source_doc_id if source_doc_id is not None else -1,
                    'topic_hint': item.topic_hint,
                    'summary_short': item.summary_short,
                    'keywords': ','.join(item.keywords),
                }
            )
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def query(self, query_text: str, n_results: int = 5, where: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = self.collection.query(
            query_embeddings=[self._embed_text(query_text)],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances'],
        )
        rows: list[dict[str, Any]] = []
        for idx, doc in enumerate(result.get('documents', [[]])[0]):
            metadata = result.get('metadatas', [[]])[0][idx] or {}
            rows.append(
                {
                    'chunk_id': metadata.get('chunk_id'),
                    'meeting_id': None if metadata.get('meeting_id') == -1 else metadata.get('meeting_id'),
                    'source_type': metadata.get('source_type', ''),
                    'topic_hint': metadata.get('topic_hint'),
                    'snippet': doc[:240],
                    'score': None if not result.get('distances') else 1 - float(result['distances'][0][idx] or 0),
                    'text': doc,
                }
            )
        return rows
