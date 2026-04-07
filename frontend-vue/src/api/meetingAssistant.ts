const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || 'http://localhost:8000';
const REQUEST_TIMEOUT_MS = 12000;

type RequestOptions = {
  method?: string;
  body?: BodyInit | null;
  headers?: HeadersInit;
  timeoutMs?: number | null;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs === undefined ? REQUEST_TIMEOUT_MS : options.timeoutMs;
  const timeoutId = typeof timeoutMs === 'number' && timeoutMs > 0 ? window.setTimeout(() => controller.abort(), timeoutMs) : null;

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? 'GET',
      body: options.body,
      headers: options.headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || '请求失败');
      }
      throw new Error((await response.text()) || '请求失败');
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('后端接口响应超时，请检查后端服务或数据库连接。');
    }
    if (error instanceof TypeError) {
      throw new Error('无法连接到后端服务，请确认 http://localhost:8000 已启动。');
    }
    throw error;
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
}

export type ApiProjectCard = {
  id: number;
  slug: string;
  name: string;
  description: string;
  owner: string;
  start_date: string | null;
  status: string;
  archived_at: string | null;
  last_updated_at: string | null;
  latest_meeting_time: string | null;
  todo_count: number;
  meeting_count: number;
  unfinished_todo_count: number;
};

export type ApiProjectDetail = {
  id: number;
  slug: string;
  name: string;
  description: string;
  owner: string;
  start_date: string | null;
  status: string;
  archived_at: string | null;
  meeting_count: number;
  todo_count: number;
  latest_updated_at: string | null;
};

export type ApiProjectStatusResponse = {
  id: number;
  status: string;
  archived_at: string | null;
};

export type ApiMeetingListItem = {
  id: number;
  title: string;
  meeting_time: string | null;
  summary_preview: string;
  risk_count: number;
  task_count: number;
  decision_count: number;
};

export type ApiMeetingTaskItem = {
  id: number | null;
  title: string;
  description: string | null;
  owner: string | null;
  due_date: string | null;
  status: string;
};

export type ApiMeetingDetail = {
  id: number;
  project_id: number;
  title: string;
  meeting_time: string | null;
  participants: string[];
  summary: string;
  decisions: Array<{ text: string }>;
  tasks: ApiMeetingTaskItem[];
  risks: Array<{ text: string }>;
  raw_json: Record<string, unknown> | null;
  raw_text: string | null;
  source_file_name: string | null;
};

export type ApiMeetingUploadResponse = {
  meeting_id: number;
  title: string;
  meeting_time: string | null;
  summary: string;
  decisions: Array<{ text: string }>;
  tasks: ApiMeetingTaskItem[];
  risks: Array<{ text: string }>;
  updated_doc_versions: Array<Record<string, unknown>>;
};

export type ApiTaskItem = {
  id: number;
  title: string;
  owner: string | null;
  due_date: string | null;
  status: string;
  status_label: string;
  source_meeting_title: string | null;
  latest_update_meeting_title: string | null;
};

export type ApiTaskSummary = {
  total: number;
  done_count: number;
  unfinished_count: number;
  delayed_count: number;
  blocked_count: number;
};

export type ApiProjectDocItem = {
  id: number;
  title: string;
  doc_name: string;
  doc_type: string;
  doc_type_label: string;
  parse_status: string;
  parse_status_label: string;
  qa_enabled: boolean;
  has_task_link_suggestion: boolean;
  task_link_suggestion_count: number;
  current_version_label: string | null;
  updated_at: string | null;
};

export type ApiProjectDocUploadResponse = {
  doc_id: number;
  title: string;
  doc_name: string;
  doc_type: string;
  doc_type_label: string;
  parse_status: string;
  parse_status_label: string;
  qa_enabled: boolean;
  has_task_link_suggestion: boolean;
  task_link_suggestion_count: number;
  current_version_label: string;
  indexed_chunks: number;
};

export type ApiTaskLinkSuggestion = {
  suggestion_id: number;
  task_id: number;
  task_title: string;
  owner: string | null;
  current_status: string;
  current_status_label: string;
  source_meeting: string | null;
  suggested_status: string;
  suggested_status_label: string;
  match_reason: string | null;
  match_score: number;
};

