from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.meeting_service import MeetingService
from app.services.project_service import ProjectService

router = APIRouter(tags=['meetings'])
meeting_service = MeetingService()
project_service = ProjectService()


@router.get('/api/projects/{project_id}/meetings')
def list_project_meetings(project_id: int, db: Session = Depends(get_db)):
    try:
        project = project_service.get_project(db, project_id)
        return meeting_service.list_meetings(project)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/api/projects/{project_id}/meetings/upload')
async def upload_project_meeting(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    payload = await file.read()
    try:
        return meeting_service.upload_meeting(db, project_id, file.filename, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/api/meetings/{meeting_id}')
def get_meeting_detail(meeting_id: int, db: Session = Depends(get_db)):
    try:
        return meeting_service.get_meeting_detail(db, meeting_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
