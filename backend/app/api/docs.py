from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.doc import ConfirmTaskLinkSuggestionRequest
from app.services.doc_service import DocService
from app.services.project_service import ProjectService

router = APIRouter(tags=['docs'])
doc_service = DocService()
project_service = ProjectService()


@router.post('/api/projects/{project_id}/docs')
@router.post('/api/projects/{project_id}/docs/upload')
async def upload_project_doc(
    project_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    payload = await file.read()
    try:
        project = project_service.get_project(db, project_id)
        return doc_service.upload_doc(db, project, doc_type, file.filename, payload, title=title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/api/projects/{project_id}/docs')
def list_project_docs(project_id: int, doc_type: str = Query(default='all'), db: Session = Depends(get_db)):
    try:
        project = project_service.get_project(db, project_id)
        return doc_service.list_docs(project, doc_type=doc_type)
    except ValueError as exc:
        status_code = 404 if str(exc) == 'Project not found' else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get('/api/projects/{project_id}/docs/{doc_id}/task-link-suggestions')
def list_doc_task_link_suggestions(project_id: int, doc_id: int, db: Session = Depends(get_db)):
    try:
        return doc_service.list_task_link_suggestions(db, project_id, doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/api/projects/{project_id}/docs/{doc_id}/task-link-suggestions/{suggestion_id}/confirm')
def confirm_doc_task_link_suggestion(project_id: int, doc_id: int, suggestion_id: int, payload: ConfirmTaskLinkSuggestionRequest, db: Session = Depends(get_db)):
    try:
        return doc_service.confirm_task_link_suggestion(db, project_id, doc_id, suggestion_id, payload.update_task_status)
    except ValueError as exc:
        status_code = 404 if 'not found' in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post('/api/projects/{project_id}/docs/{doc_id}/task-link-suggestions/{suggestion_id}/ignore')
def ignore_doc_task_link_suggestion(project_id: int, doc_id: int, suggestion_id: int, db: Session = Depends(get_db)):
    try:
        return doc_service.ignore_task_link_suggestion(db, project_id, doc_id, suggestion_id)
    except ValueError as exc:
        status_code = 404 if 'not found' in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get('/api/docs/{doc_id}/versions')
def list_doc_versions(doc_id: int, db: Session = Depends(get_db)):
    try:
        return doc_service.list_versions(db, doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/api/doc-versions/{version_id}')
def get_doc_version_detail(version_id: int, db: Session = Depends(get_db)):
    try:
        return doc_service.get_version_detail(db, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
