from typing import Literal

from pydantic import Field

from app.schemas.agents import StrictBaseModel

TaskMatchType = Literal['new_task', 'same_task_update']
TaskDecisionConfidence = Literal['high', 'medium', 'low']
TaskFinalStatus = Literal['new', 'in_progress', 'done', 'blocked', 'delayed', 'cancelled']


class TaskContinuityDecision(StrictBaseModel):
    current_item_title: str
    matched_task_id: int | None = None
    match_type: TaskMatchType
    confidence: TaskDecisionConfidence
    final_status: TaskFinalStatus
    owner_changed: bool
    new_owner: str | None = None
    due_date_changed: bool
    new_due_date: str | None = None
    reason: str


class TaskContinuityOutput(StrictBaseModel):
    decisions: list[TaskContinuityDecision] = Field(default_factory=list)
