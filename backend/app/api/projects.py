from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.project import CreateProjectRequest
from app.services.project_service import ProjectService

router = APIRouter(prefix='/api/projects', tags=['projects'])
service = ProjectService()


@router.get('')
def list_projects(status: str = Query(default='all'), db: Session = Depends(get_db)):
    return service.list_projects(db, status=status)


@router.post('')
def create_project(payload: CreateProjectRequest, db: Session = Depends(get_db)):
    return service.create_project(db, payload)


@router.get('/{project_id}')
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    try:
        return service.get_project_detail(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/{project_id}/archive')
def archive_project(project_id: int, db: Session = Depends(get_db)):
    try:
        return service.archive_project(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/{project_id}/reopen')
def reopen_project(project_id: int, db: Session = Depends(get_db)):
    try:
        return service.reopen_project(db, project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
