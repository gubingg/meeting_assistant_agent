from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from app.agents.prompt_library import PROJECT_DOC_UPDATE_SYSTEM_PROMPT, PROJECT_DOC_UPDATE_USER_PROMPT_TEMPLATE
from app.constants.doc_types import get_doc_type_label
from app.core.exceptions import AgentSchemaValidationError
from app.models import ProjectDoc, Task
from app.schemas.agents.project_doc_update import ProjectDocUpdateOutput
from app.services.llm_service import OpenAICompatibleClient

logger = logging.getLogger(__name__)

_TYPE_KEYWORDS = {
    'prd': ['需求', '范围', 'prd', '产品'],
    'field_definition': ['字段', '口径', '定义', '面板'],
    'tech_spec': ['技术', '方案', '接口', '架构', 'runbook'],
    'test_acceptance': ['测试', '验收', '上线条件'],
    'test_plan': ['测试', '验收', '上线条件'],
    'reference': ['参考', '背景', '说明', '复盘'],
}
_DOC_TYPE_ALIASES = {
    'test_plan': 'test_acceptance',
    'test_acceptance': 'test_acceptance',
}


class ProjectDocUpdateAgent:
    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    @staticmethod
    def _fill_template(template: str, mapping: dict[str, str]) -> str:
        value = template
        for key, replacement in mapping.items():
            value = value.replace('{{' + key + '}}', replacement)
        return value

    def _validate_output(self, payload: dict | list) -> ProjectDocUpdateOutput:
        try:
            return ProjectDocUpdateOutput.model_validate(payload)
        except ValidationError as exc:
            logger.exception('ProjectDocUpdateAgent schema validation failed: payload=%s', payload)
            raise AgentSchemaValidationError('project_doc_update_agent') from exc

    @staticmethod
    def _normalize_agent_doc_type(doc_type: str) -> str:
        return _DOC_TYPE_ALIASES.get(doc_type, doc_type)

    def _fallback(self, analysis: dict, existing_docs: list[ProjectDoc]) -> list[dict]:
        corpus = ' '.join(
            [analysis.get('summary', '')]
            + [item.get('text', '') for item in analysis.get('decisions', [])]
            + [item.get('text', '') for item in analysis.get('risks', [])]
            + [item.get('title', '') for item in analysis.get('tasks', [])]
            + [item.get('description', '') for item in analysis.get('tasks', [])]
        ).lower()
        impacted_types = {
            self._normalize_agent_doc_type(doc_type)
            for doc_type, keywords in _TYPE_KEYWORDS.items()
            if any(keyword.lower() in corpus for keyword in keywords)
        }
        updates = []
        for doc in existing_docs:
            if doc.current_version and doc.doc_type in impacted_types:
                updates.append(
                    {
                        'doc': doc,
                        'change_summary': f'会议提到 {get_doc_type_label(doc.doc_type)} 相关变更：{analysis.get("summary", "")[:60]}',
                        'reason': '本地兜底根据摘要、结论、待办和风险中的关键词判断资料受影响。',
                        'suggested_task_title': None,
                    }
                )
        return updates

    def detect_updates(
        self,
        planner_strategy: dict,
        meeting_analysis: dict,
        existing_docs: list[ProjectDoc],
        existing_open_doc_update_tasks: list[Task] | None = None,
    ) -> list[dict]:
        if not existing_docs:
            return []
        existing_open_doc_update_tasks = existing_open_doc_update_tasks or []
        user_prompt = self._fill_template(
            PROJECT_DOC_UPDATE_USER_PROMPT_TEMPLATE,
            {
                'planner_strategy_json': json.dumps(planner_strategy, ensure_ascii=False, indent=2),
                'meeting_analysis_json': json.dumps(meeting_analysis.get('structured_output') or meeting_analysis, ensure_ascii=False, indent=2, default=str),
                'project_docs_json': json.dumps(
                    [
                        {
                            'id': doc.id,
                            'title': doc.title or doc.doc_name,
                            'doc_name': doc.doc_name,
                            'doc_type': doc.doc_type,
                            'doc_type_label': get_doc_type_label(doc.doc_type),
                            'current_version_label': doc.current_version.version_label if doc.current_version else None,
                        }
                        for doc in existing_docs
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
                'existing_open_doc_update_tasks_json': json.dumps(
                    [
                        {
                            'id': task.id,
                            'title': task.title,
                            'description': task.description,
                            'owner': task.owner,
                            'status': task.status,
                        }
                        for task in existing_open_doc_update_tasks
                    ],
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        )
        payload = self.llm.chat_json_payload(PROJECT_DOC_UPDATE_SYSTEM_PROMPT, user_prompt, ProjectDocUpdateOutput)
        if payload is None:
            logger.info('ProjectDocUpdateAgent fallback detect: docs=%s', len(existing_docs))
            return self._fallback(meeting_analysis, existing_docs)
        result = self._validate_output(payload)
        updates = []
        doc_map: dict[str, ProjectDoc] = {}
        for doc in existing_docs:
            if doc.current_version is None:
                continue
            doc_map[doc.doc_type] = doc
            normalized_alias = self._normalize_agent_doc_type(doc.doc_type)
            doc_map.setdefault(normalized_alias, doc)
        suggestions_by_type = {self._normalize_agent_doc_type(item.doc_type): item for item in result.doc_update_task_suggestions}
        for item in result.affected_docs:
            normalized_doc_type = self._normalize_agent_doc_type(item.doc_type)
            doc = doc_map.get(normalized_doc_type)
            if not doc or not item.should_create_new_version:
                continue
            suggestion = suggestions_by_type.get(normalized_doc_type)
            updates.append(
                {
                    'doc': doc,
                    'change_summary': item.change_summary,
                    'reason': item.change_summary,
                    'suggested_task_title': suggestion.suggested_title if suggestion and suggestion.task_action != 'no_task_needed' else None,
                }
            )
        logger.info('ProjectDocUpdateAgent LLM detect completed: affected_docs=%s updates=%s', len(result.affected_docs), len(updates))
        return updates
