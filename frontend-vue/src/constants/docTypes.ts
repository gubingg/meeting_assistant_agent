export const DOC_TYPE_OPTIONS = [
  { value: 'prd', label: 'PRD' },
  { value: 'field_definition', label: '字段定义' },
  { value: 'tech_spec', label: '技术方案' },
  { value: 'test_acceptance', label: '测试/验收' },
  { value: 'reference', label: '参考资料' },
  { value: 'other', label: '其他' },
] as const;

export const LEGACY_DOC_TYPE_MAP: Record<string, string> = {
  PRD: 'prd',
  prd: 'prd',
  方案文档: 'tech_spec',
  技术方案: 'tech_spec',
  合同: 'reference',
  补充备注: 'other',
  补充说明: 'other',
  参考资料: 'reference',
  字段定义: 'field_definition',
  '测试/验收': 'test_acceptance',
  测试计划: 'test_acceptance',
  其他: 'other',
};

export type ProjectDocType = (typeof DOC_TYPE_OPTIONS)[number]['value'];
export type ProjectDocTypeFilter = ProjectDocType | 'all';

const DOC_TYPE_LABELS = DOC_TYPE_OPTIONS.reduce<Record<ProjectDocType, string>>((result, option) => {
  result[option.value] = option.label;
  return result;
}, {} as Record<ProjectDocType, string>);

export function normalizeDocType(raw: string | null | undefined): ProjectDocType {
  const value = raw?.trim();
  if (!value) return 'other';

  if (value in DOC_TYPE_LABELS) {
    return value as ProjectDocType;
  }

  const lowered = value.toLowerCase();
  if (lowered in DOC_TYPE_LABELS) {
    return lowered as ProjectDocType;
  }

  return (LEGACY_DOC_TYPE_MAP[value] as ProjectDocType | undefined) ?? 'other';
}

export function getDocTypeLabel(raw: string | null | undefined) {
  return DOC_TYPE_LABELS[normalizeDocType(raw)];
}
