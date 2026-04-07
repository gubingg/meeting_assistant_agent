from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class BaseModelMixin:
    pass


class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    meetings: Mapped[list['Meeting']] = relationship(back_populates='project', cascade='all, delete-orphan')
    tasks: Mapped[list['Task']] = relationship(back_populates='project', cascade='all, delete-orphan')
    docs: Mapped[list['ProjectDoc']] = relationship(back_populates='project', cascade='all, delete-orphan')
    chat_logs: Mapped[list['ChatLog']] = relationship(back_populates='project', cascade='all, delete-orphan')
    task_link_suggestions: Mapped[list['TaskLinkSuggestion']] = relationship(back_populates='project', cascade='all, delete-orphan')


class Meeting(Base):
    __tablename__ = 'meetings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    meeting_uuid: Mapped[str] = mapped_column(String(64), nullable=False, default=lambda: uuid4().hex)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    meeting_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    participants: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    participants_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default='')
    decisions_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    risks_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    transcript_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped['Project'] = relationship(back_populates='meetings')
    source_tasks: Mapped[list['Task']] = relationship(back_populates='source_meeting', foreign_keys='Task.source_meeting_id')
    updated_tasks: Mapped[list['Task']] = relationship(back_populates='latest_update_meeting', foreign_keys='Task.latest_update_meeting_id')
    doc_versions: Mapped[list['ProjectDocVersion']] = relationship(back_populates='source_meeting')


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='new')
    source_meeting_id: Mapped[int | None] = mapped_column(ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    latest_update_meeting_id: Mapped[int | None] = mapped_column(ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped['Project'] = relationship(back_populates='tasks')
    source_meeting: Mapped['Meeting | None'] = relationship(back_populates='source_tasks', foreign_keys=[source_meeting_id])
    latest_update_meeting: Mapped['Meeting | None'] = relationship(back_populates='updated_tasks', foreign_keys=[latest_update_meeting_id])
    task_link_suggestions: Mapped[list['TaskLinkSuggestion']] = relationship(back_populates='task')


class ProjectDoc(Base):
    __tablename__ = 'project_docs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default='')
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    doc_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), nullable=False, default='processing')
    qa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_version_id: Mapped[int | None] = mapped_column(ForeignKey('project_doc_versions.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped['Project'] = relationship(back_populates='docs')
    versions: Mapped[list['ProjectDocVersion']] = relationship(back_populates='project_doc', cascade='all, delete-orphan', foreign_keys='ProjectDocVersion.project_doc_id')
    current_version: Mapped['ProjectDocVersion | None'] = relationship(foreign_keys=[current_version_id], post_update=True)
    task_link_suggestions: Mapped[list['TaskLinkSuggestion']] = relationship(back_populates='doc', cascade='all, delete-orphan')


class ProjectDocVersion(Base):
    __tablename__ = 'project_doc_versions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_doc_id: Mapped[int] = mapped_column(ForeignKey('project_docs.id', ondelete='CASCADE'), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(30), nullable=False)
    content_raw: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_meeting_id: Mapped[int | None] = mapped_column(ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project_doc: Mapped['ProjectDoc'] = relationship(back_populates='versions', foreign_keys=[project_doc_id])
    source_meeting: Mapped['Meeting | None'] = relationship(back_populates='doc_versions')


class TaskLinkSuggestion(Base):
    __tablename__ = 'task_link_suggestions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey('project_docs.id', ondelete='CASCADE'), nullable=False, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_status: Mapped[str] = mapped_column(String(32), nullable=False, default='pending_confirmation')
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped['Project'] = relationship(back_populates='task_link_suggestions')
    doc: Mapped['ProjectDoc'] = relationship(back_populates='task_link_suggestions')
    task: Mapped['Task'] = relationship(back_populates='task_link_suggestions')


class ChatLog(Base):
    __tablename__ = 'chat_logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped['Project'] = relationship(back_populates='chat_logs')


__all__ = ['BaseModelMixin', 'ChatLog', 'Meeting', 'Project', 'ProjectDoc', 'ProjectDocVersion', 'Task', 'TaskLinkSuggestion']
