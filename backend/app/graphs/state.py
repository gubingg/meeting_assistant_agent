from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.models import Meeting, Project, ProjectDoc, Task
from app.services.transcript_parser import ParsedTranscript


class MeetingWorkflowState(TypedDict, total=False):
    db: Session
    project: Project
    meeting: Meeting
    parsed: ParsedTranscript
    raw_json: dict | None
    project_tasks: list[Task]
    project_docs: list[ProjectDoc]
    planner_strategy: dict
    analysis: dict
    resolved_tasks: list[dict]
    doc_updates: list[dict]
    response: dict


class QAWorkflowState(TypedDict, total=False):
    project_name: str
    question: str
    current_tasks: list[dict]
    retrieved_meeting_chunks: list[dict]
    retrieved_current_doc_chunks: list[dict]
    retrieved_history_doc_chunks: list[dict]
    doc_update_tasks: list[dict]
    chat_history: list[dict]
    citation_pool: list[Any]
    response: object