export type ApiTaskLinkActionResponse = {
  suggestion_id: number;
  suggestion_status: string;
  suggestion_status_label: string;
  task_id: number;
  task_status: string;
  task_status_label: string;
};

export type ApiCitation = {
  source_type: string;
  label: string;
  source_id: number | string;
  doc_type: string | null;
  doc_type_label: string | null;
};

export type ApiQaResponse = {
  answer: string;
  citations: ApiCitation[];
};

export type ApiQaHistoryItem = {
  id: number;
  question: string;
  answer: string;
  citations: ApiCitation[];
  created_at: string;
};

export type ApiExportSummary = {
  project_id: number;
  format: string;
  content: string;
};

export function listProjects(status = 'all') {
  return request<ApiProjectCard[]>(`/api/projects?status=${encodeURIComponent(status)}`);
}

export function createProject(payload: { name: string; description: string; owner: string; start_date?: string | null }) {
  return request<ApiProjectDetail>('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export function getProjectDetail(projectId: number) {
  return request<ApiProjectDetail>(`/api/projects/${projectId}`);
}

export function archiveProject(projectId: number) {
  return request<ApiProjectStatusResponse>(`/api/projects/${projectId}/archive`, { method: 'POST' });
}

export function reopenProject(projectId: number) {
  return request<ApiProjectStatusResponse>(`/api/projects/${projectId}/reopen`, { method: 'POST' });
}

export function listProjectMeetings(projectId: number) {
  return request<ApiMeetingListItem[]>(`/api/projects/${projectId}/meetings`);
}

export function getMeetingDetail(meetingId: number) {
  return request<ApiMeetingDetail>(`/api/meetings/${meetingId}`);
}

export function uploadProjectMeeting(projectId: number, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return request<ApiMeetingUploadResponse>(`/api/projects/${projectId}/meetings/upload`, {
    method: 'POST',
    body: formData,
    timeoutMs: null,
  });
}

export function listProjectTasks(projectId: number, status = 'all') {
  return request<ApiTaskItem[]>(`/api/projects/${projectId}/tasks?status=${encodeURIComponent(status)}`);
}

export function getProjectTaskSummary(projectId: number) {
  return request<ApiTaskSummary>(`/api/projects/${projectId}/tasks/summary`);
}

export function listProjectDocs(projectId: number, docType = 'all') {
  return request<ApiProjectDocItem[]>(`/api/projects/${projectId}/docs?doc_type=${encodeURIComponent(docType)}`);
}

export function uploadProjectDoc(projectId: number, payload: { file: File; title?: string; docType: string }) {
  const formData = new FormData();
  formData.append('file', payload.file);
  formData.append('doc_type', payload.docType);
  if (payload.title) {
    formData.append('title', payload.title);
  }
  return request<ApiProjectDocUploadResponse>(`/api/projects/${projectId}/docs`, {
    method: 'POST',
    body: formData,
  });
}

export function getDocTaskLinkSuggestions(projectId: number, docId: number) {
  return request<ApiTaskLinkSuggestion[]>(`/api/projects/${projectId}/docs/${docId}/task-link-suggestions`);
}

export function confirmDocTaskLinkSuggestion(projectId: number, docId: number, suggestionId: number, updateTaskStatus: string) {
  return request<ApiTaskLinkActionResponse>(`/api/projects/${projectId}/docs/${docId}/task-link-suggestions/${suggestionId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ update_task_status: updateTaskStatus }),
  });
}

export function ignoreDocTaskLinkSuggestion(projectId: number, docId: number, suggestionId: number) {
  return request<ApiTaskLinkActionResponse>(`/api/projects/${projectId}/docs/${docId}/task-link-suggestions/${suggestionId}/ignore`, {
    method: 'POST',
  });
}

export function askProjectQuestion(projectId: number, question: string) {
  return request<ApiQaResponse>(`/api/projects/${projectId}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}

export function getProjectQaHistory(projectId: number) {
  return request<ApiQaHistoryItem[]>(`/api/projects/${projectId}/qa/history`);
}

export function exportProjectSummary(projectId: number) {
  return request<ApiExportSummary>(`/api/projects/${projectId}/export-summary`);
}
