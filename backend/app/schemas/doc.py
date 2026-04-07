from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UpdatedDocVersionItem(BaseModel):
    doc_id: int
    doc_name: str
    doc_type: str
    doc_type_label: str
    version_id: int
    version_label: str
    change_summary: str | None = None


class ProjectDocItemResponse(BaseModel):
    id: int
    title: str
    doc_name: str
    doc_type: str
    doc_type_label: str
    parse_status: str
    parse_status_label: str
    qa_enabled: bool
    has_task_link_suggestion: bool
    task_link_suggestion_count: int
    current_version_label: str | None
    updated_at: datetime | None


class ProjectDocUploadResponse(BaseModel):
    doc_id: int
    title: str
    doc_name: str
    doc_type: str
    doc_type_label: str
    parse_status: str
    parse_status_label: str
    qa_enabled: bool
    has_task_link_suggestion: bool
    task_link_suggestion_count: int
    current_version_label: str
    indexed_chunks: int


class ProjectDocVersionItemResponse(BaseModel):
    id: int
    version_label: str
    change_summary: str | None
    source_meeting_id: int | None
    status: str
    created_at: datetime


class ProjectDocVersionDetailResponse(BaseModel):
    id: int
    project_doc_id: int
    version_label: str
    content_raw: str
    change_summary: str | None
    source_meeting_id: int | None
    status: str
    created_at: datetime


class TaskLinkSuggestionItemResponse(BaseModel):
    suggestion_id: int
    task_id: int
    task_title: str
    owner: str | None
    current_status: str
    current_status_label: str
    source_meeting: str | None
    suggested_status: str
    suggested_status_label: str
    match_reason: str | None
    match_score: float


class ConfirmTaskLinkSuggestionRequest(BaseModel):
    update_task_status: str = Field(min_length=1)


class TaskLinkSuggestionActionResponse(BaseModel):
    suggestion_id: int
    suggestion_status: str
    suggestion_status_label: str
    task_id: int
    task_status: str
    task_status_label: str
