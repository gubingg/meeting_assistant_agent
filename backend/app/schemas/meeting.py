from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.doc import UpdatedDocVersionItem


class MeetingListItemResponse(BaseModel):
    id: int
    title: str
    meeting_time: datetime | None
    summary_preview: str
    risk_count: int
    task_count: int
    decision_count: int


class MeetingTaskItemResponse(BaseModel):
    id: int | None = None
    title: str
    description: str | None = None
    owner: str | None = None
    due_date: datetime | None = None
    status: str


class MeetingDecisionItemResponse(BaseModel):
    text: str


class MeetingRiskItemResponse(BaseModel):
    text: str


class MeetingUploadResponse(BaseModel):
    meeting_id: int
    title: str
    meeting_time: datetime | None
    summary: str
    decisions: list[MeetingDecisionItemResponse]
    tasks: list[MeetingTaskItemResponse]
    risks: list[MeetingRiskItemResponse]
    updated_doc_versions: list[UpdatedDocVersionItem]


class MeetingDetailResponse(BaseModel):
    id: int
    project_id: int
    title: str
    meeting_time: datetime | None
    participants: list[str]
    summary: str
    decisions: list[MeetingDecisionItemResponse]
    tasks: list[MeetingTaskItemResponse]
    risks: list[MeetingRiskItemResponse]
    raw_json: dict | None
    raw_text: str | None
    source_file_name: str | None
