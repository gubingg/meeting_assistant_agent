from __future__ import annotations

DOC_PARSE_STATUS_LABELS = {
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
}

TASK_LINK_SUGGESTION_STATUS_LABELS = {
    'pending': '待确认',
    'confirmed': '已确认',
    'ignored': '已忽略',
}


def get_doc_parse_status_label(status: str | None) -> str:
    return DOC_PARSE_STATUS_LABELS.get((status or '').strip(), '处理中')



def get_task_link_suggestion_status_label(status: str | None) -> str:
    return TASK_LINK_SUGGESTION_STATUS_LABELS.get((status or '').strip(), '待确认')
