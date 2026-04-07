from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.export_service import ExportService

router = APIRouter(tags=['export'])
service = ExportService()


@router.get('/api/projects/{project_id}/export-summary')
def export_project_summary(project_id: int, db: Session = Depends(get_db)):
    try:
        return service.export_project_summary(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
