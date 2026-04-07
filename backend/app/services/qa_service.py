from __future__ import annotations

from sqlalchemy.orm import Session

from app.agents.project_qa_agent import ProjectQAAgent
from app.constants.doc_types import infer_preferred_doc_types
from app.constants.task_statuses import get_task_status_label
from app.graphs.qa_workflow import QAWorkflow
from app.models import ChatLog
from app.rag.retriever import ProjectRetriever
from app.schemas.qa import CitationItem, ProjectQAHistoryItem, ProjectQAResponse
from app.services.project_service import ProjectService


class QAService:
    def __init__(self) -> None:
        self.project_service = ProjectService()
        self.retriever = ProjectRetriever()
        self.project_qa_agent = ProjectQAAgent()
        self.workflow = QAWorkflow(self.project_qa_agent).build()

    def ask(self, db: Session, project_id: int, question: str) -> ProjectQAResponse:
        project = self.project_service.get_project(db, project_id)
        preferred_doc_types = infer_preferred_doc_types(question)
        evidences = self.retriever.retrieve(project.id, question, {'meeting', 'project_doc_version'}, top_k=8, preferred_doc_types=preferred_doc_types)

        current_version_ids = {doc.current_version.id: doc for doc in project.docs if doc.current_version is not None}
        current_tasks = [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'owner': task.owner,
                'status': task.status,
                'status_label': get_task_status_label(task.status),
                'due_date': task.due_date.isoformat() if task.due_date else None,
            }
            for task in project.tasks
        ]

        retrieved_meeting_chunks = []
        retrieved_current_doc_chunks = []
        retrieved_history_doc_chunks = []
        citation_pool: list[CitationItem] = []

        for item in evidences:
            if item.source_type == 'meeting':
                chunk = {
                    'source_id': str(item.source_id or item.chunk_id),
                    'label': item.title or item.topic_hint or item.snippet[:24],
                    'snippet': item.snippet,
                }
                retrieved_meeting_chunks.append(chunk)
                citation_pool.append(CitationItem(source_type='meeting', label=chunk['label'], source_id=chunk['source_id'], doc_type=item.doc_type, doc_type_label=item.doc_type_label))
            elif item.source_type == 'project_doc_version':
                source_type = 'project_doc_current' if item.doc_version_id in current_version_ids else 'project_doc_history'
                label = f"{item.doc_type_label or '项目资料'} / {item.title or item.topic_hint or '未命名资料'}"
                chunk = {
                    'source_id': str(item.source_id or item.chunk_id),
                    'label': label,
                    'snippet': item.snippet,
                    'doc_type': item.doc_type,
                    'doc_type_label': item.doc_type_label,
                }
                if source_type == 'project_doc_current':
                    retrieved_current_doc_chunks.append(chunk)
                else:
                    retrieved_history_doc_chunks.append(chunk)
                citation_pool.append(CitationItem(source_type=source_type, label=label, source_id=chunk['source_id'], doc_type=item.doc_type, doc_type_label=item.doc_type_label))

        doc_update_tasks = [
            {
                'source_id': str(task.id),
                'label': f'待办：{task.title}',
                'title': task.title,
                'status': task.status,
                'status_label': get_task_status_label(task.status),
            }
            for task in project.tasks
            if any(keyword in (task.title + ' ' + (task.description or '')) for keyword in ['PRD', '文档', '资料', '方案', '测试', '字段'])
        ]
        for item in doc_update_tasks:
            citation_pool.append(CitationItem(source_type='doc_update_task', label=item['label'], source_id=item['source_id']))

        chat_history = [
            {
                'source_id': str(log.id),
                'label': f'历史问答 {log.id}',
                'question': log.question,
                'answer': log.answer,
            }
            for log in sorted(project.chat_logs, key=lambda log: log.created_at, reverse=True)[:3]
        ]
        for item in chat_history:
            citation_pool.append(CitationItem(source_type='chat_history', label=item['label'], source_id=item['source_id']))

        response: ProjectQAResponse = self.workflow.invoke(
            {
                'project_name': project.name,
                'question': question,
                'current_tasks': current_tasks,
                'retrieved_meeting_chunks': retrieved_meeting_chunks,
                'retrieved_current_doc_chunks': retrieved_current_doc_chunks,
                'retrieved_history_doc_chunks': retrieved_history_doc_chunks,
                'doc_update_tasks': doc_update_tasks,
                'chat_history': chat_history,
                'citation_pool': citation_pool,
            }
        )['response']
        db.add(ChatLog(project_id=project.id, question=question, answer=response.answer, citations_json=[item.model_dump() for item in response.citations]))
        self.project_service.touch_project(db, project)
        db.commit()
        return response

    def history(self, db: Session, project_id: int) -> list[ProjectQAHistoryItem]:
        project = self.project_service.get_project(db, project_id)
        return [
            ProjectQAHistoryItem(
                id=item.id,
                question=item.question,
                answer=item.answer,
                citations=[CitationItem(**citation) for citation in item.citations_json or []],
                created_at=item.created_at,
            )
            for item in sorted(project.chat_logs, key=lambda log: log.created_at)
        ]
