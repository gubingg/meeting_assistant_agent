import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

import {
  archiveProject as archiveProjectRequest,
  askProjectQuestion as askProjectQuestionRequest,
  confirmDocTaskLinkSuggestion,
  createProject as createProjectRequest,
  exportProjectSummary as exportProjectSummaryRequest,
  getDocTaskLinkSuggestions,
  getMeetingDetail,
  getProjectQaHistory,
  listProjectDocs,
  listProjectMeetings,
  listProjectTasks,
  listProjects,
  type ApiMeetingDetail,
  type ApiMeetingTaskItem,
  type ApiProjectCard,
  type ApiProjectDocItem,
  type ApiQaHistoryItem,
  type ApiTaskItem,
  type ApiTaskLinkSuggestion,
  ignoreDocTaskLinkSuggestion,
  reopenProject as reopenProjectRequest,
  uploadProjectDoc,
  uploadProjectMeeting,
} from '@/api/meetingAssistant';
import { getMaterialSuggestedTaskStatusLabel } from '@/data/prototype';
import {
  buildFallbackProject,
  type MaterialSuggestedTaskStatus,
  type MaterialSuggestionStatus,
  type MaterialParseStatus,
  type MeetingActionItem,
  type MeetingRecord,
  type ProjectMaterial,
  type ProjectMaterialTaskLinkSuggestion,
  type ProjectRecord,
  type ProjectStatus,
  type ProjectTodoItem,
  type QaMessage,
  type TodoStatus,
} from '@/data/prototype';

type NewProjectPayload = {
  name: string;
  summary: string;
  owner: string;
  startTime: string;
};

type UploadMaterialPayload = {
  title: string;
  docType: string;
  file: File;
};

type ToastTone = 'success' | 'info';

type ToastState = {
  message: string;
  tone: ToastTone;
};

function formatDateTime(value: string | null | undefined, fallback = '待安排') {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value.replace('T', ' ').slice(0, 16);
  }
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  const hour = `${date.getHours()}`.padStart(2, '0');
  const minute = `${date.getMinutes()}`.padStart(2, '0');
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

function extractFinalSummary(content: string, fallback: string) {
  const lines = content.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const meetingSummary = lines.find((line) => line.startsWith('- 会议摘要：'));
  return meetingSummary ? meetingSummary.replace('- 会议摘要：', '').trim() : fallback;
}

function mapProjectStatus(status: string): ProjectStatus {
  return status === 'archived' ? 'archived' : 'active';
}

function mapTaskStatus(status: string): { status: TodoStatus; blocked: boolean; overdue: boolean } {
  switch (status) {
    case 'done':
      return { status: 'done', blocked: false, overdue: false };
    case 'pending_confirmation':
      return { status: 'pending_confirmation', blocked: false, overdue: false };
    case 'blocked':
      return { status: 'doing', blocked: true, overdue: false };
    case 'delayed':
      return { status: 'doing', blocked: false, overdue: true };
    case 'in_progress':
      return { status: 'doing', blocked: false, overdue: false };
    case 'cancelled':
      return { status: 'done', blocked: false, overdue: false };
    default:
      return { status: 'todo', blocked: false, overdue: false };
  }
}

function mapMeetingTask(item: ApiMeetingTaskItem, meetingTitle: string): MeetingActionItem {
  const mapped = mapTaskStatus(item.status);
  return {
    id: String(item.id ?? `${meetingTitle}-${item.title}`),
    task: item.title,
    owner: item.owner || '未分配',
    dueDate: formatDateTime(item.due_date, '待安排'),
    status: mapped.status,
    blocked: mapped.blocked,
    lastUpdatedMeetingTitle: meetingTitle,
  };
}

