from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.qa import ProjectQARequest
from app.services.qa_service import QAService

router = APIRouter(tags=['qa'])
service = QAService()


@router.post('/api/projects/{project_id}/qa')
def ask_project_question(project_id: int, payload: ProjectQARequest, db: Session = Depends(get_db)):
    try:
        return service.ask(db, project_id, payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/api/projects/{project_id}/qa/history')
def project_qa_history(project_id: int, db: Session = Depends(get_db)):
    try:
        return service.history(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
