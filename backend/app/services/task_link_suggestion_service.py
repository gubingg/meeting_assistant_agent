from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.doc_types import get_doc_type_label
from app.constants.task_statuses import ACTIVE_TASK_STATUSES
from app.models import Project, ProjectDoc, Task, TaskLinkSuggestion


logger = logging.getLogger(__name__)


class TaskLinkSuggestionService:
    DOC_TYPE_HINTS = {
        'prd': ['目标', '范围', '需求', '非目标'],
        'field_definition': ['字段', '口径', '结果面板', '定义'],
        'tech_spec': ['技术', '方案', '接口', '实现', '链路'],
        'test_acceptance': ['测试', '验收', '上线检查'],
        'reference': ['背景', '参考', '补充'],
    }
    DOCUMENT_TERMS = ('文档', '资料', 'PRD', '方案', '字段定义', '技术方案', '测试', '验收')
    GENERIC_TOKENS = {'v0', 'v1', 'v2', '文档', '资料', '终稿', '草案', '版本', '整理', '输出', '编写', '补齐'}

    def _normalize(self, text: str) -> str:
        return re.sub(r'[^一-鿿A-Za-z0-9]', '', text).lower()

    def _keyword_hits(self, text: str) -> set[str]:
        source = text.lower()
        hits: set[str] = set()
        for keywords in self.DOC_TYPE_HINTS.values():
            for keyword in keywords:
                if keyword.lower() in source:
                    hits.add(keyword)
        return hits

    def _document_phrases(self, doc: ProjectDoc) -> list[str]:
        raw = ' '.join(filter(None, [doc.title, doc.doc_name, get_doc_type_label(doc.doc_type)]))
        phrases: list[str] = []
        for part in re.split(r'[\s_\-()（）.]+', raw):
            value = part.strip()
            if not value:
                continue
            if value.lower() in self.GENERIC_TOKENS:
                continue
            if len(value) >= 2 and value not in phrases:
                phrases.append(value)
        return phrases[:8]

    def _document_delivery_boost(self, doc: ProjectDoc, task: Task) -> tuple[float, list[str]]:
        task_corpus_raw = ' '.join(filter(None, [task.title, task.description or '', task.source_meeting.title if task.source_meeting else '']))
        if not any(term.lower() in task_corpus_raw.lower() for term in self.DOCUMENT_TERMS):
            return 0.0, []

        normalized_task = self._normalize(task_corpus_raw)
        matched_phrases: list[str] = []
        core_title = re.sub(r'[_\-\s]*v\d+(?:\.\d+)?$', '', doc.title or '', flags=re.I).strip()
        normalized_core_title = self._normalize(core_title)
        if normalized_core_title and normalized_core_title in normalized_task:
            matched_phrases.append(core_title)

        for phrase in self._document_phrases(doc):
            normalized_phrase = self._normalize(phrase)
            if not normalized_phrase:
                continue
            if phrase.lower() in task_corpus_raw.lower() or normalized_phrase in normalized_task:
                matched_phrases.append(phrase)

        deduped_phrases: list[str] = []
        for phrase in matched_phrases:
            if phrase and phrase not in deduped_phrases:
                deduped_phrases.append(phrase)

        if not deduped_phrases:
            return 0.0, []

        boost = min(0.42, 0.18 + 0.08 * (len(deduped_phrases) - 1))
        return boost, deduped_phrases[:3]

    def _eligible_tasks(self, db: Session, project_id: int) -> list[Task]:
        active = list(db.scalars(select(Task).where(Task.project_id == project_id, Task.status.in_(tuple(ACTIVE_TASK_STATUSES)))).all())
        if active:
            return active
        return list(db.scalars(select(Task).where(Task.project_id == project_id)).all())

    def _build_reason(
        self,
        task: Task,
        title_score: float,
        overlap_score: float,
        doc_type_boost: float,
        delivery_boost: float,
        hits: set[str],
        matched_phrases: list[str],
    ) -> str:
        reasons: list[str] = []
        if title_score >= 0.55:
            reasons.append('资料标题与待办标题较接近')
        if overlap_score >= 0.2:
            reasons.append('资料正文与待办描述命中了相同关键词')
        if doc_type_boost > 0:
            reasons.append('资料类型与待办语义较匹配')
        if delivery_boost > 0 and matched_phrases:
            reasons.append(f"待办中提到了资料交付，且命中了：{'、'.join(matched_phrases)}")
        if hits and not reasons:
            reasons.append(f"命中了关键词：{'、'.join(sorted(hits)[:3])}")
        return '，'.join(reasons) or '资料内容与当前待办存在较高相似度'

    def _score_task(self, doc: ProjectDoc, task: Task) -> tuple[float, str]:
        title_text = self._normalize(doc.title)
        task_title = self._normalize(task.title)
        title_score = SequenceMatcher(None, title_text, task_title).ratio() if title_text and task_title else 0.0

        doc_corpus = ' '.join(filter(None, [doc.title, doc.content or '', doc.doc_type]))
        task_corpus = ' '.join(filter(None, [task.title, task.description or '', task.source_meeting.title if task.source_meeting else '']))
        doc_hits = self._keyword_hits(doc_corpus)
        task_hits = self._keyword_hits(task_corpus)
        overlap_score = len(doc_hits & task_hits) / max(len(doc_hits | task_hits), 1)

        type_keywords = self.DOC_TYPE_HINTS.get(doc.doc_type, [])
        doc_type_boost = 0.1 if any(keyword in task_corpus for keyword in type_keywords) else 0.0
        delivery_boost, matched_phrases = self._document_delivery_boost(doc, task)
        score = title_score * 0.46 + overlap_score * 0.18 + doc_type_boost + delivery_boost
        return score, self._build_reason(task, title_score, overlap_score, doc_type_boost, delivery_boost, doc_hits & task_hits, matched_phrases)

    def create_suggestions(self, db: Session, project: Project, doc: ProjectDoc) -> list[TaskLinkSuggestion]:
        existing_pending = db.scalars(select(TaskLinkSuggestion).where(TaskLinkSuggestion.doc_id == doc.id, TaskLinkSuggestion.status == 'pending')).all()
        for suggestion in existing_pending:
            db.delete(suggestion)

        candidates: list[tuple[float, Task, str]] = []
        for task in self._eligible_tasks(db, project.id):
            score, reason = self._score_task(doc, task)
            logger.info('Task link scoring: project_id=%s doc=%s task=%s score=%.4f reason=%s', project.id, doc.title, task.title, score, reason)
            if score >= 0.34:
                candidates.append((score, task, reason))

        candidates.sort(key=lambda item: item[0], reverse=True)
        logger.info('Task link suggestion candidates: project_id=%s doc=%s count=%s', project.id, doc.title, len(candidates))
        if not candidates:
            return []

        top_score, top_task, top_reason = candidates[0]
        suggestion = TaskLinkSuggestion(
            project_id=project.id,
            doc_id=doc.id,
            task_id=top_task.id,
            match_score=round(top_score, 4),
            match_reason=top_reason,
            suggested_status='pending_confirmation',
            status='pending',
        )
        db.add(suggestion)
        db.flush()
        return [suggestion]
