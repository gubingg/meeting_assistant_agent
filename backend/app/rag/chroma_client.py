from __future__ import annotations

from typing import Any

import chromadb

from app.core.config import get_settings
from app.rag.embedder import Embedder


class ChromaIndexClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection)
        self.embedder = Embedder()

    def upsert(self, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        self.collection.upsert(
            ids=[item['id'] for item in items],
            documents=[item['text'] for item in items],
            embeddings=[self.embedder.embed(item['text']) for item in items],
            metadatas=[item['metadata'] for item in items],
        )

    def query(self, query: str, project_id: int, n_results: int = 6) -> list[dict[str, Any]]:
        result = self.collection.query(
            query_embeddings=[self.embedder.embed(query)],
            n_results=n_results,
            where={'project_id': project_id},
            include=['documents', 'metadatas', 'distances'],
        )
        rows: list[dict[str, Any]] = []
        documents = result.get('documents', [[]])[0]
        metadatas = result.get('metadatas', [[]])[0]
        distances = result.get('distances', [[]])[0]
        for idx, text in enumerate(documents):
            metadata = metadatas[idx] or {}
            rows.append(
                {
                    'chunk_id': metadata.get('chunk_id'),
                    'source_type': metadata.get('source_type'),
                    'source_id': metadata.get('source_id'),
                    'meeting_id': metadata.get('meeting_id'),
                    'doc_id': metadata.get('doc_id'),
                    'doc_version_id': metadata.get('doc_version_id'),
                    'title': metadata.get('title'),
                    'doc_type': metadata.get('doc_type'),
                    'doc_type_label': metadata.get('doc_type_label'),
                    'snippet': text[:240],
                    'score': 1 - float(distances[idx] or 0),
                    'text': text,
                }
            )
        return rows
