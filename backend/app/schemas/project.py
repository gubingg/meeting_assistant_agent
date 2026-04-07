from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2000)
    owner: str = Field(min_length=1, max_length=120)
    start_date: datetime | None = None


class ProjectCardResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    owner: str
    start_date: datetime | None
    status: str
    archived_at: datetime | None = None
    last_updated_at: datetime | None
    latest_meeting_time: datetime | None
    todo_count: int
    meeting_count: int
    unfinished_todo_count: int = 0


class ProjectDetailResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    owner: str
    start_date: datetime | None
    status: str
    archived_at: datetime | None = None
    meeting_count: int
    todo_count: int
    latest_updated_at: datetime | None


class ProjectStatusResponse(BaseModel):
    id: int
    status: str
    archived_at: datetime | None = None
