from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EvidenceItem(BaseModel):
    chunk_id: str
    meeting_id: int | None
    source_type: str
    topic_hint: str | None
    snippet: str
    score: float | None = None
    rerank_score: float | None = None
    source_id: int | None = None
    doc_id: int | None = None
    doc_version_id: int | None = None
    title: str | None = None
    doc_type: str | None = None
    doc_type_label: str | None = None


class SyncStatusItem(BaseModel):
    target_type: str
    target_url: str | None
    sync_status: str
    sync_message: str | None
    synced_at: datetime | None
