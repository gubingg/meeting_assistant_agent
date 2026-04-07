from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graphs.state import QAWorkflowState


class QAWorkflow:
    def __init__(self, qa_agent) -> None:
        self.qa_agent = qa_agent

    def project_qa_node(self, state: QAWorkflowState) -> QAWorkflowState:
        return {
            'response': self.qa_agent.answer(
                project_name=state['project_name'],
                question=state['question'],
                current_tasks=state.get('current_tasks', []),
                retrieved_meeting_chunks=state.get('retrieved_meeting_chunks', []),
                retrieved_current_doc_chunks=state.get('retrieved_current_doc_chunks', []),
                retrieved_history_doc_chunks=state.get('retrieved_history_doc_chunks', []),
                doc_update_tasks=state.get('doc_update_tasks', []),
                chat_history=state.get('chat_history', []),
                citation_pool=state.get('citation_pool', []),
            )
        }

    def build(self):
        graph = StateGraph(QAWorkflowState)
        graph.add_node('project_qa_node', self.project_qa_node)
        graph.add_edge(START, 'project_qa_node')
        graph.add_edge('project_qa_node', END)
        return graph.compile()
