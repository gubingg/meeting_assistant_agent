from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from dateutil import parser as date_parser
from pydantic import ValidationError

from app.agents.prompt_library import MEETING_ANALYST_SYSTEM_PROMPT, MEETING_ANALYST_USER_PROMPT_TEMPLATE
from app.constants.task_statuses import normalize_task_status
from app.core.exceptions import AgentSchemaValidationError
from app.schemas.agents.meeting_analyst import MeetingAcceptanceReview, MeetingActionItem, MeetingAnalystOutput, MeetingRawRecordEntry, MeetingRiskBlocker
from app.services.llm_service import OpenAICompatibleClient
from app.services.transcript_parser import ParsedTranscript

logger = logging.getLogger(__name__)

_DECISION_KEYWORDS = ('决定', '确定', '通过', '暂定', '采用', '上线')
_TASK_KEYWORDS = ('负责', '跟进', '推进', '处理', '确认', '完成', '输出', '同步', '安排')
_RISK_KEYWORDS = ('风险', '阻塞', '延期', '问题', '待确认', '卡住', '依赖')
_OWNER_RE = re.compile(r'(?:负责人|由|请)([\u4e00-\u9fffA-Za-z0-9_-]{1,20})')
_DATE_RE = re.compile(r'(20\d{2}-\d{1,2}-\d{1,2})')


class MeetingAnalystAgent:
    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    @staticmethod
    def _fill_template(template: str, mapping: dict[str, str]) -> str:
        value = template
        for key, replacement in mapping.items():
            value = value.replace('{{' + key + '}}', replacement)
        return value

    def _validate_output(self, payload: dict | list) -> MeetingAnalystOutput:
        try:
            return MeetingAnalystOutput.model_validate(payload)
        except ValidationError as exc:
            logger.exception('MeetingAnalystAgent schema validation failed: payload=%s', payload)
            raise AgentSchemaValidationError('meeting_analyst_agent') from exc

    @staticmethod
    def _safe_date(raw: str | None) -> datetime | None:
        if not raw:
            return None
        try:
            return date_parser.parse(raw)
        except Exception:
            match = _DATE_RE.search(raw)
            if not match:
                return None
            try:
                return date_parser.parse(match.group(1))
            except Exception:
                return None

    @staticmethod
    def _normalize_status(raw: str) -> str:
        status_map = {'未开始': 'new', '进行中': 'in_progress', '已完成': 'done', '阻塞': 'blocked'}
        return normalize_task_status(status_map.get(raw, 'new'))

    @staticmethod
    def _extract_owner(speaker: str, text: str) -> str | None:
        if '我来' in text or '我负责' in text:
            return speaker
        match = _OWNER_RE.search(text)
        if match:
            return match.group(1)
        return None

    def _fallback(self, parsed: ParsedTranscript, source_file_name: str, source_type: str, source_ref: str) -> MeetingAnalystOutput:
        lines = [(item.speaker or '未知', item.text.strip()) for item in parsed.utterances if item.text.strip()]
        summary = '；'.join(text for _, text in lines[:3]) if lines else '本次会议已上传，待进一步生成结构化摘要。'
        key_conclusions = [text[:60] for _, text in lines if any(keyword in text for keyword in _DECISION_KEYWORDS)][:6]
        action_items = []
        for speaker, text in lines:
            if any(keyword in text for keyword in _TASK_KEYWORDS):
                date_match = _DATE_RE.search(text)
                action_items.append(MeetingActionItem(title=text[:60], description=text, owner=self._extract_owner(speaker, text), due_date=date_match.group(1) if date_match else None, status='进行中' if '进行中' in text else '未开始'))
        risks_blockers = []
        for _, text in lines:
            if any(keyword in text for keyword in _RISK_KEYWORDS):
                risks_blockers.append(MeetingRiskBlocker(title=text[:24], description=text, severity='high' if '延期' in text or '阻塞' in text else 'medium'))
        if not key_conclusions and lines:
            key_conclusions = [lines[0][1][:60]]
        return MeetingAnalystOutput(
            summary=summary,
            key_conclusions=key_conclusions,
            action_items=action_items,
            risks_blockers=risks_blockers,
            acceptance_review=MeetingAcceptanceReview(result='not_applicable', leftover_issues=[], launch_conditions=[]),
            raw_record_entry=MeetingRawRecordEntry(file_name=source_file_name, source_type=source_type, source_ref=source_ref),
        )

    def analyze(self, project_name: str, parsed: ParsedTranscript, planner_strategy: dict, source_file_name: str, source_type: str = 'meeting_json') -> dict:
        source_ref = source_file_name
        meeting_text = '\n'.join(f'[{item.speaker}] {item.text}' for item in parsed.utterances)
        user_prompt = self._fill_template(
            MEETING_ANALYST_USER_PROMPT_TEMPLATE,
            {
                'planner_strategy_json': json.dumps(planner_strategy, ensure_ascii=False, indent=2),
                'project_name': project_name,
                'meeting_title': parsed.title,
                'meeting_time': parsed.meeting_date.isoformat(sep=' ') if parsed.meeting_date else '',
                'participants': json.dumps(parsed.participants, ensure_ascii=False),
                'source_file_name': source_file_name,
                'source_type': source_type,
                'source_ref': source_ref,
                'meeting_text': meeting_text,
            },
        )
        payload = self.llm.chat_json_payload(MEETING_ANALYST_SYSTEM_PROMPT, user_prompt, MeetingAnalystOutput)
        if payload is None:
            logger.info('MeetingAnalystAgent fallback analysis: title=%s', parsed.title)
            result = self._fallback(parsed, source_file_name, source_type, source_ref)
        else:
            result = self._validate_output(payload)
        raw = result.model_dump()
        normalized = {
            'summary': result.summary,
            'decisions': [{'text': item} for item in result.key_conclusions],
            'tasks': [
                {
                    'title': item.title,
                    'description': item.description or item.title,
                    'owner': item.owner,
                    'due_date': self._safe_date(item.due_date),
                    'status': self._normalize_status(item.status),
                }
                for item in result.action_items
            ],
            'risks': [{'text': f'{item.title}：{item.description}' if item.title else item.description} for item in result.risks_blockers],
            'acceptance_review': raw['acceptance_review'],
            'raw_record_entry': raw['raw_record_entry'],
            'structured_output': raw,
        }
        logger.info('MeetingAnalystAgent LLM analysis completed: title=%s decisions=%s tasks=%s risks=%s', parsed.title, len(normalized['decisions']), len(normalized['tasks']), len(normalized['risks']))
        return normalized
