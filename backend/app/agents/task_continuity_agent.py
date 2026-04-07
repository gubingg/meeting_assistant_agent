from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from difflib import SequenceMatcher

from dateutil import parser as date_parser
from pydantic import ValidationError

from app.agents.prompt_library import TASK_CONTINUITY_SYSTEM_PROMPT, TASK_CONTINUITY_USER_PROMPT_TEMPLATE
from app.constants.task_statuses import ACTIVE_TASK_STATUSES, normalize_task_status
from app.core.exceptions import AgentSchemaValidationError
from app.models import Task
from app.schemas.agents.task_continuity import TaskContinuityOutput
from app.services.llm_service import OpenAICompatibleClient

logger = logging.getLogger(__name__)


class TaskContinuityAgent:
    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', text).lower()

    @staticmethod
    def _safe_date(raw: str | None) -> datetime | None:
        if not raw:
            return None
        try:
            return date_parser.parse(raw)
        except Exception:
            return None

    def _validate_output(self, payload: dict | list) -> TaskContinuityOutput:
        try:
            return TaskContinuityOutput.model_validate(payload)
        except ValidationError as exc:
            logger.exception('TaskContinuityAgent schema validation failed: payload=%s', payload)
            raise AgentSchemaValidationError('task_continuity_agent') from exc

    def _candidate_pool(self, existing_tasks: list[Task]) -> list[Task]:
        active = [task for task in existing_tasks if task.status in ACTIVE_TASK_STATUSES]
        return active or list(existing_tasks)

    def _recall_candidates(self, title: str, existing_tasks: list[Task]) -> list[dict]:
        normalized = self._normalize(title)
        scored: list[tuple[float, Task]] = []
        for task in self._candidate_pool(existing_tasks):
            score = SequenceMatcher(None, normalized, self._normalize(task.title)).ratio()
            if score >= 0.35:
                scored.append((score, task))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [{'id': task.id, 'title': task.title, 'description': task.description, 'owner': task.owner, 'due_date': task.due_date.isoformat() if task.due_date else None, 'status': task.status, 'source_meeting': task.source_meeting.title if task.source_meeting else None, 'similarity_score': round(score, 3)} for score, task in scored[:5]]

    @staticmethod
    def _fill_template(template: str, mapping: dict[str, str]) -> str:
        value = template
        for key, replacement in mapping.items():
            value = value.replace('{{' + key + '}}', replacement)
        return value

    @staticmethod
    def _final_task_status(raw_status: str | None, matched_existing: bool) -> str:
        normalized = normalize_task_status(raw_status or ('in_progress' if not matched_existing else 'new'))
        if not matched_existing and normalized == 'new':
            return 'in_progress'
        return normalized

    def _fallback(self, current_action_items: list[dict], existing_tasks: list[Task]) -> list[dict]:
        decisions = []
        for item in current_action_items:
            candidates = self._recall_candidates(item['title'], existing_tasks)
            best = candidates[0] if candidates and candidates[0]['similarity_score'] >= 0.58 else None
            decisions.append({
                'task_id': best['id'] if best else None,
                'title': item['title'],
                'description': item.get('description') or item['title'],
                'owner': item.get('owner') or (best['owner'] if best else None),
                'due_date': item.get('due_date') or (self._safe_date(best['due_date']) if best and best.get('due_date') else None),
                'status': self._final_task_status(item.get('status') or (best['status'] if best else 'new'), matched_existing=bool(best)),
                'relation': 'same_task_update' if best else 'new_task',
                'reason': '?????????????????????',
            })
        return decisions

    def resolve(self, planner_strategy: dict, meeting_title: str, meeting_time: datetime | None, current_action_items: list[dict], existing_tasks: list[Task]) -> list[dict]:
        if not current_action_items:
            return []
        candidates_payload = []
        for item in current_action_items:
            candidates_payload.append({'title': item['title'], 'description': item.get('description'), 'owner': item.get('owner'), 'due_date': item.get('due_date').isoformat() if isinstance(item.get('due_date'), datetime) else None, 'status': item.get('status'), 'candidates': self._recall_candidates(item['title'], existing_tasks)})
        user_prompt = self._fill_template(TASK_CONTINUITY_USER_PROMPT_TEMPLATE, {'planner_strategy_json': json.dumps(planner_strategy, ensure_ascii=False, indent=2), 'meeting_title': meeting_title, 'meeting_time': meeting_time.isoformat(sep=' ') if meeting_time else '', 'current_action_items_json': json.dumps(candidates_payload, ensure_ascii=False, indent=2, default=str), 'historical_task_candidates_json': json.dumps([{'id': task.id, 'title': task.title, 'description': task.description, 'owner': task.owner, 'due_date': task.due_date.isoformat() if task.due_date else None, 'status': task.status} for task in existing_tasks], ensure_ascii=False, indent=2)})
        payload = self.llm.chat_json_payload(TASK_CONTINUITY_SYSTEM_PROMPT, user_prompt, TaskContinuityOutput)
        valid_task_ids = {task.id for task in existing_tasks}
        if payload is None:
            logger.info('TaskContinuityAgent fallback resolve: meeting=%s items=%s', meeting_title, len(current_action_items))
            return self._fallback(current_action_items, existing_tasks)
        result = self._validate_output(payload)
        resolved = []
        source_by_title = {item['title']: item for item in current_action_items}
        for decision in result.decisions:
            source = source_by_title.get(decision.current_item_title, {})
            matched_id = decision.matched_task_id if decision.matched_task_id in valid_task_ids else None
            matched_task = next((task for task in existing_tasks if task.id == matched_id), None)
            resolved.append({'task_id': matched_id, 'title': source.get('title') or decision.current_item_title, 'description': source.get('description') or decision.current_item_title, 'owner': decision.new_owner if decision.owner_changed else (source.get('owner') or (matched_task.owner if matched_task else None)), 'due_date': self._safe_date(decision.new_due_date) if decision.due_date_changed else (source.get('due_date') or (matched_task.due_date if matched_task else None)), 'status': self._final_task_status(decision.final_status, matched_existing=bool(matched_id)), 'relation': decision.match_type, 'reason': decision.reason})
        logger.info('TaskContinuityAgent LLM resolve completed: meeting=%s resolved=%s', meeting_title, len(resolved))
        return resolved
