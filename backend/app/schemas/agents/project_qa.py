from typing import Literal

from pydantic import Field

from app.schemas.agents import StrictBaseModel

QAAnswerType = Literal['current_status', 'history_trace', 'doc_query', 'task_query', 'risk_query', 'mixed_query', 'insufficient_evidence']
QAConfidence = Literal['high', 'medium', 'low']
QASourceType = Literal['meeting', 'task', 'project_doc_current', 'project_doc_history', 'doc_update_task', 'chat_history']


class QACitation(StrictBaseModel):
    source_type: QASourceType
    source_id: str = ''
    label: str


class ProjectQAOutput(StrictBaseModel):
    answer_type: QAAnswerType
    answer: str
    confidence: QAConfidence
    citations: list[QACitation] = Field(default_factory=list)
    insufficient_info: list[str] = Field(default_factory=list)
