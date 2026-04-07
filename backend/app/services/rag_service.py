from __future__ import annotations

from app.schemas.common import EvidenceItem
from app.services.vector_service import VectorStoreService


class RagService:
    def __init__(self) -> None:
        self.vector_store = VectorStoreService()

    def retrieve(self, query: str, meeting_id: int, source_types: list[str], top_k: int = 5) -> list[EvidenceItem]:
        results: list[EvidenceItem] = []
        for source_type in source_types:
            rows = self.vector_store.query(query, n_results=top_k, where={'source_type': source_type})
            for row in rows:
                if source_type == 'current_transcript' and row['meeting_id'] != meeting_id:
                    continue
                if source_type in {'history_transcript', 'history_minutes'} and row['meeting_id'] == meeting_id:
                    continue
                results.append(EvidenceItem(**{k: row[k] for k in ('chunk_id', 'meeting_id', 'source_type', 'topic_hint', 'snippet', 'score')}))
        deduped: dict[str, EvidenceItem] = {}
        for item in results:
            deduped[item.chunk_id] = item
        return list(deduped.values())[:top_k]


