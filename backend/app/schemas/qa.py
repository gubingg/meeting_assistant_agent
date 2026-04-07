from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    source_type: str
    label: str
    source_id: int | str
    doc_type: str | None = None
    doc_type_label: str | None = None


class ProjectQARequest(BaseModel):
    question: str = Field(min_length=1)


class ProjectQAResponse(BaseModel):
    answer: str
    citations: list[CitationItem]


class ProjectQAHistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    citations: list[CitationItem]
    created_at: datetime
