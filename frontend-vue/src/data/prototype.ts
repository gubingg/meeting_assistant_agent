import { getDocTypeLabel, normalizeDocType, type ProjectDocType } from '@/constants/docTypes';

export type TodoStatus = 'todo' | 'doing' | 'pending_confirmation' | 'done';
export type ProjectStatus = 'active' | 'archived';
export type MaterialParseStatus = 'processing' | 'completed' | 'failed';
export type MaterialSuggestionStatus = 'pending' | 'confirmed' | 'ignored';
export type MaterialSuggestedTaskStatus = 'pending_confirmation' | 'done';

export type MeetingActionItem = {
  id: string;
  task: string;
  owner: string;
  dueDate: string;
  status: TodoStatus;
  blocked?: boolean;
  lastUpdatedMeetingTitle?: string;
};

export type MeetingRecord = {
  id: string;
  title: string;
  startedAt: string;
  participants: string[];
  summary: string;
  decisions: string[];
  blockers: string[];
  actionItems: MeetingActionItem[];
  rawFileName: string;
};

export type ProjectMaterialTaskLinkSuggestion = {
  id: string;
  taskId: string;
  taskTitle: string;
  owner: string;
  currentStatus: TodoStatus;
  sourceMeetingTitle?: string;
  suggestedStatus: MaterialSuggestedTaskStatus;
  status: MaterialSuggestionStatus;
  matchReason?: string;
};

export type ProjectMaterial = {
  id: string;
  title: string;
  docType: string;
  updatedAt: string;
  parseStatus: MaterialParseStatus;
  qaEnabled: boolean;
  taskLinkSuggestions: ProjectMaterialTaskLinkSuggestion[];
};

export type QaMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
};

export type ProjectTodoSummary = {
  total: number;
  todo: number;
  doing: number;
  pending_confirmation: number;
  done: number;
};

export type ProjectTodoItem = MeetingActionItem & {
  meetingTitle: string;
  meetingId: string;
  lastUpdatedMeetingTitle: string;
  isBlocked: boolean;
  isOverdue: boolean;
};

export type ProjectMetrics = {
  meetingCount: number;
  todoCount: number;
  unfinishedTodoCount: number;
  completedTodoCount: number;
  overdueTodoCount: number;
  blockedTodoCount: number;
  decisionCount: number;
  riskCount: number;
  materialCount: number;
  lastUpdatedAt: string;
};

export type ProjectRecord = {
  id: string;
  backendId: number;
  name: string;
  summary: string;
  owner: string;
  stage: string;
  status: ProjectStatus;
  startTime: string;
  latestMeetingAt: string;
  updatedAt: string;
  archivedAt: string | null;
  finalSummary: string;
  meetings: MeetingRecord[];
  materials: ProjectMaterial[];
  qaMessages: QaMessage[];
  todos: ProjectTodoItem[];
};

const TODAY = '2026-04-05';

export function getTodoSummary(project: ProjectRecord): ProjectTodoSummary {
  return getProjectTodos(project).reduce(
    (summary, item) => {
      summary.total += 1;
      summary[item.status] += 1;
      return summary;
    },
    { total: 0, todo: 0, doing: 0, pending_confirmation: 0, done: 0 } as ProjectTodoSummary,
  );
}

export function getProjectTodos(project: ProjectRecord): ProjectTodoItem[] {
  if (project.todos?.length) {
    return project.todos;
  }

  return project.meetings.flatMap((meeting) =>
    meeting.actionItems.map((item) => ({
      ...item,
      meetingTitle: meeting.title,
      meetingId: meeting.id,
      lastUpdatedMeetingTitle: item.lastUpdatedMeetingTitle ?? meeting.title,
      isBlocked: Boolean(item.blocked),
      isOverdue: item.status !== 'done' && item.dueDate < TODAY,
    })),
  );
}