function mapTodoItem(item: ApiTaskItem): ProjectTodoItem {
  const mapped = mapTaskStatus(item.status);
  return {
    id: String(item.id),
    task: item.title,
    owner: item.owner || '未分配',
    dueDate: formatDateTime(item.due_date, '待安排'),
    status: mapped.status,
    blocked: mapped.blocked,
    meetingTitle: item.source_meeting_title || item.latest_update_meeting_title || '未关联会议',
    meetingId: item.source_meeting_title || item.latest_update_meeting_title || 'unknown-meeting',
    lastUpdatedMeetingTitle: item.latest_update_meeting_title || item.source_meeting_title || '未关联会议',
    isBlocked: mapped.blocked,
    isOverdue: mapped.overdue,
  };
}

function mapMeeting(detail: ApiMeetingDetail): MeetingRecord {
  return {
    id: String(detail.id),
    title: detail.title,
    startedAt: formatDateTime(detail.meeting_time, '待安排'),
    participants: detail.participants,
    summary: detail.summary || '暂无摘要',
    decisions: detail.decisions.map((item) => item.text).filter(Boolean),
    blockers: detail.risks.length ? detail.risks.map((item) => item.text).filter(Boolean) : ['无'],
    actionItems: detail.tasks.map((item) => mapMeetingTask(item, detail.title)),
    rawFileName: detail.source_file_name || '未命名记录',
  };
}

function mapSuggestion(item: ApiTaskLinkSuggestion): ProjectMaterialTaskLinkSuggestion {
  const currentStatus = mapTaskStatus(item.current_status).status;
  const suggestedStatus = item.suggested_status === 'done' ? 'done' : 'pending_confirmation';
  const suggestionStatus = (item.suggested_status && item.suggestion_id) ? 'pending' : 'pending';
  return {
    id: String(item.suggestion_id),
    taskId: String(item.task_id),
    taskTitle: item.task_title,
    owner: item.owner || '未分配',
    currentStatus,
    sourceMeetingTitle: item.source_meeting || undefined,
    suggestedStatus,
    status: suggestionStatus as MaterialSuggestionStatus,
    matchReason: item.match_reason || undefined,
  };
}

function mapMaterial(item: ApiProjectDocItem, suggestions: ApiTaskLinkSuggestion[]): ProjectMaterial {
  return {
    id: String(item.id),
    title: item.title,
    docType: item.doc_type,
    updatedAt: formatDateTime(item.updated_at),
    parseStatus: (item.parse_status === 'failed' ? 'failed' : item.parse_status === 'processing' ? 'processing' : 'completed') as MaterialParseStatus,
    qaEnabled: item.qa_enabled,
    taskLinkSuggestions: suggestions.map(mapSuggestion),
  };
}

function mapQaHistory(history: ApiQaHistoryItem[]): QaMessage[] {
  return history.flatMap((item) => [
    {
      id: `qa-${item.id}-q`,
      role: 'user' as const,
      content: item.question,
    },
    {
      id: `qa-${item.id}-a`,
      role: 'assistant' as const,
      content: item.answer,
      citations: item.citations.map((citation) => citation.label),
    },
  ]);
}

function buildProjectStage(status: ProjectStatus, meetingCount: number) {
  if (status === 'archived') return '项目归档';
  if (meetingCount === 0) return '待启动';
  return '项目推进';
}

function buildProjectRecord(card: ApiProjectCard, meetings: MeetingRecord[], docs: ProjectMaterial[], qaMessages: QaMessage[], todos: ProjectTodoItem[], finalSummary: string): ProjectRecord {
  const status = mapProjectStatus(card.status);
  return {
    id: card.slug,
    backendId: card.id,
    name: card.name,
    summary: card.description,
    owner: card.owner,
    stage: buildProjectStage(status, meetings.length),
    status,
    startTime: formatDateTime(card.start_date),
    latestMeetingAt: formatDateTime(card.latest_meeting_time),
    updatedAt: formatDateTime(card.last_updated_at),
    archivedAt: card.archived_at ? formatDateTime(card.archived_at) : null,
    finalSummary,
    meetings,
    materials: docs,
    qaMessages,
    todos,
  };
}

