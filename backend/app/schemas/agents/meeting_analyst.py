from typing import Literal

from pydantic import Field

from app.schemas.agents import StrictBaseModel

MeetingActionStatus = Literal['未开始', '进行中', '已完成', '阻塞']
MeetingRiskSeverity = Literal['low', 'medium', 'high']
AcceptanceResult = Literal['pass', 'conditional_pass', 'fail', 'not_applicable']


class MeetingActionItem(StrictBaseModel):
    title: str
    description: str | None = None
    owner: str | None = None
    due_date: str | None = None
    status: MeetingActionStatus


class MeetingRiskBlocker(StrictBaseModel):
    title: str
    description: str
    severity: MeetingRiskSeverity


class MeetingAcceptanceReview(StrictBaseModel):
    result: AcceptanceResult
    leftover_issues: list[str] = Field(default_factory=list)
    launch_conditions: list[str] = Field(default_factory=list)


class MeetingRawRecordEntry(StrictBaseModel):
    file_name: str = ''
    source_type: str = ''
    source_ref: str = ''


class MeetingAnalystOutput(StrictBaseModel):
    summary: str
    key_conclusions: list[str] = Field(default_factory=list)
    action_items: list[MeetingActionItem] = Field(default_factory=list)
    risks_blockers: list[MeetingRiskBlocker] = Field(default_factory=list)
    acceptance_review: MeetingAcceptanceReview
    raw_record_entry: MeetingRawRecordEntry
