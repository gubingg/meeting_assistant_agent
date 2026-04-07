from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import EvidenceItem


class ChatRequest(BaseModel):
    meeting_id: int
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    intent: str
    used_skills: list[str]
    answer: str
    summary_updated: bool = False
    action_items_updated: bool = False
    decisions_updated: bool = False
    evidence: list[EvidenceItem] = Field(default_factory=list)

