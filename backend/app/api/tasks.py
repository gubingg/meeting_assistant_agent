from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter(tags=['tasks'])
project_service = ProjectService()
task_service = TaskService()


@router.get('/api/projects/{project_id}/tasks')
def list_project_tasks(project_id: int, status: str = Query(default='all'), db: Session = Depends(get_db)):
    try:
        project = project_service.get_project(db, project_id)
        return task_service.list_tasks(project.id, project.tasks, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/api/projects/{project_id}/tasks/summary')
def get_task_summary(project_id: int, db: Session = Depends(get_db)):
    try:
        project = project_service.get_project(db, project_id)
        return task_service.build_summary(project.tasks)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
