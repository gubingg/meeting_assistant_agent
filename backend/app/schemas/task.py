from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TaskItemResponse(BaseModel):
    id: int
    title: str
    owner: str | None
    due_date: datetime | None
    status: str
    status_label: str
    source_meeting_title: str | None
    latest_update_meeting_title: str | None


class TaskSummaryResponse(BaseModel):
    total: int
    done_count: int
    unfinished_count: int
    delayed_count: int
    blocked_count: int
