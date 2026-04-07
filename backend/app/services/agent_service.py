from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import ActionItem, ChatMessage, Chunk, Decision, Meeting, MeetingSummary, Utterance
from app.schemas.chat import ChatResponse
from app.schemas.common import EvidenceItem
from app.services.feishu_service import FeishuService
from app.services.llm_service import OpenAICompatibleClient
from app.services.rag_service import RagService
from app.services.skill_service import SkillRegistry


class SkillExecutor:
    def __init__(self) -> None:
        self.registry = SkillRegistry()
        self.rag = RagService()
        self.feishu = FeishuService()

    def _get_current_chunks(self, db: Session, meeting_id: int) -> list[Chunk]:
        return db.scalars(
            select(Chunk).where(Chunk.meeting_id == meeting_id, Chunk.source_type == 'current_transcript')
        ).all()

    def _get_current_lines(self, db: Session, meeting_id: int) -> list[tuple[str, str]]:
        utterances = db.scalars(
            select(Utterance).where(Utterance.meeting_id == meeting_id).order_by(Utterance.turn_index.asc())
        ).all()
        return [(item.speaker or 'Speaker', item.text) for item in utterances]

    def _evidence_ids(self, evidence: list[EvidenceItem]) -> list[str]:
        return [item.chunk_id for item in evidence]

    def execute_summary(self, db: Session, meeting_id: int, evidence: list[EvidenceItem]) -> dict:
        chunks = self._get_current_chunks(db, meeting_id)
        topics = [chunk.topic_hint for chunk in chunks[:4] if chunk.topic_hint]
        summary_lines = [chunk.summary_short for chunk in chunks[:5] if chunk.summary_short]
        risk_lines = [line for line in summary_lines if any(word in line for word in ['risk', 'delay', 'blocked', 'exception'])]
        open_lines = [line for line in summary_lines if any(word in line for word in ['confirm', 'follow-up', 'question'])]
        return {
            'background_text': summary_lines[0] if summary_lines else 'No summary available.',
            'agenda_text': '; '.join(topics) if topics else 'No agenda identified.',
            'summary_text': '\n'.join(f'- {line}' for line in summary_lines) or '- No summary available.',
            'risks_text': '\n'.join(f'- {line}' for line in risk_lines) or 'No explicit risks captured.',
            'open_questions_text': '\n'.join(f'- {line}' for line in open_lines) or 'No open questions captured.',
            'evidence_chunk_ids': self._evidence_ids(evidence),
        }

    def execute_action_items(self, db: Session, meeting_id: int) -> list[dict]:
        lines = self._get_current_lines(db, meeting_id)
        current_chunks = self._get_current_chunks(db, meeting_id)
        fallback_chunk_id = current_chunks[0].chunk_uuid if current_chunks else None
        actions: list[dict] = []
        for speaker, text in lines:
            line = f'[{speaker}] {text}'
            if any(keyword in line for keyword in ['负责', '跟进', '安排', '处理', '确认', '完成']):
                owner = speaker if any(keyword in text for keyword in ['我来', '我负责', '我处理']) else 'unassigned'
                priority = 'high' if any(word in line for word in ['今天', '立即', '尽快', '本周']) else 'medium'
                due_date = datetime.utcnow() if any(word in line for word in ['今天', '今晚']) else None
                actions.append(
                    {
                        'item_uuid': f'ai_{uuid.uuid4().hex[:16]}',
                        'task_content': line[:200],
                        'owner': owner,
                        'due_date': due_date,
                        'priority': priority,
                        'status': 'todo',
                        'dependency_text': 'Depends on another confirmation' if '依赖' in line else None,
                        'evidence_chunk_ids': [fallback_chunk_id] if fallback_chunk_id else [],
                        'is_legacy': False,
                    }
                )
        if not actions and current_chunks:
            actions.append(
                {
                    'item_uuid': f'ai_{uuid.uuid4().hex[:16]}',
                    'task_content': current_chunks[0].summary_short,
                    'owner': 'unassigned',
                    'due_date': None,
                    'priority': 'medium',
                    'status': 'todo',
                    'dependency_text': None,
                    'evidence_chunk_ids': [current_chunks[0].chunk_uuid],
                    'is_legacy': False,
                }
            )
        return actions[:10]

    def execute_decisions(self, db: Session, meeting_id: int) -> list[dict]:
        lines = self._get_current_lines(db, meeting_id)
        current_chunks = self._get_current_chunks(db, meeting_id)
        fallback_chunk_id = current_chunks[0].chunk_uuid if current_chunks else None
        decisions: list[dict] = []
        for speaker, text in lines:
            line = f'[{speaker}] {text}'
            if any(keyword in line for keyword in ['决定', '结论', '通过', '采用', '暂定']):
                status = 'confirmed' if any(word in line for word in ['决定', '通过', '采用']) else 'pending'
                decisions.append(
                    {
                        'decision_uuid': f'd_{uuid.uuid4().hex[:16]}',
                        'decision_text': line[:200],
                        'decision_status': status,
                        'evidence_chunk_ids': [fallback_chunk_id] if fallback_chunk_id else [],
                    }
                )
        return decisions[:10]

    def execute_memory(self, message: str, current_meeting_id: int, source_types: list[str]) -> dict:
        evidence = self.rag.retrieve(message, current_meeting_id, source_types, top_k=5)
        if evidence:
            answer = 'Found related historical context:\n' + '\n'.join(
                f'- [{item.source_type}] {item.snippet}' for item in evidence
            )
        else:
            answer = 'No related historical context found.'
        return {'answer': answer, 'evidence': evidence}

    def persist_summary(self, db: Session, meeting_id: int, payload: dict) -> None:
        latest = db.scalars(
            select(MeetingSummary)
            .where(MeetingSummary.meeting_id == meeting_id)
            .order_by(MeetingSummary.summary_version.desc())
        ).first()
        version = 1 if latest is None else latest.summary_version + 1
        db.add(MeetingSummary(meeting_id=meeting_id, summary_version=version, **payload))
        db.commit()

    def persist_action_items(self, db: Session, meeting_id: int, payload: list[dict]) -> None:
        db.execute(
            delete(ActionItem).where(ActionItem.meeting_id == meeting_id, ActionItem.status.in_(['todo', 'doing']))
        )
        db.add_all(ActionItem(meeting_id=meeting_id, **item) for item in payload)
        db.commit()

    def persist_decisions(self, db: Session, meeting_id: int, payload: list[dict]) -> None:
        db.execute(delete(Decision).where(Decision.meeting_id == meeting_id))
        db.add_all(Decision(meeting_id=meeting_id, **item) for item in payload)
        db.commit()

    def sync_target(self, db: Session, meeting: Meeting, target: str) -> None:
        if target == 'doc':
            self.feishu.sync_doc(db, meeting)
        else:
            self.feishu.sync_bitable(db, meeting)


