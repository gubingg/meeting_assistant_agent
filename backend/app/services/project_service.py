from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project
from app.schemas.project import CreateProjectRequest, ProjectCardResponse, ProjectDetailResponse, ProjectStatusResponse


class ProjectService:
    def _slugify(self, name: str) -> str:
        base = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', name.strip().lower()).strip('-') or 'project'
        return base[:100]

    def _unique_slug(self, db: Session, name: str) -> str:
        base = self._slugify(name)
        slug = base
        index = 2
        while db.scalar(select(Project).where(Project.slug == slug)) is not None:
            slug = f'{base}-{index}'
            index += 1
        return slug

    def get_project(self, db: Session, project_id: int) -> Project:
        project = db.get(Project, project_id)
        if project is None:
            raise ValueError('Project not found')
        return project

    def touch_project(self, db: Session, project: Project) -> None:
        project.updated_at = datetime.utcnow()
        db.add(project)

    def _build_card(self, project: Project) -> ProjectCardResponse:
        latest_meeting = max((meeting.meeting_time for meeting in project.meetings if meeting.meeting_time), default=None)
        todo_count = len(project.tasks)
        unfinished_count = len([item for item in project.tasks if item.status not in {'done', 'cancelled'}])
        return ProjectCardResponse(
            id=project.id,
            slug=project.slug,
            name=project.name,
            description=project.description,
            owner=project.owner,
            start_date=project.start_date,
            status=project.status,
            archived_at=project.archived_at,
            last_updated_at=project.updated_at,
            latest_meeting_time=latest_meeting,
            todo_count=todo_count,
            meeting_count=len(project.meetings),
            unfinished_todo_count=unfinished_count,
        )

    def list_projects(self, db: Session, status: str = 'all') -> list[ProjectCardResponse]:
        stmt = select(Project).order_by(Project.updated_at.desc())
        projects = list(db.scalars(stmt).all())
        if status != 'all':
            projects = [project for project in projects if project.status == status]
        projects.sort(key=lambda item: (item.status != 'active', -(item.updated_at.timestamp() if item.updated_at else 0)))
        return [self._build_card(project) for project in projects]

    def create_project(self, db: Session, payload: CreateProjectRequest) -> ProjectDetailResponse:
        project = Project(
            slug=self._unique_slug(db, payload.name),
            name=payload.name.strip(),
            description=payload.description.strip(),
            owner=payload.owner.strip(),
            start_date=payload.start_date,
            status='active',
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return self.get_project_detail(db, project.id)

    def get_project_detail(self, db: Session, project_id: int) -> ProjectDetailResponse:
        project = self.get_project(db, project_id)
        return ProjectDetailResponse(
            id=project.id,
            slug=project.slug,
            name=project.name,
            description=project.description,
            owner=project.owner,
            start_date=project.start_date,
            status=project.status,
            archived_at=project.archived_at,
            meeting_count=len(project.meetings),
            todo_count=len(project.tasks),
            latest_updated_at=project.updated_at,
        )

    def archive_project(self, db: Session, project_id: int) -> ProjectStatusResponse:
        project = self.get_project(db, project_id)
        project.status = 'archived'
        project.archived_at = datetime.utcnow()
        self.touch_project(db, project)
        db.commit()
        db.refresh(project)
        return ProjectStatusResponse(id=project.id, status=project.status, archived_at=project.archived_at)

    def reopen_project(self, db: Session, project_id: int) -> ProjectStatusResponse:
        project = self.get_project(db, project_id)
        project.status = 'active'
        project.archived_at = None
        self.touch_project(db, project)
        db.commit()
        db.refresh(project)
        return ProjectStatusResponse(id=project.id, status=project.status, archived_at=project.archived_at)
