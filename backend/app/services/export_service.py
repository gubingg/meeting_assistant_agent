from __future__ import annotations

from app.schemas.export import ProjectExportSummaryResponse
from app.services.project_service import ProjectService
from app.utils.export_builder import build_project_summary_markdown


class ExportService:
    def __init__(self) -> None:
        self.project_service = ProjectService()

    def export_project_summary(self, db, project_id: int) -> ProjectExportSummaryResponse:
        project = self.project_service.get_project(db, project_id)
        meetings = sorted(project.meetings, key=lambda item: item.meeting_time or item.created_at)
        return ProjectExportSummaryResponse(project_id=project.id, format='markdown', content=build_project_summary_markdown(project, meetings))
