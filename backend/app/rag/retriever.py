from __future__ import annotations

from app.constants.doc_types import get_doc_type_label
from app.rag.chroma_client import ChromaIndexClient
from app.schemas.common import EvidenceItem
from app.services.llm_service import OpenAICompatibleClient


class ProjectRetriever:
    def __init__(self, client: ChromaIndexClient | None = None, llm_client: OpenAICompatibleClient | None = None) -> None:
        self.client = client or ChromaIndexClient()
        self.llm_client = llm_client or OpenAICompatibleClient()

    def retrieve(self, project_id: int, query: str, source_types: set[str] | None = None, top_k: int = 6, preferred_doc_types: list[str] | None = None) -> list[EvidenceItem]:
        rows = self.client.query(query=query, project_id=project_id, n_results=max(top_k * 2, 8))
        preferred_doc_types = preferred_doc_types or []

        filtered_rows = [row for row in rows if not source_types or row['source_type'] in source_types]
        fallback_sorted = sorted(filtered_rows, key=lambda row: self._fallback_sort_key(row, preferred_doc_types))
        rerank_scores = self._rerank_rows(query, fallback_sorted, top_k)

        if rerank_scores:
            ranked_rows = sorted(
                fallback_sorted,
                key=lambda row: self._rerank_sort_key(row, preferred_doc_types, rerank_scores),
            )
        else:
            ranked_rows = fallback_sorted

        items: list[EvidenceItem] = []
        for row in ranked_rows[:top_k]:
            items.append(
                EvidenceItem(
                    chunk_id=row['chunk_id'],
                    meeting_id=row['meeting_id'],
                    source_type=row['source_type'],
                    topic_hint=row['title'],
                    snippet=row['snippet'],
                    score=row['score'],
                    rerank_score=rerank_scores.get(row['chunk_id']) if rerank_scores else None,
                    source_id=row['source_id'],
                    doc_id=row['doc_id'],
                    doc_version_id=row['doc_version_id'],
                    title=row['title'],
                    doc_type=row.get('doc_type'),
                    doc_type_label=row.get('doc_type_label') or get_doc_type_label(row.get('doc_type')),
                )
            )
        return items

    @staticmethod
    def _preferred_rank(row: dict, preferred_doc_types: list[str]) -> int:
        if row.get('source_type') == 'project_doc_version' and row.get('doc_type') in preferred_doc_types:
            return 0
        return 1

    def _fallback_sort_key(self, row: dict, preferred_doc_types: list[str]) -> tuple[int, float]:
        return (self._preferred_rank(row, preferred_doc_types), -(row.get('score') or 0.0))

    def _rerank_rows(self, query: str, rows: list[dict], top_k: int) -> dict[str, float]:
        documents = [row.get('text') or row.get('snippet') or '' for row in rows]
        rerank_results = self.llm_client.rerank(query, documents, top_n=top_k)
        if not rerank_results:
            return {}

        scores: dict[str, float] = {}
        for item in rerank_results:
            index = item.get('index')
            if index is None or not isinstance(index, int) or index < 0 or index >= len(rows):
                continue
            scores[rows[index]['chunk_id']] = float(item.get('score') or 0.0)
        return scores

    def _rerank_sort_key(self, row: dict, preferred_doc_types: list[str], rerank_scores: dict[str, float]) -> tuple[int, float, int, float]:
        rerank_score = rerank_scores.get(row['chunk_id'])
        if rerank_score is None:
            return (1, 0.0, self._preferred_rank(row, preferred_doc_types), -(row.get('score') or 0.0))
        return (0, -rerank_score, self._preferred_rank(row, preferred_doc_types), -(row.get('score') or 0.0))
