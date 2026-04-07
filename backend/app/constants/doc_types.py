from __future__ import annotations

from dataclasses import dataclass


DOC_TYPE_LABELS = {
    'prd': 'PRD',
    'field_definition': '字段定义',
    'tech_spec': '技术方案',
    'test_acceptance': '测试/验收',
    'reference': '参考资料',
    'other': '其他',
}

LEGACY_DOC_TYPE_MAP = {
    'PRD': 'prd',
    'prd': 'prd',
    '方案文档': 'tech_spec',
    '技术方案': 'tech_spec',
    '合同': 'reference',
    '补充备注': 'other',
    '补充说明': 'other',
    '参考资料': 'reference',
    '字段定义': 'field_definition',
    '测试/验收': 'test_acceptance',
    '测试计划': 'test_acceptance',
    '其他': 'other',
}

QUESTION_DOC_TYPE_HINTS = [
    ('prd', ['目标', '范围', '非目标', '为什么做', '背景', '需求']),
    ('field_definition', ['字段', '结果面板', '口径', '状态定义', '字段定义']),
    ('tech_spec', ['怎么实现', '输入格式', '检索链路', '状态更新规则', '技术方案', '接口', '实现']),
    ('test_acceptance', ['验收', '测试', '上线检查项', '验收标准', '测试条件']),
    ('reference', ['补充说明', '背景资料', '参考']),
]


@dataclass(frozen=True)
class DocTypeOption:
    value: str
    label: str


DOC_TYPE_OPTIONS = [DocTypeOption(value=value, label=label) for value, label in DOC_TYPE_LABELS.items()]
VALID_DOC_TYPES = set(DOC_TYPE_LABELS)


def normalize_doc_type(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    if value in VALID_DOC_TYPES:
        return value
    lowered = value.lower()
    if lowered in VALID_DOC_TYPES:
        return lowered
    return LEGACY_DOC_TYPE_MAP.get(value)


def require_doc_type(raw: str | None) -> str:
    normalized = normalize_doc_type(raw)
    if normalized is None:
        raise ValueError('资料类型不合法，请选择 PRD、字段定义、技术方案、测试/验收、参考资料或其他。')
    return normalized


def get_doc_type_label(doc_type: str | None) -> str:
    normalized = normalize_doc_type(doc_type)
    if normalized is None:
        return '其他'
    return DOC_TYPE_LABELS.get(normalized, '其他')


def infer_preferred_doc_types(question: str) -> list[str]:
    lowered = question.lower()
    matches: list[str] = []
    for doc_type, keywords in QUESTION_DOC_TYPE_HINTS:
        if any(keyword.lower() in lowered for keyword in keywords):
            matches.append(doc_type)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in matches:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered
