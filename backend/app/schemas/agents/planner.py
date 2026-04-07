from typing import Literal

from pydantic import Field

from app.schemas.agents import StrictBaseModel

PlannerNormalizedCategory = Literal['alignment_decision', 'execution_sync', 'review_acceptance', 'incident_response', 'postmortem_retro', 'mixed', 'other']
PlannerConfidence = Literal['high', 'medium', 'low']
PlannerAgentName = Literal['meeting_analyst', 'task_continuity', 'project_doc_update']
PlannerFocusDimension = Literal['goal_scope', 'key_conclusions', 'task_continuity', 'status_changes', 'blockers_risks', 'acceptance_results', 'leftover_issues', 'launch_conditions', 'incident_impact', 'incident_root_cause', 'incident_recovery', 'retro_actions', 'doc_changes']
PlannerPriority = Literal['high', 'medium', 'low']
PlannerRiskFlag = Literal['insufficient_context', 'mixed_signals', 'unclear_ownership', 'unclear_scope', 'unclear_acceptance', 'possible_doc_impact', 'possible_blockers', 'possible_incident_impact', 'possible_recovery_risk', 'none']


class PlannerMeetingNature(StrictBaseModel):
    primary_label: str = Field(min_length=2, max_length=30)
    secondary_label: str | None = Field(default=None, max_length=30)
    normalized_category: PlannerNormalizedCategory


class PlannerAgentGuidanceItem(StrictBaseModel):
    priority: PlannerPriority
    focus_points: list[str] = Field(default_factory=list)
    instructions: str = Field(min_length=1, max_length=120)


class PlannerAgentGuidance(StrictBaseModel):
    meeting_analyst: PlannerAgentGuidanceItem
    task_continuity: PlannerAgentGuidanceItem
    project_doc_update: PlannerAgentGuidanceItem


class PlannerOutput(StrictBaseModel):
    meeting_nature: PlannerMeetingNature
    meeting_goal: str = Field(min_length=1, max_length=200)
    confidence: PlannerConfidence
    reason: str = Field(min_length=1, max_length=200)
    primary_agent: PlannerAgentName
    secondary_agent: PlannerAgentName | None = None
    focus_priority: list[PlannerFocusDimension] = Field(default_factory=list)
    agent_guidance: PlannerAgentGuidance
    risk_flags: list[PlannerRiskFlag] = Field(default_factory=list)
