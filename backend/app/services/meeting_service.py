from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.meeting_analyst_agent import MeetingAnalystAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.project_doc_update_agent import ProjectDocUpdateAgent
from app.agents.task_continuity_agent import TaskContinuityAgent
from app.core.config import get_settings
from app.graphs.meeting_workflow import MeetingWorkflow
from app.models import Meeting, Project, ProjectDoc, Task
from app.rag.chroma_client import ChromaIndexClient
from app.rag.chunker import TextChunker
from app.schemas.meeting import MeetingDecisionItemResponse, MeetingDetailResponse, MeetingListItemResponse, MeetingRiskItemResponse, MeetingTaskItemResponse, MeetingUploadResponse
from app.services.doc_service import DocService
from app.services.project_service import ProjectService
from app.services.transcript_parser import parse_transcript


class MeetingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.project_service = ProjectService()
        self.doc_service = DocService()
        self.chunker = TextChunker()
        self.chroma = ChromaIndexClient()
        self.workflow = MeetingWorkflow(
            planner=PlannerAgent(),
            analyst=MeetingAnalystAgent(),
            continuity=TaskContinuityAgent(),
            doc_updater=ProjectDocUpdateAgent(),
            persist_fn=self._persist_results,
            chroma_ingest_fn=self._ingest_chroma,
        ).build()

    def _save_file(self, project_id: int, meeting_id: int, file_name: str, content: bytes) -> None:
        target_dir = Path(self.settings.upload_dir) / f'project_{project_id}' / 'meetings' / str(meeting_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / file_name).write_bytes(content)

    def list_meetings(self, project: Project) -> list[MeetingListItemResponse]:
        items = []
        for meeting in sorted(project.meetings, key=lambda item: item.meeting_time or item.created_at, reverse=True):
            tasks = [task for task in project.tasks if task.source_meeting_id == meeting.id]
            items.append(MeetingListItemResponse(id=meeting.id, title=meeting.title, meeting_time=meeting.meeting_time, summary_preview=(meeting.summary or '')[:80], risk_count=len(meeting.risks_json or []), task_count=len(tasks), decision_count=len(meeting.decisions_json or [])))
        return items

    def upload_meeting(self, db: Session, project_id: int, file_name: str, content: bytes) -> MeetingUploadResponse:
        project = self.project_service.get_project(db, project_id)
        if project.status == 'archived':
            raise ValueError('Archived project is read-only')
        raw_text = content.decode('utf-8', errors='ignore')
        raw_json = json.loads(raw_text) if file_name.lower().endswith('.json') else None
        parsed = parse_transcript(file_name, content)
        meeting_time = parsed.meeting_date or datetime.utcnow()
        meeting = Meeting(
            meeting_uuid=uuid4().hex,
            project_id=project.id,
            title=parsed.title,
            meeting_date=meeting_time,
            meeting_time=meeting_time,
            participants=parsed.participants,
            participants_json=parsed.participants,
            raw_json=raw_json,
            raw_text=raw_text,
            summary='',
            decisions_json=[],
            risks_json=[],
            transcript_file_path=file_name,
            source_file_name=file_name,
        )
        db.add(meeting)
        db.flush()
        self._save_file(project.id, meeting.id, file_name, content)

        project_tasks = list(db.scalars(select(Task).where(Task.project_id == project.id)).all())
        project_docs = list(db.scalars(select(ProjectDoc).where(ProjectDoc.project_id == project.id)).all())

        state = self.workflow.invoke(
            {
                'db': db,
                'project': project,
                'meeting': meeting,
                'parsed': parsed,
                'raw_json': raw_json,
                'project_tasks': project_tasks,
                'project_docs': project_docs,
            }
        )
        db.commit()
        db.refresh(meeting)
        return MeetingUploadResponse(**state['response'])

    def _persist_results(self, state: dict) -> dict:
        db: Session = state['db']
        project: Project = state['project']
        meeting: Meeting = state['meeting']
        analysis = state['analysis']
        meeting.summary = analysis.get('summary', '')
        meeting.decisions_json = analysis.get('decisions', [])
        meeting.risks_json = analysis.get('risks', [])
        db.add(meeting)
        for item in state['resolved_tasks']:
            if item['task_id']:
                task = db.get(Task, item['task_id'])
                # ?????????????????????????????????????????
                task.owner = item.get('owner') or task.owner
                task.due_date = item.get('due_date') or task.due_date
                task.status = item['status']
                task.latest_update_meeting_id = meeting.id
                db.add(task)
            else:
                db.add(Task(project_id=project.id, title=item['title'], description=item.get('description'), owner=item.get('owner'), due_date=item.get('due_date'), status=item['status'], source_meeting_id=meeting.id, latest_update_meeting_id=meeting.id))
        project.updated_at = datetime.utcnow()
        db.add(project)
        db.flush()
        updated_doc_versions = self.doc_service.apply_meeting_updates(db, project, meeting, state['doc_updates'])
        db.flush()
        tasks = list(db.scalars(select(Task).where(Task.project_id == project.id, Task.source_meeting_id == meeting.id)).all())
        return MeetingUploadResponse(
            meeting_id=meeting.id,
            title=meeting.title,
            meeting_time=meeting.meeting_time,
            summary=meeting.summary,
            decisions=[MeetingDecisionItemResponse(text=item.get('text', '')) for item in meeting.decisions_json or []],
            tasks=[MeetingTaskItemResponse(id=task.id, title=task.title, description=task.description, owner=task.owner, due_date=task.due_date, status=task.status) for task in tasks],
            risks=[MeetingRiskItemResponse(text=item.get('text', '')) for item in meeting.risks_json or []],
            updated_doc_versions=updated_doc_versions,
        ).model_dump()

    def _ingest_chroma(self, state: dict) -> None:
        meeting: Meeting = state['meeting']
        project: Project = state['project']
        chunks = self.chunker.chunk_document(meeting.title, [meeting.raw_text or meeting.summary])
        self.chroma.upsert([
            {
                'id': chunk.chunk_id,
                'text': chunk.text,
                'metadata': {
                    'project_id': project.id,
                    'source_type': 'meeting',
                    'source_id': meeting.id,
                    'meeting_id': meeting.id,
                    'doc_id': -1,
                    'doc_version_id': -1,
                    'title': meeting.title,
                    'chunk_id': chunk.chunk_id,
                },
            }
            for chunk in chunks
        ])

    def get_meeting_detail(self, db: Session, meeting_id: int) -> MeetingDetailResponse:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            raise ValueError('Meeting not found')
        project = meeting.project
        tasks = [task for task in project.tasks if task.source_meeting_id == meeting.id]
        return MeetingDetailResponse(
            id=meeting.id,
            project_id=meeting.project_id,
            title=meeting.title,
            meeting_time=meeting.meeting_time,
            participants=meeting.participants_json or meeting.participants or [],
            summary=meeting.summary,
            decisions=[MeetingDecisionItemResponse(text=item.get('text', '')) for item in meeting.decisions_json or []],
            tasks=[MeetingTaskItemResponse(id=task.id, title=task.title, description=task.description, owner=task.owner, due_date=task.due_date, status=task.status) for task in tasks],
            risks=[MeetingRiskItemResponse(text=item.get('text', '')) for item in meeting.risks_json or []],
            raw_json=meeting.raw_json,
            raw_text=meeting.raw_text,
            source_file_name=meeting.source_file_name,
        )
