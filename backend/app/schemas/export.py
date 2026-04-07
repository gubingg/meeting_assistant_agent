from __future__ import annotations

from pydantic import BaseModel


class ProjectExportSummaryResponse(BaseModel):
    project_id: int
    format: str
    content: str
