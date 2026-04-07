from typing import Literal

from pydantic import Field

from app.schemas.agents import StrictBaseModel

DocType = Literal['prd', 'field_definition', 'tech_spec', 'test_plan', 'test_acceptance', 'reference', 'other']
DocImpactLevel = Literal['low', 'medium', 'high']
DocTaskAction = Literal['create_new', 'update_existing', 'no_task_needed']
DocTaskPriority = Literal['low', 'medium', 'high']


class AffectedDoc(StrictBaseModel):
    doc_type: DocType
    impact_level: DocImpactLevel
    should_create_new_version: bool
    should_update_current_version_pointer: bool
    change_summary: str


class DocUpdateTaskSuggestion(StrictBaseModel):
    doc_type: DocType
    task_action: DocTaskAction
    matched_existing_task_id: str | None = None
    suggested_title: str = ''
    suggested_description: str = ''
    priority: DocTaskPriority


class ProjectDocUpdateOutput(StrictBaseModel):
    has_doc_impact: bool
    affected_docs: list[AffectedDoc] = Field(default_factory=list)
    doc_update_task_suggestions: list[DocUpdateTaskSuggestion] = Field(default_factory=list)