async function fetchProjectAggregate(card: ApiProjectCard): Promise<ProjectRecord> {
  const [meetingItems, taskItems, docItems, qaHistory] = await Promise.all([
    listProjectMeetings(card.id),
    listProjectTasks(card.id),
    listProjectDocs(card.id),
    getProjectQaHistory(card.id),
  ]);

  const [meetingDetails, materials, finalSummary] = await Promise.all([
    Promise.all(meetingItems.map((meeting) => getMeetingDetail(meeting.id))),
    Promise.all(
      docItems.map(async (doc) => {
        const suggestions = doc.has_task_link_suggestion ? await getDocTaskLinkSuggestions(card.id, doc.id) : [];
        return mapMaterial(doc, suggestions);
      }),
    ),
    card.status === 'archived'
      ? exportProjectSummaryRequest(card.id).then((payload) => extractFinalSummary(payload.content, card.description)).catch(() => card.description)
      : Promise.resolve(card.description),
  ]);

  return buildProjectRecord(
    card,
    meetingDetails.map(mapMeeting).sort((a, b) => b.startedAt.localeCompare(a.startedAt)),
    materials.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)),
    mapQaHistory(qaHistory),
    taskItems.map(mapTodoItem),
    finalSummary,
  );
}

function sortProjects(projects: ProjectRecord[]) {
  return [...projects].sort((a, b) => {
    if (a.status !== b.status) {
      return a.status === 'active' ? -1 : 1;
    }
    return b.updatedAt.localeCompare(a.updatedAt);
  });
}

