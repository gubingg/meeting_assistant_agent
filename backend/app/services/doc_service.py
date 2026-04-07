from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.doc_processing import get_doc_parse_status_label, get_task_link_suggestion_status_label
from app.constants.doc_types import get_doc_type_label, require_doc_type
from app.constants.task_statuses import get_task_status_label, normalize_task_status
from app.core.config import get_settings
from app.models import Project, ProjectDoc, ProjectDocVersion, TaskLinkSuggestion
from app.rag.chroma_client import ChromaIndexClient
from app.rag.chunker import TextChunker
from app.schemas.doc import (
    ProjectDocItemResponse,
    ProjectDocUploadResponse,
    ProjectDocVersionDetailResponse,
    ProjectDocVersionItemResponse,
    TaskLinkSuggestionActionResponse,
    TaskLinkSuggestionItemResponse,
    UpdatedDocVersionItem,
)
from app.services.task_link_suggestion_service import TaskLinkSuggestionService
from app.utils.file_parser import parse_reference_document
from app.utils.versioning import next_version_label

logger = logging.getLogger(__name__)


class DocService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.chunker = TextChunker()
        self.chroma = ChromaIndexClient()
        self.task_link_service = TaskLinkSuggestionService()

    def _save_file(self, project_id: int, file_name: str, content: bytes) -> None:
        target_dir = Path(self.settings.upload_dir) / f'project_{project_id}' / 'docs'
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / file_name).write_bytes(content)

    def _pending_suggestions(self, doc: ProjectDoc) -> list[TaskLinkSuggestion]:
        return [item for item in doc.task_link_suggestions if item.status == 'pending']

    def _build_doc_item(self, doc: ProjectDoc) -> ProjectDocItemResponse:
        pending_suggestions = self._pending_suggestions(doc)
        return ProjectDocItemResponse(
            id=doc.id,
            title=doc.title or doc.doc_name,
            doc_name=doc.doc_name,
            doc_type=doc.doc_type,
            doc_type_label=get_doc_type_label(doc.doc_type),
            parse_status=doc.parse_status,
            parse_status_label=get_doc_parse_status_label(doc.parse_status),
            qa_enabled=bool(doc.qa_enabled),
            has_task_link_suggestion=bool(pending_suggestions),
            task_link_suggestion_count=len(pending_suggestions),
            current_version_label=doc.current_version.version_label if doc.current_version else None,
            updated_at=doc.updated_at,
        )

    def _build_upload_response(self, doc: ProjectDoc, indexed_chunks: int) -> ProjectDocUploadResponse:
        pending_suggestions = self._pending_suggestions(doc)
        return ProjectDocUploadResponse(
            doc_id=doc.id,
            title=doc.title or doc.doc_name,
            doc_name=doc.doc_name,
            doc_type=doc.doc_type,
            doc_type_label=get_doc_type_label(doc.doc_type),
            parse_status=doc.parse_status,
            parse_status_label=get_doc_parse_status_label(doc.parse_status),
            qa_enabled=bool(doc.qa_enabled),
            has_task_link_suggestion=bool(pending_suggestions),
            task_link_suggestion_count=len(pending_suggestions),
            current_version_label=doc.current_version.version_label if doc.current_version else 'v1',
            indexed_chunks=indexed_chunks,
        )

    def upload_doc(self, db: Session, project: Project, doc_type: str, file_name: str, content: bytes, title: str | None = None) -> ProjectDocUploadResponse:
        if project.status == 'archived':
            raise ValueError('Archived project is read-only')

        normalized_type = require_doc_type(doc_type)
        display_title = (title or '').strip() or Path(file_name).stem
        self._save_file(project.id, file_name, content)
        doc = db.scalar(select(ProjectDoc).where(ProjectDoc.project_id == project.id, ProjectDoc.doc_name == file_name))
        if doc is None:
            doc = ProjectDoc(
                project_id=project.id,
                title=display_title,
                doc_type=normalized_type,
                doc_name=file_name,
                content='',
                parse_status='processing',
                qa_enabled=False,
            )
            db.add(doc)
            db.flush()
            version_label = 'v1'
        else:
            doc.title = display_title
            doc.doc_type = normalized_type
            doc.parse_status = 'processing'
            doc.qa_enabled = False
            version_label = next_version_label(doc.current_version.version_label if doc.current_version else None)

        indexed_chunks = 0
        try:
            parsed = parse_reference_document(file_name, content)
            content_raw = '\n\n'.join(parsed.paragraphs).strip()
            if not content_raw:
                content_raw = content.decode('utf-8', errors='ignore')
            version = ProjectDocVersion(
                project_doc_id=doc.id,
                version_label=version_label,
                content_raw=content_raw,
                change_summary='手动上传项目资料',
                source_meeting_id=None,
                status='active',
                file_name=file_name,
            )
            db.add(version)
            db.flush()
            doc.current_version_id = version.id
            doc.content = content_raw
            doc.parse_status = 'completed'
            doc.qa_enabled = True
            doc.updated_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            db.add_all([doc, project])
            db.flush()

            chunks = self.chunker.chunk_document(doc.title or file_name, parsed.paragraphs or [content_raw])
            indexed_chunks = len(chunks)
            self.chroma.upsert([
                {
                    'id': chunk.chunk_id,
                    'text': chunk.text,
                    'metadata': {
                        'project_id': project.id,
                        'source_type': 'project_doc_version',
                        'source_id': version.id,
                        'meeting_id': -1,
                        'doc_id': doc.id,
                        'doc_version_id': version.id,
                        'title': doc.title or doc.doc_name,
                        'chunk_id': chunk.chunk_id,
                        'doc_type': normalized_type,
                        'doc_type_label': get_doc_type_label(normalized_type),
                    },
                }
                for chunk in chunks
            ])

            self.task_link_service.create_suggestions(db, project, doc)
            db.commit()
            db.refresh(doc)
            return self._build_upload_response(doc, indexed_chunks)
        except Exception:
            logger.exception('Project document upload failed: project_id=%s file_name=%s', project.id, file_name)
            db.rollback()
            doc.parse_status = 'failed'
            doc.qa_enabled = False
            doc.updated_at = datetime.utcnow()
            db.add(doc)
            db.commit()
            db.refresh(doc)
            return self._build_upload_response(doc, indexed_chunks)

    def list_docs(self, project: Project, doc_type: str = 'all') -> list[ProjectDocItemResponse]:
        normalized_filter = None if doc_type == 'all' else require_doc_type(doc_type)
        items = []
        for doc in sorted(project.docs, key=lambda item: item.updated_at or item.created_at, reverse=True):
            doc.doc_type = require_doc_type(doc.doc_type)
            if normalized_filter and doc.doc_type != normalized_filter:
                continue
            items.append(self._build_doc_item(doc))
        return items

    def list_versions(self, db: Session, doc_id: int) -> list[ProjectDocVersionItemResponse]:
        doc = db.get(ProjectDoc, doc_id)
        if doc is None:
            raise ValueError('Project doc not found')
        doc.doc_type = require_doc_type(doc.doc_type)
        return [ProjectDocVersionItemResponse(id=version.id, version_label=version.version_label, change_summary=version.change_summary, source_meeting_id=version.source_meeting_id, status=version.status, created_at=version.created_at) for version in sorted(doc.versions, key=lambda item: item.created_at, reverse=True)]

    def get_version_detail(self, db: Session, version_id: int) -> ProjectDocVersionDetailResponse:
        version = db.get(ProjectDocVersion, version_id)
        if version is None:
            raise ValueError('Doc version not found')
        return ProjectDocVersionDetailResponse(id=version.id, project_doc_id=version.project_doc_id, version_label=version.version_label, content_raw=version.content_raw, change_summary=version.change_summary, source_meeting_id=version.source_meeting_id, status=version.status, created_at=version.created_at)

    def list_task_link_suggestions(self, db: Session, project_id: int, doc_id: int) -> list[TaskLinkSuggestionItemResponse]:
        doc = db.get(ProjectDoc, doc_id)
        if doc is None or doc.project_id != project_id:
            raise ValueError('Project doc not found')
        pending = [item for item in sorted(doc.task_link_suggestions, key=lambda value: value.created_at, reverse=True) if item.status == 'pending']
        return [
            TaskLinkSuggestionItemResponse(
                suggestion_id=item.id,
                task_id=item.task_id,
                task_title=item.task.title,
                owner=item.task.owner,
                current_status=item.task.status,
                current_status_label=get_task_status_label(item.task.status),
                source_meeting=item.task.source_meeting.title if item.task.source_meeting else None,
                suggested_status=item.suggested_status,
                suggested_status_label=get_task_status_label(item.suggested_status),
                match_reason=item.match_reason,
                match_score=item.match_score,
            )
            for item in pending
        ]

    def confirm_task_link_suggestion(self, db: Session, project_id: int, doc_id: int, suggestion_id: int, update_task_status: str) -> TaskLinkSuggestionActionResponse:
        suggestion = db.get(TaskLinkSuggestion, suggestion_id)
        if suggestion is None or suggestion.project_id != project_id or suggestion.doc_id != doc_id:
            raise ValueError('Task link suggestion not found')
        normalized_status = normalize_task_status(update_task_status)
        suggestion.status = 'confirmed'
        suggestion.suggested_status = normalized_status
        suggestion.task.status = normalized_status
        suggestion.task.updated_at = datetime.utcnow()
        suggestion.updated_at = datetime.utcnow()
        suggestion.doc.updated_at = datetime.utcnow()
        suggestion.project.updated_at = datetime.utcnow()
        db.add_all([suggestion, suggestion.task, suggestion.doc, suggestion.project])
        db.commit()
        db.refresh(suggestion)
        return TaskLinkSuggestionActionResponse(
            suggestion_id=suggestion.id,
            suggestion_status=suggestion.status,
            suggestion_status_label=get_task_link_suggestion_status_label(suggestion.status),
            task_id=suggestion.task_id,
            task_status=suggestion.task.status,
            task_status_label=get_task_status_label(suggestion.task.status),
        )

    def ignore_task_link_suggestion(self, db: Session, project_id: int, doc_id: int, suggestion_id: int) -> TaskLinkSuggestionActionResponse:
        suggestion = db.get(TaskLinkSuggestion, suggestion_id)
        if suggestion is None or suggestion.project_id != project_id or suggestion.doc_id != doc_id:
            raise ValueError('Task link suggestion not found')
        suggestion.status = 'ignored'
        suggestion.updated_at = datetime.utcnow()
        suggestion.doc.updated_at = datetime.utcnow()
        suggestion.project.updated_at = datetime.utcnow()
        db.add_all([suggestion, suggestion.doc, suggestion.project])
        db.commit()
        db.refresh(suggestion)
        return TaskLinkSuggestionActionResponse(
            suggestion_id=suggestion.id,
            suggestion_status=suggestion.status,
            suggestion_status_label=get_task_link_suggestion_status_label(suggestion.status),
            task_id=suggestion.task_id,
            task_status=suggestion.task.status,
            task_status_label=get_task_status_label(suggestion.task.status),
        )

    def apply_meeting_updates(self, db: Session, project: Project, meeting, doc_updates: list[dict]) -> list[UpdatedDocVersionItem]:
        created: list[UpdatedDocVersionItem] = []
        for item in doc_updates:
            doc = item['doc']
            doc.doc_type = require_doc_type(doc.doc_type)
            base_content = doc.current_version.content_raw if doc.current_version else ''
            new_label = next_version_label(doc.current_version.version_label if doc.current_version else None)
            version = ProjectDocVersion(project_doc_id=doc.id, version_label=new_label, content_raw=(base_content + '\n\n## 会议更新\n' + meeting.summary).strip(), change_summary=item['change_summary'], source_meeting_id=meeting.id, status='active', file_name=doc.doc_name)
            db.add(version)
            db.flush()
            doc.current_version_id = version.id
            doc.content = version.content_raw
            doc.parse_status = 'completed'
            doc.qa_enabled = True
            doc.updated_at = datetime.utcnow()
            db.add(doc)
            chunks = self.chunker.chunk_document(doc.title or doc.doc_name, [version.content_raw])
            self.chroma.upsert([
                {
                    'id': chunk.chunk_id,
                    'text': chunk.text,
                    'metadata': {
                        'project_id': project.id,
                        'source_type': 'project_doc_version',
                        'source_id': version.id,
                        'meeting_id': meeting.id,
                        'doc_id': doc.id,
                        'doc_version_id': version.id,
                        'title': doc.title or doc.doc_name,
                        'chunk_id': chunk.chunk_id,
                        'doc_type': doc.doc_type,
                        'doc_type_label': get_doc_type_label(doc.doc_type),
                    },
                }
                for chunk in chunks
            ])
            created.append(UpdatedDocVersionItem(doc_id=doc.id, doc_name=doc.doc_name, doc_type=doc.doc_type, doc_type_label=get_doc_type_label(doc.doc_type), version_id=version.id, version_label=version.version_label, change_summary=version.change_summary))
        return created