export function getProjectMetrics(project: ProjectRecord): ProjectMetrics {
  const todos = getProjectTodos(project);
  const risks = project.meetings.flatMap((meeting) => meeting.blockers.filter((blocker) => blocker !== '无'));

  return {
    meetingCount: project.meetings.length,
    todoCount: todos.length,
    unfinishedTodoCount: todos.filter((item) => item.status !== 'done').length,
    completedTodoCount: todos.filter((item) => item.status === 'done').length,
    overdueTodoCount: todos.filter((item) => item.isOverdue).length,
    blockedTodoCount: todos.filter((item) => item.isBlocked).length,
    decisionCount: project.meetings.reduce((count, meeting) => count + meeting.decisions.length, 0),
    riskCount: risks.length,
    materialCount: project.materials.length,
    lastUpdatedAt: project.updatedAt || project.latestMeetingAt,
  };
}

export function getProjectDecisionTimeline(project: ProjectRecord) {
  return [...project.meetings]
    .sort((a, b) => a.startedAt.localeCompare(b.startedAt))
    .flatMap((meeting) => meeting.decisions.map((decision) => ({
      id: `${meeting.id}-${decision}`,
      meetingId: meeting.id,
      meetingTitle: meeting.title,
      startedAt: meeting.startedAt,
      decision,
    })));
}

export function getProjectRiskTimeline(project: ProjectRecord) {
  return [...project.meetings]
    .sort((a, b) => a.startedAt.localeCompare(b.startedAt))
    .flatMap((meeting) => meeting.blockers
      .filter((blocker) => blocker !== '无')
      .map((blocker) => ({
        id: `${meeting.id}-${blocker}`,
        meetingId: meeting.id,
        meetingTitle: meeting.title,
        startedAt: meeting.startedAt,
        blocker,
      })));
}

export function getProjectStatusLabel(project: ProjectRecord) {
  return project.status === 'archived' ? '已归档' : '进行中';
}

export function getTodoStatusLabel(status: TodoStatus) {
  return status === 'todo' ? '未开始' : status === 'doing' ? '进行中' : status === 'pending_confirmation' ? '待确认' : '已完成';
}

export function getMaterialDocType(material: ProjectMaterial): ProjectDocType {
  return normalizeDocType(material.docType);
}

export function getMaterialDocTypeLabel(material: ProjectMaterial) {
  return getDocTypeLabel(material.docType);
}

export function getMaterialParseStatusLabel(status: MaterialParseStatus) {
  return status === 'processing' ? '处理中' : status === 'completed' ? '已完成' : '失败';
}

export function getMaterialQaStatusLabel(material: ProjectMaterial) {
  return material.qaEnabled ? '参与问答：已启用' : '参与问答：未启用';
}

export function getPendingTaskLinkSuggestions(material: ProjectMaterial) {
  return material.taskLinkSuggestions.filter((item) => item.status === 'pending');
}

export function hasMaterialTaskLinkSuggestion(material: ProjectMaterial) {
  return getPendingTaskLinkSuggestions(material).length > 0;
}

export function getMaterialTaskLinkSuggestionCount(material: ProjectMaterial) {
  return getPendingTaskLinkSuggestions(material).length;
}

export function getMaterialSuggestedTaskStatusLabel(status: MaterialSuggestedTaskStatus) {
  return status === 'pending_confirmation' ? '待确认' : '已完成';
}

export function buildMaterialCitation(material: ProjectMaterial) {
  return `${getMaterialDocTypeLabel(material)} / ${material.title}`;
}

export function buildFallbackProject(projectId: string): ProjectRecord {
  const label = decodeURIComponent(projectId).replace(/-/g, ' ');
  return {
    id: projectId,
    backendId: 0,
    name: label || '项目加载中',
    summary: '正在加载项目详情。',
    owner: '加载中',
    stage: '项目推进',
    status: 'active',
    startTime: '待安排',
    latestMeetingAt: '待安排',
    updatedAt: '待安排',
    archivedAt: null,
    finalSummary: '正在加载项目总结。',
    meetings: [],
    materials: [],
    qaMessages: [],
    todos: [],
  };
}
