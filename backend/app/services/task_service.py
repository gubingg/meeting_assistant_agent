from __future__ import annotations

from app.constants.task_statuses import get_task_status_label
from app.models import Task
from app.schemas.task import TaskItemResponse, TaskSummaryResponse


class TaskService:
    def list_tasks(self, project_id: int, tasks: list[Task], status: str = 'all') -> list[TaskItemResponse]:
        items = [task for task in tasks if status == 'all' or task.status == status]
        return [
            TaskItemResponse(
                id=task.id,
                title=task.title,
                owner=task.owner,
                due_date=task.due_date,
                status=task.status,
                status_label=get_task_status_label(task.status),
                source_meeting_title=task.source_meeting.title if task.source_meeting else None,
                latest_update_meeting_title=task.latest_update_meeting.title if task.latest_update_meeting else None,
            )
            for task in sorted(items, key=lambda item: item.updated_at or item.created_at, reverse=True)
        ]

    def build_summary(self, tasks: list[Task]) -> TaskSummaryResponse:
        total = len(tasks)
        done_count = len([task for task in tasks if task.status == 'done'])
        delayed_count = len([task for task in tasks if task.status == 'delayed'])
        blocked_count = len([task for task in tasks if task.status == 'blocked'])
        unfinished_count = len([task for task in tasks if task.status not in {'done', 'cancelled'}])
        return TaskSummaryResponse(total=total, done_count=done_count, unfinished_count=unfinished_count, delayed_count=delayed_count, blocked_count=blocked_count)