class AgentService:
    def __init__(self) -> None:
        from app.graph.workflow import MeetingAgentWorkflow

        self.executor = SkillExecutor()
        self.registry = self.executor.registry
        self.llm_client = OpenAICompatibleClient()
        self.workflow = MeetingAgentWorkflow(self).build()

    def classify_intent(self, message: str) -> tuple[str, list[str]]:
        return self.registry.classify_message(message)

    def load_skills(self, intents: list[str]) -> dict[str, str]:
        loaded: dict[str, str] = {}
        for intent in intents:
            skill_name = 'cross_meeting_memory' if intent == 'project_doc_qa' else intent
            loaded[skill_name] = self.registry.load_skill_content(skill_name)
        return loaded

    def retrieve_context(self, message: str, meeting_id: int, intents: list[str]) -> dict[str, list[EvidenceItem]]:
        context: dict[str, list[EvidenceItem]] = {}
        for intent in intents:
            if intent in {'meeting_summary', 'action_items', 'decisions'}:
                context[intent] = self.executor.rag.retrieve(message, meeting_id, ['current_transcript'])
            elif intent == 'cross_meeting_memory':
                context[intent] = self.executor.rag.retrieve(
                    message, meeting_id, ['history_transcript', 'history_minutes', 'project_doc']
                )
            elif intent == 'project_doc_qa':
                context[intent] = self.executor.rag.retrieve(message, meeting_id, ['project_doc'])
            else:
                context[intent] = []
        return context

    def execute(self, db: Session, meeting_id: int, message: str) -> ChatResponse:
        if db.get(Meeting, meeting_id) is None:
            raise ValueError('Meeting not found')
        state = self.workflow.invoke({'meeting_id': meeting_id, 'message': message, 'db': db})
        return state['response']

    def _build_fallback_answer(self, outputs: dict[str, object]) -> str:
        answer_parts: list[str] = []
        if 'meeting_summary' in outputs:
            answer_parts.append('Summary generated.')
        if 'action_items' in outputs:
            answer_parts.append(f"Extracted {len(outputs['action_items'])} action items.")
        if 'decisions' in outputs:
            answer_parts.append(f"Extracted {len(outputs['decisions'])} decisions.")
        if 'cross_meeting_memory' in outputs:
            answer_parts.append(outputs['cross_meeting_memory']['answer'])
        if 'project_doc_qa' in outputs:
            answer_parts.append(outputs['project_doc_qa']['answer'])
        if 'feishu_sync' in outputs:
            answer_parts.append(outputs['feishu_sync']['answer'])
        if not answer_parts:
            answer_parts.append('Request processed.')
        return '\n'.join(answer_parts)

    def _build_llm_prompt(self, message: str, outputs: dict[str, object]) -> tuple[str, str]:
        sections: list[str] = []
        if 'meeting_summary' in outputs:
            summary = outputs['meeting_summary']
            sections.append(
                '\n'.join(
                    [
                        'Meeting summary:',
                        f"Background: {summary.get('background_text', '')}",
                        f"Agenda: {summary.get('agenda_text', '')}",
                        f"Summary: {summary.get('summary_text', '')}",
                        f"Risks: {summary.get('risks_text', '')}",
                        f"Open questions: {summary.get('open_questions_text', '')}",
                    ]
                )
            )
        if 'action_items' in outputs:
            items = outputs['action_items']
            sections.append(
                'Action items:\n' + '\n'.join(
                    f"- {item['task_content']} | owner={item['owner']} | priority={item['priority']}"
                    for item in items[:10]
                )
            )
        if 'decisions' in outputs:
            items = outputs['decisions']
            sections.append(
                'Decisions:\n' + '\n'.join(
                    f"- {item['decision_text']} | status={item['decision_status']}" for item in items[:10]
                )
            )
        if 'cross_meeting_memory' in outputs:
            sections.append('Cross meeting memory:\n' + outputs['cross_meeting_memory']['answer'])
        if 'project_doc_qa' in outputs:
            sections.append('Project document answer:\n' + outputs['project_doc_qa']['answer'])
        if 'feishu_sync' in outputs:
            sections.append('Feishu sync:\n' + outputs['feishu_sync']['answer'])

        system_prompt = (
            'You are a senior meeting assistant. Respond in concise Chinese, grounded in the structured tool output. '
            'Do not invent facts that are not present in the provided execution results.'
        )
        user_prompt = f"User request:\n{message}\n\nExecution results:\n\n" + '\n\n'.join(sections)
        return system_prompt, user_prompt

    def _generate_answer(self, message: str, outputs: dict[str, object]) -> str:
        fallback_answer = self._build_fallback_answer(outputs)
        system_prompt, user_prompt = self._build_llm_prompt(message, outputs)
        generated = self.llm_client.chat(system_prompt, user_prompt)
        return generated.strip() if generated else fallback_answer

    def run_execution(
        self,
        db: Session,
        meeting: Meeting,
        message: str,
        intent: str,
        sub_intents: list[str],
        context: dict[str, list[EvidenceItem]],
    ) -> dict:
        outputs: dict[str, object] = {}
        used_skills: list[str] = []
        all_evidence: dict[str, EvidenceItem] = {}
        flags = {'summary_updated': False, 'action_items_updated': False, 'decisions_updated': False}

        for sub_intent in sub_intents:
            skill_name = 'cross_meeting_memory' if sub_intent == 'project_doc_qa' else sub_intent
            if skill_name not in used_skills:
                used_skills.append(skill_name)
            for item in context.get(sub_intent, []):
                all_evidence[item.chunk_id] = item
            if sub_intent == 'meeting_summary':
                payload = self.executor.execute_summary(db, meeting.id, context.get(sub_intent, []))
                self.executor.persist_summary(db, meeting.id, payload)
                outputs[sub_intent] = payload
                flags['summary_updated'] = True
            elif sub_intent == 'action_items':
                payload = self.executor.execute_action_items(db, meeting.id)
                self.executor.persist_action_items(db, meeting.id, payload)
                outputs[sub_intent] = payload
                flags['action_items_updated'] = True
            elif sub_intent == 'decisions':
                payload = self.executor.execute_decisions(db, meeting.id)
                self.executor.persist_decisions(db, meeting.id, payload)
                outputs[sub_intent] = payload
                flags['decisions_updated'] = True
            elif sub_intent in {'cross_meeting_memory', 'project_doc_qa'}:
                outputs[sub_intent] = self.executor.execute_memory(
                    message,
                    meeting.id,
                    ['project_doc'] if sub_intent == 'project_doc_qa' else ['history_transcript', 'history_minutes', 'project_doc'],
                )
                for item in outputs[sub_intent]['evidence']:
                    all_evidence[item.chunk_id] = item
            elif sub_intent == 'feishu_sync':
                self.executor.sync_target(db, meeting, 'doc')
                self.executor.sync_target(db, meeting, 'bitable')
                outputs[sub_intent] = {'answer': 'Feishu sync completed.'}

        final_answer = self._generate_answer(message, outputs)

        db.add(
            ChatMessage(
                meeting_id=meeting.id,
                role='user',
                content=message,
                intent=intent,
                used_skills=used_skills,
                evidence_chunk_ids=[],
            )
        )
        db.add(
            ChatMessage(
                meeting_id=meeting.id,
                role='assistant',
                content=final_answer,
                intent=intent,
                used_skills=used_skills,
                evidence_chunk_ids=list(all_evidence.keys()),
            )
        )
        db.commit()
        return {
            'intent': intent,
            'used_skills': used_skills,
            'answer': final_answer,
            'summary_updated': flags['summary_updated'],
            'action_items_updated': flags['action_items_updated'],
            'decisions_updated': flags['decisions_updated'],
            'evidence': list(all_evidence.values()),
        }
