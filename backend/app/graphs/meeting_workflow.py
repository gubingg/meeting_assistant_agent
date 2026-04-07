from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graphs.state import MeetingWorkflowState


class MeetingWorkflow:
    def __init__(self, planner, analyst, continuity, doc_updater, persist_fn, chroma_ingest_fn) -> None:
        self.planner = planner
        self.analyst = analyst
        self.continuity = continuity
        self.doc_updater = doc_updater
        self.persist_fn = persist_fn
        self.chroma_ingest_fn = chroma_ingest_fn

    def planner_node(self, state: MeetingWorkflowState) -> MeetingWorkflowState:
        return {
            'planner_strategy': self.planner.plan_meeting_upload(
                project_name=state['project'].name,
                project_desc=state['project'].description,
                project_docs=state.get('project_docs', []),
                parsed=state['parsed'],
                source_file_name=state['meeting'].source_file_name or state['meeting'].title,
                source_type='meeting_json',
            )
        }

    def meeting_analyst_node(self, state: MeetingWorkflowState) -> MeetingWorkflowState:
        return {
            'analysis': self.analyst.analyze(
                project_name=state['project'].name,
                parsed=state['parsed'],
                planner_strategy=state['planner_strategy'],
                source_file_name=state['meeting'].source_file_name or state['meeting'].title,
                source_type='meeting_json',
            )
        }

    def task_continuity_node(self, state: MeetingWorkflowState) -> MeetingWorkflowState:
        return {
            'resolved_tasks': self.continuity.resolve(
                planner_strategy=state['planner_strategy'],
                meeting_title=state['meeting'].title,
                meeting_time=state['meeting'].meeting_time,
                current_action_items=state['analysis'].get('tasks', []),
                existing_tasks=state.get('project_tasks', []),
            )
        }

    def project_doc_update_node(self, state: MeetingWorkflowState) -> MeetingWorkflowState:
        project_tasks = state.get('project_tasks', [])
        existing_open_doc_update_tasks = [
            task for task in project_tasks
            if task.status in {'new', 'in_progress', 'pending_confirmation', 'blocked', 'delayed'} and any(keyword in (task.title + ' ' + (task.description or '')) for keyword in ['PRD', '文档', '资料', '方案', '测试', '字段'])
        ]
        return {
            'doc_updates': self.doc_updater.detect_updates(
                planner_strategy=state['planner_strategy'],
                meeting_analysis=state['analysis'],
                existing_docs=state.get('project_docs', []),
                existing_open_doc_update_tasks=existing_open_doc_update_tasks,
            )
        }

    def persist_results_node(self, state: MeetingWorkflowState) -> MeetingWorkflowState:
        return {'response': self.persist_fn(state)}

    def chroma_ingest_node(self, state: MeetingWorkflowState) -> MeetingWorkflowState:
        self.chroma_ingest_fn(state)
        return state

    def build(self):
        graph = StateGraph(MeetingWorkflowState)
        graph.add_node('planner_node', self.planner_node)
        graph.add_node('meeting_analyst_node', self.meeting_analyst_node)
        graph.add_node('task_continuity_node', self.task_continuity_node)
        graph.add_node('project_doc_update_node', self.project_doc_update_node)
        graph.add_node('persist_results_node', self.persist_results_node)
        graph.add_node('chroma_ingest_node', self.chroma_ingest_node)

        graph.add_edge(START, 'planner_node')
        graph.add_edge('planner_node', 'meeting_analyst_node')
        graph.add_edge('meeting_analyst_node', 'task_continuity_node')
        graph.add_edge('meeting_analyst_node', 'project_doc_update_node')
        graph.add_edge('task_continuity_node', 'persist_results_node')
        graph.add_edge('project_doc_update_node', 'persist_results_node')
        graph.add_edge('persist_results_node', 'chroma_ingest_node')
        graph.add_edge('chroma_ingest_node', END)
        return graph.compile()
