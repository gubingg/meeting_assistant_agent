from __future__ import annotations

TASK_STATUS_LABELS = {
    'new': '待开始',
    'in_progress': '进行中',
    'pending_confirmation': '待确认',
    'done': '已完成',
    'delayed': '已延期',
    'blocked': '已阻塞',
    'cancelled': '已取消',
}

TASK_STATUS_INPUT_MAP = {
    '待开始': 'new',
    '进行中': 'in_progress',
    '待确认': 'pending_confirmation',
    '已完成': 'done',
    '已延期': 'delayed',
    '已阻塞': 'blocked',
    '已取消': 'cancelled',
    'new': 'new',
    'in_progress': 'in_progress',
    'pending_confirmation': 'pending_confirmation',
    'done': 'done',
    'delayed': 'delayed',
    'blocked': 'blocked',
    'cancelled': 'cancelled',
}

ACTIVE_TASK_STATUSES = {'new', 'in_progress', 'pending_confirmation', 'delayed', 'blocked'}


def normalize_task_status(raw: str | None) -> str:
    value = (raw or '').strip()
    normalized = TASK_STATUS_INPUT_MAP.get(value)
    if normalized is None:
        raise ValueError('待办状态不合法，请选择待开始、进行中、待确认、已完成、已延期、已阻塞或已取消。')
    return normalized



def get_task_status_label(status: str | None) -> str:
    normalized = TASK_STATUS_INPUT_MAP.get((status or '').strip(), status or 'new')
    return TASK_STATUS_LABELS.get(normalized, '待开始')
