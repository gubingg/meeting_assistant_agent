from __future__ import annotations

import json

from pydantic import ValidationError

from app.agents.prompt_library import PROJECT_QA_SYSTEM_PROMPT, PROJECT_QA_USER_PROMPT_TEMPLATE
from app.core.exceptions import AgentSchemaValidationError
from app.schemas.agents.project_qa import ProjectQAOutput
from app.schemas.qa import CitationItem, ProjectQAResponse
from app.services.llm_service import OpenAICompatibleClient


class ProjectQAAgent:
    def __init__(self) -> None:
        self.llm = OpenAICompatibleClient()

    @staticmethod
    def _fill_template(template: str, mapping: dict[str, str]) -> str:
        value = template
        for key, replacement in mapping.items():
            value = value.replace('{{' + key + '}}', replacement)
        return value

    def _validate_output(self, payload: dict | list) -> ProjectQAOutput:
        try:
            return ProjectQAOutput.model_validate(payload)
        except ValidationError as exc:
            import logging
            logging.getLogger(__name__).exception('ProjectQAAgent schema validation failed: payload=%s', payload)
            raise AgentSchemaValidationError('project_qa_agent') from exc

    def _fallback_answer(self, question: str, current_tasks: list[dict], retrieved_meeting_chunks: list[dict], retrieved_current_doc_chunks: list[dict], retrieved_history_doc_chunks: list[dict]) -> str:
        if any(keyword in question for keyword in ['待办', '完成', '负责人']):
            if current_tasks:
                return '基于当前项目待办状态，相关信息如下：\n' + '\n'.join(f'- {item["title"]} | 负责人：{item.get("owner") or "未分配"} | 状态：{item.get("status_label") or item.get("status")}' for item in current_tasks[:5])
            return '当前没有检索到匹配的待办信息。'
        if any(keyword in question for keyword in ['风险', '阻塞']):
            if retrieved_meeting_chunks:
                return '基于会议记录，当前相关风险如下：\n' + '\n'.join(f'- {item["snippet"]}' for item in retrieved_meeting_chunks[:5])
            return '当前没有检索到明确的风险记录。'
        chunks = retrieved_current_doc_chunks[:3] + retrieved_history_doc_chunks[:2]
        if chunks:
            return '基于当前项目资料，相关内容如下：\n' + '\n'.join(f'- {item["snippet"]}' for item in chunks)
        return '当前项目还没有足够的会议、待办或资料信息可供回答。'

    def answer(self, project_name: str, question: str, current_tasks: list[dict], retrieved_meeting_chunks: list[dict], retrieved_current_doc_chunks: list[dict], retrieved_history_doc_chunks: list[dict], doc_update_tasks: list[dict], chat_history: list[dict], citation_pool: list[CitationItem]) -> ProjectQAResponse:
        fallback = self._fallback_answer(question, current_tasks, retrieved_meeting_chunks, retrieved_current_doc_chunks, retrieved_history_doc_chunks)
        user_prompt = self._fill_template(PROJECT_QA_USER_PROMPT_TEMPLATE, {'project_name': project_name, 'question': question, 'current_tasks_json': json.dumps(current_tasks, ensure_ascii=False, indent=2), 'retrieved_meeting_chunks_json': json.dumps(retrieved_meeting_chunks, ensure_ascii=False, indent=2), 'retrieved_current_doc_chunks_json': json.dumps(retrieved_current_doc_chunks, ensure_ascii=False, indent=2), 'retrieved_history_doc_chunks_json': json.dumps(retrieved_history_doc_chunks, ensure_ascii=False, indent=2), 'doc_update_tasks_json': json.dumps(doc_update_tasks, ensure_ascii=False, indent=2), 'chat_history_json': json.dumps(chat_history, ensure_ascii=False, indent=2)})
        payload = self.llm.chat_json_payload(PROJECT_QA_SYSTEM_PROMPT, user_prompt, ProjectQAOutput)
        if payload is None:
            return ProjectQAResponse(answer=fallback, citations=citation_pool[:6])
        result = self._validate_output(payload)
        citation_by_key = {(item.source_type, str(item.source_id), item.label): item for item in citation_pool}
        citation_by_label = {item.label: item for item in citation_pool}
        selected: list[CitationItem] = []
        for item in result.citations:
            matched = citation_by_key.get((item.source_type, item.source_id, item.label)) or citation_by_label.get(item.label)
            if matched and matched not in selected:
                selected.append(matched)
        if not selected:
            selected = citation_pool[:6]
        answer = result.answer.strip() if result.answer.strip() else fallback
        return ProjectQAResponse(answer=answer, citations=selected[:6])
