from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.models import Meeting
from app.schemas.chat import ChatResponse


class WorkflowState(TypedDict, total=False):
    db: Session
    meeting_id: int
    message: str
    meeting: Meeting
    intent: str
    sub_intents: list[str]
    loaded_skills: dict[str, str]
    context: dict[str, list]
    output: dict[str, Any]
    response: ChatResponse


class MeetingAgentWorkflow:
    def __init__(self, agent_service) -> None:
        self.agent_service = agent_service

    def classify_intent_node(self, state: WorkflowState) -> WorkflowState:
        intent, sub_intents = self.agent_service.classify_intent(state['message'])
        meeting = state['db'].get(Meeting, state['meeting_id'])
        return {'intent': intent, 'sub_intents': sub_intents, 'meeting': meeting}

    def load_skill_node(self, state: WorkflowState) -> WorkflowState:
        return {'loaded_skills': self.agent_service.load_skills(state['sub_intents'])}

    def retrieve_context_node(self, state: WorkflowState) -> WorkflowState:
        return {'context': self.agent_service.retrieve_context(state['message'], state['meeting_id'], state['sub_intents'])}

    def execute_skill_node(self, state: WorkflowState) -> WorkflowState:
        output = self.agent_service.run_execution(
            db=state['db'],
            meeting=state['meeting'],
            message=state['message'],
            intent=state['intent'],
            sub_intents=state['sub_intents'],
            context=state['context'],
        )
        return {'output': output}

    def persist_result_node(self, state: WorkflowState) -> WorkflowState:
        return state

    def build_response_node(self, state: WorkflowState) -> WorkflowState:
        return {'response': ChatResponse(**state['output'])}

    def build(self):
        graph = StateGraph(WorkflowState)
        graph.add_node('classify_intent_node', self.classify_intent_node)
        graph.add_node('load_skill_node', self.load_skill_node)
        graph.add_node('retrieve_context_node', self.retrieve_context_node)
        graph.add_node('execute_skill_node', self.execute_skill_node)
        graph.add_node('persist_result_node', self.persist_result_node)
        graph.add_node('build_response_node', self.build_response_node)
        graph.add_edge(START, 'classify_intent_node')
        graph.add_edge('classify_intent_node', 'load_skill_node')
        graph.add_edge('load_skill_node', 'retrieve_context_node')
        graph.add_edge('retrieve_context_node', 'execute_skill_node')
        graph.add_edge('execute_skill_node', 'persist_result_node')
        graph.add_edge('persist_result_node', 'build_response_node')
        graph.add_edge('build_response_node', END)
        return graph.compile()

