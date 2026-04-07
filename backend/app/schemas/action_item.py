from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.meeting import ActionItemResponse


class ActionItemUpdateRequest(BaseModel):
    owner: str | None = None
    due_date: datetime | None = None
    priority: str | None = None
    status: str | None = None


class ActionItemUpdateResponse(ActionItemResponse):
    pass

