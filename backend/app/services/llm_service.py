from __future__ import annotations

import json
import logging
import re

import httpx
from openai import OpenAI
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
JSON_BLOCK_RE = re.compile(r'```(?:json)?\s*(\{.*\}|\[.*\])\s*```', re.DOTALL)


class OpenAICompatibleClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.llm_base_url or ''
        self.api_key = settings.llm_api_key or ''
        self.chat_model = settings.chat_model or ''
        self.embedding_model = settings.embedding_model or ''
        self.enabled = bool(self.base_url and self.api_key)
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key) if self.enabled else None

        self.rerank_base_url = self._resolve_rerank_base_url(settings.rerank_base_url or self.base_url)
        self.rerank_api_key = settings.rerank_api_key or self.api_key
        self.rerank_model = settings.rerank_model or ''
        self.rerank_enabled = bool(self.rerank_base_url and self.rerank_api_key and self.rerank_model)

        logger.info(
            'LLM client initialized: chat_enabled=%s chat_model=%s embedding_model=%s rerank_enabled=%s rerank_model=%s',
            self.enabled,
            self.chat_model or 'N/A',
            self.embedding_model or 'N/A',
            self.rerank_enabled,
            self.rerank_model or 'N/A',
        )

    @staticmethod
    def _resolve_rerank_base_url(base_url: str | None) -> str:
        if not base_url:
            return ''
        normalized = base_url.rstrip('/')
        if 'dashscope.aliyuncs.com/compatible-mode/' in normalized:
            normalized = normalized.replace('/compatible-mode/', '/compatible-api/')
        return normalized

    @staticmethod
    def _extract_json_payload(raw: str) -> dict | list | None:
        text = raw.strip()
        candidates = [text]
        block_match = JSON_BLOCK_RE.search(text)
        if block_match:
            candidates.append(block_match.group(1).strip())

        brace_start = text.find('{')
        brace_end = text.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            candidates.append(text[brace_start:brace_end + 1])

        bracket_start = text.find('[')
        bracket_end = text.rfind(']')
        if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
            candidates.append(text[bracket_start:bracket_end + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except Exception:
                continue
        return None

    def chat(self, system_prompt: str, user_prompt: str) -> str | None:
        if not self.enabled or self.client is None or not self.chat_model:
            logger.warning('LLM chat skipped: enabled=%s model=%s', self.enabled, self.chat_model or 'N/A')
            return None
        logger.info('LLM chat request: model=%s system_chars=%s user_chars=%s', self.chat_model, len(system_prompt), len(user_prompt))
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.2,
            )
        except Exception:
            logger.exception('LLM chat failed: model=%s', self.chat_model)
            return None
        content = response.choices[0].message.content or None
        logger.info('LLM chat success: model=%s response_chars=%s', self.chat_model, len(content or ''))
        return content

    def chat_json_payload(self, system_prompt: str, user_prompt: str, schema_model: type[BaseModel]) -> dict | list | None:
        schema_json = json.dumps(schema_model.model_json_schema(), ensure_ascii=False, indent=2)
        enhanced_system_prompt = '\n'.join(
            [
                system_prompt,
                '你必须只返回一个合法 JSON 对象，不要输出解释，不要输出 Markdown 代码块。',
                '返回 JSON 必须严格符合下面的 JSON Schema：',
                schema_json,
            ]
        )
        raw = self.chat(enhanced_system_prompt, user_prompt)
        if not raw:
            return None

        payload = self._extract_json_payload(raw)
        if payload is None:
            logger.warning('LLM JSON parse failed: model=%s raw=%s', self.chat_model, raw[:400])
            return None
        logger.info('LLM JSON payload extracted: model=%s schema=%s', self.chat_model, schema_model.__name__)
        return payload

    def embed_text(self, text: str, dimensions: int | None = None) -> list[float] | None:
        if not self.enabled or self.client is None or not self.embedding_model:
            logger.warning('LLM embedding skipped: enabled=%s model=%s', self.enabled, self.embedding_model or 'N/A')
            return None
        payload: dict[str, object] = {'model': self.embedding_model, 'input': text}
        if dimensions is not None:
            payload['dimensions'] = dimensions
        logger.info('LLM embedding request: model=%s text_chars=%s dimensions=%s', self.embedding_model, len(text), dimensions or 'default')
        try:
            response = self.client.embeddings.create(**payload)
        except Exception:
            logger.exception('LLM embedding failed: model=%s', self.embedding_model)
            return None
        if not response.data:
            logger.warning('LLM embedding returned empty data: model=%s', self.embedding_model)
            return None
        embedding = list(response.data[0].embedding)
        logger.info('LLM embedding success: model=%s dims=%s', self.embedding_model, len(embedding))
        return embedding

    def rerank(self, query: str, documents: list[str], top_n: int | None = None) -> list[dict[str, float | int]] | None:
        if not self.rerank_enabled or not documents:
            logger.warning('LLM rerank skipped: enabled=%s model=%s documents=%s', self.rerank_enabled, self.rerank_model or 'N/A', len(documents))
            return None

        payload: dict[str, object] = {'model': self.rerank_model, 'query': query, 'documents': documents}
        if top_n is not None:
            payload['top_n'] = top_n

        logger.info('LLM rerank request: model=%s query_chars=%s documents=%s top_n=%s', self.rerank_model, len(query), len(documents), top_n or 'default')
        try:
            response = httpx.post(
                f'{self.rerank_base_url}/reranks',
                json=payload,
                headers={'Authorization': f'Bearer {self.rerank_api_key}', 'Content-Type': 'application/json'},
                timeout=20.0,
            )
            response.raise_for_status()
            body = response.json()
        except Exception:
            logger.exception('LLM rerank failed: model=%s', self.rerank_model)
            return None

        raw_results = body.get('results') or body.get('output', {}).get('results') or []
        results: list[dict[str, float | int]] = []
        for item in raw_results:
            index = item.get('index')
            if index is None:
                continue
            score = item.get('relevance_score')
            if score is None:
                score = item.get('score')
            if score is None:
                score = 0.0
            results.append({'index': int(index), 'score': float(score)})
        logger.info('LLM rerank success: model=%s results=%s', self.rerank_model, len(results))
        return results or None