export const useUiStore = defineStore('ui', () => {
  const isCreateModalOpen = ref(false);
  const projects = ref<ProjectRecord[]>([]);
  const toast = ref<ToastState | null>(null);
  const isHydrating = ref(false);
  const initialized = ref(false);
  let toastTimer: ReturnType<typeof setTimeout> | null = null;

  function openCreateModal() {
    isCreateModalOpen.value = true;
  }

  function closeCreateModal() {
    isCreateModalOpen.value = false;
  }

  function showToast(message: string, tone: ToastTone = 'success') {
    toast.value = { message, tone };
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.value = null;
    }, 2600);
  }

  function closeToast() {
    toast.value = null;
    if (toastTimer) {
      clearTimeout(toastTimer);
      toastTimer = null;
    }
  }

  function upsertProject(project: ProjectRecord) {
    const next = [...projects.value];
    const index = next.findIndex((item) => item.id === project.id);
    if (index >= 0) {
      next[index] = project;
    } else {
      next.push(project);
    }
    projects.value = sortProjects(next);
    return project;
  }

  async function refreshProjects() {
    isHydrating.value = true;
    try {
      const cards = await listProjects('all');
      const aggregates = await Promise.all(cards.map(fetchProjectAggregate));
      projects.value = sortProjects(aggregates);
      initialized.value = true;
      return projects.value;
    } finally {
      isHydrating.value = false;
    }
  }

  async function initialize() {
    if (initialized.value && projects.value.length) {
      return projects.value;
    }
    return refreshProjects();
  }

  async function ensureProject(projectId: string, force = false) {
    if (!force) {
      const existing = projects.value.find((project) => project.id === projectId);
      if (existing) return existing;
    }

    const cards = await listProjects('all');
    const card = cards.find((item) => item.slug === projectId);
    if (!card) {
      throw new Error('项目不存在');
    }
    const project = await fetchProjectAggregate(card);
    initialized.value = true;
    return upsertProject(project);
  }

  async function addProject(payload: NewProjectPayload) {
    const detail = await createProjectRequest({
      name: payload.name,
      description: payload.summary,
      owner: payload.owner,
      start_date: payload.startTime ? `${payload.startTime}T00:00:00` : null,
    });

    const project = await ensureProject(detail.slug, true);
    isCreateModalOpen.value = false;
    showToast(`已创建项目《${project.name}》。`, 'success');
    return project;
  }

  async function archiveProject(projectId: string) {
    const project = await ensureProject(projectId);
    await archiveProjectRequest(project.backendId);
    const latest = await ensureProject(projectId, true);
    showToast('项目已归档，可继续查看历史记录和追溯问答。', 'success');
    return latest;
  }

  async function reopenProject(projectId: string) {
    const project = await ensureProject(projectId);
    await reopenProjectRequest(project.backendId);
    const latest = await ensureProject(projectId, true);
    showToast('项目已重新开启，上传和查看入口已恢复。', 'success');
    return latest;
  }

  async function exportProjectSummary(projectId: string) {
    const project = await ensureProject(projectId);
    await exportProjectSummaryRequest(project.backendId);
    showToast(`已生成《${project.name}》的项目总结导出内容。`, 'info');
  }

  async function uploadProjectMaterial(projectId: string, payload: UploadMaterialPayload) {
    const project = await ensureProject(projectId);
    const created = await uploadProjectDoc(project.backendId, {
      file: payload.file,
      title: payload.title,
      docType: payload.docType,
    });
    await ensureProject(projectId, true);
    showToast(`已上传资料《${created.title}》。`, 'success');
    return created;
  }

  async function uploadProjectMeetingRecord(projectId: string, file: File) {
    const project = await ensureProject(projectId);
    const created = await uploadProjectMeeting(project.backendId, file);
    await ensureProject(projectId, true);
    showToast(`已上传会议《${created.title}》。`, 'success');
    return created;
  }

  async function confirmMaterialTaskLink(projectId: string, materialId: string, suggestionId: string, nextStatus: MaterialSuggestedTaskStatus) {
    const project = await ensureProject(projectId);
    await confirmDocTaskLinkSuggestion(project.backendId, Number(materialId), Number(suggestionId), getMaterialSuggestedTaskStatusLabel(nextStatus));
    await ensureProject(projectId, true);
    showToast('待办状态已按确认结果更新。', 'success');
  }

  async function ignoreMaterialTaskLink(projectId: string, materialId: string, suggestionId: string) {
    const project = await ensureProject(projectId);
    await ignoreDocTaskLinkSuggestion(project.backendId, Number(materialId), Number(suggestionId));
    await ensureProject(projectId, true);
    showToast('该条关联建议已忽略。', 'info');
  }

  async function askProjectQuestion(projectId: string, question: string) {
    const project = await ensureProject(projectId);
    const response = await askProjectQuestionRequest(project.backendId, question);
    const nextMessages: QaMessage[] = [
      ...project.qaMessages,
      { id: `user-${Date.now()}`, role: 'user', content: question },
      { id: `assistant-${Date.now() + 1}`, role: 'assistant', content: response.answer, citations: response.citations.map((item) => item.label) },
    ];
    upsertProject({ ...project, qaMessages: nextMessages });
    return response;
  }

  function getProject(projectId: string) {
    return projects.value.find((project) => project.id === projectId) ?? buildFallbackProject(projectId);
  }

  const archivedProjects = computed(() => projects.value.filter((project) => project.status === 'archived'));
  const activeProjects = computed(() => projects.value.filter((project) => project.status === 'active'));

  return {
    isCreateModalOpen,
    projects,
    activeProjects,
    archivedProjects,
    toast,
    isHydrating,
    openCreateModal,
    closeCreateModal,
    closeToast,
    showToast,
    initialize,
    refreshProjects,
    ensureProject,
    addProject,
    archiveProject,
    reopenProject,
    exportProjectSummary,
    uploadProjectMaterial,
    uploadProjectMeeting: uploadProjectMeetingRecord,
    confirmMaterialTaskLink,
    ignoreMaterialTaskLink,
    askProjectQuestion,
    getProject,
  };
});
