from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from app.agents.prompt_library import MEETING_PLANNER_SYSTEM_PROMPT, MEETING_PLANNER_USER_PROMPT_TEMPLATE
from app.constants.doc_types import get_doc_type_label
from app.core.exceptions import AgentSchemaValidationError
from app.schemas.agents.planner import PlannerOutput
from app.services.llm_service import OpenAICompatibleClient
from app.services.transcript_parser import ParsedTranscript

logger = logging.getLogger(__name__)


class PlannerAgent:
    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    @staticmethod
    def _fill_template(template: str, mapping: dict[str, str]) -> str:
        value = template
        for key, replacement in mapping.items():
            value = value.replace('{{' + key + '}}', replacement)
        return value

    def _validate_output(self, payload: dict | list) -> PlannerOutput:
        try:
            return PlannerOutput.model_validate(payload)
        except ValidationError as exc:
            logger.exception('PlannerAgent schema validation failed: payload=%s', payload)
            raise AgentSchemaValidationError('planner_agent') from exc

    @staticmethod
    def _guidance(priority: str, focus_points: list[str], instructions: str) -> dict:
        return {
            'priority': priority,
            'focus_points': focus_points,
            'instructions': instructions,
        }

    def _fallback_strategy(self, parsed: ParsedTranscript) -> dict:
        meeting_text = '\n'.join(item.text for item in parsed.utterances[:24])
        lowered = meeting_text.lower()

        if any(keyword in lowered for keyword in ['故障', '影响范围', '止血', '回滚', '恢复', '排查']):
            meeting_nature = {
                'primary_label': '故障响应与恢复会',
                'secondary_label': '任务推进同步',
                'normalized_category': 'incident_response',
            }
            meeting_goal = '确认故障影响、修复推进和恢复条件，尽快稳定系统状态并安排后续处理。'
            primary_agent = 'meeting_analyst'
            secondary_agent = 'task_continuity'
            focus_priority = ['incident_impact', 'incident_root_cause', 'incident_recovery', 'blockers_risks']
            risk_flags = ['possible_incident_impact', 'possible_recovery_risk']
        elif any(keyword in lowered for keyword in ['复盘', '根因', '教训', '预防', '机制', '监控补强']):
            meeting_nature = {
                'primary_label': '事故复盘改进会',
                'secondary_label': '资料补充规划',
                'normalized_category': 'postmortem_retro',
            }
            meeting_goal = '沉淀事故根因、改进措施和机制补强项，推动复盘结论落到文档和后续行动。'
            primary_agent = 'meeting_analyst'
            secondary_agent = 'project_doc_update'
            focus_priority = ['key_conclusions', 'retro_actions', 'doc_changes']
            risk_flags = ['possible_doc_impact']
        elif any(keyword in lowered for keyword in ['验收', '通过', '不通过', '上线条件', '遗留问题']):
            meeting_nature = {
                'primary_label': '验收结论确认会',
                'secondary_label': '资料口径同步',
                'normalized_category': 'review_acceptance',
            }
            meeting_goal = '确认当前结果是否通过验收、还有哪些遗留问题，以及是否满足上线或交付条件。'
            primary_agent = 'meeting_analyst'
            secondary_agent = 'project_doc_update'
            focus_priority = ['acceptance_results', 'leftover_issues', 'launch_conditions']
            risk_flags = ['unclear_acceptance'] if '待确认' in meeting_text else ['none']
        elif any(keyword in lowered for keyword in ['负责人', '截止', '延期', '阻塞', '依赖', '推进', '完成了吗']):
            meeting_nature = {
                'primary_label': '执行推进同步会',
                'secondary_label': '风险阻塞梳理',
                'normalized_category': 'execution_sync',
            }
            meeting_goal = '同步当前任务推进情况、负责人和时间节点，识别阻塞风险并明确下一步动作。'
            primary_agent = 'task_continuity'
            secondary_agent = 'meeting_analyst'
            focus_priority = ['task_continuity', 'status_changes', 'blockers_risks']
            risk_flags = ['possible_blockers'] if any(keyword in lowered for keyword in ['阻塞', '延期', '依赖']) else ['none']
        else:
            meeting_nature = {
                'primary_label': '需求范围对齐会',
                'secondary_label': '资料变更评估',
                'normalized_category': 'alignment_decision',
            }
            meeting_goal = '对齐本次会议要解决的目标、范围和关键口径，明确真正达成的结论与后续边界。'
            primary_agent = 'meeting_analyst'
            secondary_agent = 'project_doc_update'
            focus_priority = ['goal_scope', 'key_conclusions', 'doc_changes']
            risk_flags = ['unclear_scope'] if len(parsed.utterances) <= 2 else ['none']

        agent_guidance = {
            'meeting_analyst': self._guidance(
                'high' if primary_agent == 'meeting_analyst' else 'medium',
                ['核心会议目标', '明确结论', '边界或口径变化'] if 'goal_scope' in focus_priority else ['关键结果', '风险阻塞', '验收或恢复判断'],
                '优先抽取会议真正达成的结论、边界和对后续处理最有价值的信息。',
            ),
            'task_continuity': self._guidance(
                'high' if primary_agent == 'task_continuity' else ('medium' if secondary_agent == 'task_continuity' else 'low'),
                ['当前行动项', '历史任务延续', '状态变化与负责人变化'],
                '仅对明确可执行动作做连续性判断，不要把纯结论性描述强行映射为任务。',
            ),
            'project_doc_update': self._guidance(
                'high' if primary_agent == 'project_doc_update' else ('medium' if secondary_agent == 'project_doc_update' else 'low'),
                ['资料是否受影响', '是否需要补充说明文档', '是否需要资料更新待办'],
                '重点判断会议结论是否触发资料补充、版本更新或资料更新待办。',
            ),
        }
        return {
            'meeting_nature': meeting_nature,
            'meeting_goal': meeting_goal,
            'confidence': 'medium' if len(parsed.utterances) >= 3 else 'low',
            'reason': '根据会议正文中的关键词、讨论重点和发言密度做本地兜底判断，并按当前最强信号确定处理策略。',
            'primary_agent': primary_agent,
            'secondary_agent': secondary_agent,
            'focus_priority': focus_priority,
            'agent_guidance': agent_guidance,
            'risk_flags': risk_flags,
        }

    def plan_meeting_upload(self, project_name: str, project_desc: str, project_docs: list, parsed: ParsedTranscript, source_file_name: str, source_type: str = 'meeting_json') -> dict:
        meeting_text = '\n'.join(f'[{item.speaker}] {item.text}' for item in parsed.utterances)
        project_doc_types_payload = [
            {
                'doc_id': doc.id,
                'doc_type': doc.doc_type,
                'doc_type_label': get_doc_type_label(doc.doc_type),
                'title': doc.title or doc.doc_name,
            }
            for doc in project_docs
        ]
        user_prompt = self._fill_template(
            MEETING_PLANNER_USER_PROMPT_TEMPLATE,
            {
                'project_name': project_name,
                'project_desc': project_desc or '',
                'meeting_title': parsed.title,
                'meeting_time': parsed.meeting_date.isoformat(sep=' ') if parsed.meeting_date else '',
                'participants': json.dumps(parsed.participants, ensure_ascii=False),
                'source_file_name': source_file_name,
                'source_type': source_type,
                'project_doc_types_json': json.dumps(project_doc_types_payload, ensure_ascii=False, indent=2),
                'meeting_text': meeting_text,
            },
        )
        payload = self.llm.chat_json_payload(MEETING_PLANNER_SYSTEM_PROMPT, user_prompt, PlannerOutput)
        if payload is None:
            logger.info('PlannerAgent fallback for meeting upload: title=%s', parsed.title)
            return self._fallback_strategy(parsed)
        result = self._validate_output(payload)
        logger.info(
            'PlannerAgent LLM strategy completed: title=%s category=%s primary_agent=%s',
            parsed.title,
            result.meeting_nature.normalized_category,
            result.primary_agent,
        )
        return result.model_dump()
