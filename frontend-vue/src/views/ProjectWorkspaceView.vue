<template>
  <AppShell background-class="min-h-screen bg-[linear-gradient(135deg,#f3eee5_0%,#efe0cc_40%,#f7f3ed_100%)]">
    <ToastBanner v-if="uiStore.toast" :message="uiStore.toast.message" :tone="uiStore.toast.tone" @close="uiStore.closeToast()" />

    <div class="flex flex-col gap-5">
      <SectionCard v-if="isArchived" class="border border-slate-200 bg-slate-50/85">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div class="flex flex-wrap items-center gap-3">
              <span class="rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700">已归档</span>
              <span class="text-sm text-ink/55">归档时间：{{ project.archivedAt }}</span>
            </div>
            <p class="mt-3 text-sm leading-7 text-ink/70">该项目已进入只读状态，可继续查看历史会议、待办、资料和问答记录。</p>
          </div>
          <div class="flex flex-wrap gap-3">
            <button type="button" class="rounded-2xl border border-sand bg-white px-4 py-3 text-sm text-ink" @click="handleExportSummary">
              导出项目总结
            </button>
            <button type="button" class="rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white" @click="confirmMode = 'reopen'">
              重新开启项目
            </button>
          </div>
        </div>
      </SectionCard>

      <SectionCard>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div class="min-w-0 flex-1 space-y-4">
                <div class="flex flex-wrap items-center gap-3">
                  <RouterLink to="/" class="rounded-full border border-sand px-3 py-1 text-sm text-ink/70">返回首页</RouterLink>
                  <span class="rounded-full px-3 py-1 text-sm" :class="isArchived ? 'bg-slate-200 text-slate-700' : 'bg-emerald-100 text-emerald-700'">
                    {{ isArchived ? '已归档' : '进行中' }}
                  </span>
                  <span class="text-sm text-ink/55">{{ project.stage }}</span>
                </div>

                <div>
                  <p class="text-sm uppercase tracking-[0.3em] text-pine">Project Workspace</p>
                  <h1 class="mt-2 text-3xl font-semibold text-ink md:text-4xl">{{ project.name }}</h1>
                  <p v-if="isArchived && project.archivedAt" class="mt-2 text-sm text-ink/55">归档时间：{{ project.archivedAt }}</p>
                </div>

                <p class="text-base leading-7 text-ink/72">{{ project.summary }}</p>
              </div>

              <div v-if="!isArchived" class="flex shrink-0 flex-wrap gap-3 xl:pt-1">
                <button type="button" class="rounded-2xl border border-sand bg-white px-4 py-3 text-sm text-ink" @click="handleExportSummary">
                  导出项目总结
                </button>
                <button type="button" class="rounded-2xl border border-rose-300 bg-white px-4 py-3 text-sm text-rose-700" @click="confirmMode = 'archive'">
                  归档项目
                </button>
              </div>
            </div>

            <div class="grid gap-3 text-sm text-ink/75 xl:grid-cols-[180px_220px_minmax(0,1fr)_430px]">
              <div class="rounded-2xl bg-paper/80 p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-pine">负责人</p>
                <p class="mt-2 text-base font-medium text-ink">{{ project.owner }}</p>
              </div>

              <div class="rounded-2xl bg-paper/80 p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-pine">开始时间</p>
                <p class="mt-2 text-base font-medium text-ink">{{ project.startTime }}</p>
              </div>

              <div class="rounded-2xl bg-paper/80 p-4">
                <p class="text-xs uppercase tracking-[0.2em] text-pine">会议 / 待办 / 更新</p>
                <p class="mt-2 text-sm font-medium text-ink xl:whitespace-nowrap">
                  {{ projectMetrics.meetingCount }} 场会议 / {{ projectMetrics.todoCount }} 条待办 · 最后更新时间 {{ projectMetrics.lastUpdatedAt }}
                </p>
              </div>

              <div class="rounded-2xl bg-paper/80 p-4">
                <div class="flex h-full flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                  <div class="shrink-0">
                    <p class="text-xs uppercase tracking-[0.2em] text-pine">快捷入口</p>
                  </div>
                  <div class="grid gap-3 sm:grid-cols-2 xl:min-w-[250px] xl:flex-1">
                    <RouterLink :to="`/projects/${project.id}/todos`" class="inline-flex items-center justify-center gap-2 rounded-xl bg-pine px-3 py-3 text-sm text-white">
                      <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current" aria-hidden="true">
                        <path d="M7.5 2a2 2 0 0 0-1.937 1.5H4.5A2.5 2.5 0 0 0 2 6v9.5A2.5 2.5 0 0 0 4.5 18h11a2.5 2.5 0 0 0 2.5-2.5V6a2.5 2.5 0 0 0-2.5-2.5h-1.063A2 2 0 0 0 12.5 2h-5ZM10 4a.75.75 0 1 1 0 1.5A.75.75 0 0 1 10 4Zm-2.1 5.2 1.2 1.2 3-3 1.1 1.1-4.1 4.1-2.3-2.3 1.1-1.1Zm0 4 1.2 1.2 3-3 1.1 1.1-4.1 4.1-2.3-2.3 1.1-1.1Z" />
                      </svg>
                      待办看板
                    </RouterLink>

                    <RouterLink :to="`/projects/${project.id}/qa`" class="inline-flex items-center justify-center gap-2 rounded-xl border border-sand bg-white px-3 py-3 text-sm text-ink">
                      <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current text-pine" aria-hidden="true">
                        <path d="M10 2C5.582 2 2 4.91 2 8.5c0 1.91 1.015 3.628 2.633 4.82-.13 1.073-.55 2.09-1.222 2.942a.75.75 0 0 0 .854 1.174c1.646-.48 3.047-1.16 4.128-2.003.522.044 1.059.067 1.607.067 4.418 0 8-2.91 8-6.5S14.418 2 10 2Zm-3 5.5A1.5 1.5 0 1 1 7 10.5 1.5 1.5 0 0 1 7 7.5Zm3 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm4.5 1.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
                      </svg>
                      答疑助手
                    </RouterLink>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </SectionCard>

      <ArchivedProjectSummary v-if="isArchived" :project="project" />

      <template v-else>
        <SectionCard>
          <div class="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
            <div class="space-y-4">
              <div class="rounded-[24px] bg-paper/80 p-4 shadow-sm">
                <form class="grid gap-3" @submit.prevent="handleMeetingUpload">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <p class="text-sm uppercase tracking-[0.26em] text-pine">Meeting JSON</p>
                      <h2 class="mt-1 text-lg font-semibold text-ink">上传会议 JSON</h2>
                    </div>
                    <button
                      type="submit"
                      class="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-70"
                      :disabled="isMeetingUploadBusy"
                    >
                      {{ meetingUploadButtonLabel }}
                    </button>
                  </div>
                  <input ref="meetingInputRef" type="file" accept=".json" required :disabled="isMeetingUploadBusy" />
                </form>

                <div v-if="showMeetingUploadFeedback" class="mt-3 rounded-2xl border px-4 py-3" :class="meetingUploadFeedbackClass">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-medium">{{ meetingUploadStatusLabel }}</p>
                      <p v-if="meetingUploadFileName" class="mt-1 text-xs opacity-80">当前文件：{{ meetingUploadFileName }}</p>
                    </div>
                    <span
                      v-if="isMeetingUploadBusy"
                      class="mt-0.5 inline-flex h-2.5 w-2.5 rounded-full bg-current animate-pulse"
                      aria-hidden="true"
                    />
                  </div>
                  <p v-if="uploadHint" class="mt-2 text-sm leading-6">{{ uploadHint }}</p>
                </div>
              </div>

              <SectionCard>
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="text-sm uppercase tracking-[0.3em] text-pine">Meetings</p>
                    <h2 class="mt-2 text-xl font-semibold text-ink">会议列表</h2>
                  </div>
                  <span class="rounded-full bg-paper px-3 py-1 text-xs text-ink/65">{{ meetings.length }} 场</span>
                </div>

                <div class="mt-5 space-y-3">
                  <button
                    v-for="meeting in meetings"
                    :key="meeting.id"
                    class="w-full rounded-[22px] border p-4 text-left transition"
                    :class="meeting.id === selectedMeetingId ? 'border-pine bg-pine text-white shadow-lg' : 'border-white/70 bg-paper/70 text-ink hover:border-sand'"
                    @click="selectedMeetingId = meeting.id"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <p class="text-xs tracking-[0.18em] whitespace-nowrap" :class="meeting.id === selectedMeetingId ? 'text-white/75' : 'text-pine'">
                        {{ meeting.startedAt }}
                      </p>
                      <span
                        class="inline-flex items-center whitespace-nowrap rounded-full px-3 py-1 text-[11px] leading-none"
                        :class="meeting.id === selectedMeetingId ? 'bg-white/20 text-white' : 'bg-white text-pine'"
                      >
                        风险 {{ visibleBlockers(meeting).length }} 项
                      </span>
                    </div>
                    <h3 class="mt-2 text-lg font-medium">{{ meeting.title }}</h3>
                    <p class="mt-2 text-sm leading-6" :class="meeting.id === selectedMeetingId ? 'text-white/85' : 'text-ink/65'">
                      {{ meeting.summary }}
                    </p>
                    <div class="mt-3 flex flex-wrap gap-2 text-xs" :class="meeting.id === selectedMeetingId ? 'text-white/80' : 'text-ink/55'">
                      <span>待办 {{ meeting.actionItems.length }}</span>
                      <span>决策 {{ meeting.decisions.length }}</span>
                      <span>参会 {{ meeting.participants.length }}</span>
                    </div>
                  </button>

                  <div v-if="!meetings.length" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/60">
                    当前还没有会议，先从上方上传会议 JSON 开始。
                  </div>
                </div>
              </SectionCard>
            </div>

            <SectionCard>
              <div v-if="selectedMeeting" class="space-y-6">
                <div class="flex flex-col gap-3 border-b border-sand/80 pb-5 md:flex-row md:items-end md:justify-between">
                  <div>
                    <p class="text-sm uppercase tracking-[0.3em] text-pine">Structured Meeting Doc</p>
                    <h2 class="mt-2 text-3xl font-semibold text-ink">{{ selectedMeeting.title }}</h2>
                  </div>
                  <div class="text-sm text-ink/65">
                    <p>{{ selectedMeeting.startedAt }}</p>
                    <p>{{ selectedMeeting.participants.join(' / ') }}</p>
                  </div>
                </div>

                <section class="rounded-[24px] bg-paper/70 p-5">
                  <h3 class="text-lg font-semibold text-ink">1. 会议摘要</h3>
                  <p class="mt-3 text-sm leading-7 text-ink/75">{{ selectedMeeting.summary }}</p>
                </section>

                <section class="rounded-[24px] bg-paper/70 p-5">
                  <h3 class="text-lg font-semibold text-ink">2. 关键结论</h3>
                  <ul class="mt-3 space-y-3 text-sm leading-7 text-ink/75">
                    <li v-for="decision in selectedMeeting.decisions" :key="decision" class="rounded-2xl bg-white px-4 py-3">
                      {{ decision }}
                    </li>
                  </ul>
                </section>

                <section class="rounded-[24px] bg-paper/70 p-5">
                  <h3 class="text-lg font-semibold text-ink">3. 待办项</h3>
                  <div class="mt-3 space-y-3">
                    <article v-for="item in selectedMeeting.actionItems" :key="item.id" class="rounded-2xl bg-white px-4 py-4 text-sm text-ink/75">
                      <div class="flex flex-wrap items-center justify-between gap-3">
                        <p class="font-medium text-ink">{{ item.task }}</p>
                        <span class="rounded-full bg-paper px-3 py-1 text-xs text-pine">{{ getTodoStatusLabel(item.status) }}</span>
                      </div>
                      <p class="mt-2">负责人：{{ item.owner }}</p>
                      <p class="mt-1">截止时间：{{ item.dueDate }}</p>
                    </article>

                    <p v-if="!selectedMeeting.actionItems.length" class="rounded-2xl bg-white px-4 py-4 text-sm text-ink/65">
                      当前会议 JSON 已上传，待解析后会在这里生成待办项。
                    </p>
                  </div>
                </section>

                <section class="grid gap-4 lg:grid-cols-2">
                  <div class="rounded-[24px] bg-paper/70 p-5">
                    <h3 class="text-lg font-semibold text-ink">4. 风险与阻塞</h3>
                    <ul class="mt-3 space-y-3 text-sm leading-7 text-ink/75">
                      <li v-for="blocker in visibleBlockers(selectedMeeting)" :key="blocker" class="rounded-2xl bg-white px-4 py-3">
                        {{ blocker }}
                      </li>
                    </ul>
                    <p v-if="!visibleBlockers(selectedMeeting).length" class="mt-3 rounded-2xl bg-white px-4 py-3 text-sm text-ink/60">当前会议没有额外风险记录。</p>
                  </div>

                  <div class="rounded-[24px] bg-paper/70 p-5">
                    <h3 class="text-lg font-semibold text-ink">5. 原始记录入口</h3>
                    <div class="mt-3 rounded-2xl bg-white p-4 text-sm text-ink/75">
                      <p class="font-medium text-ink">{{ selectedMeeting.rawFileName }}</p>
                      <p class="mt-2 leading-6">这里预留查看上传 JSON / transcript 的入口，后续可接入原始内容预览或下载能力。</p>
                      <button type="button" class="mt-4 rounded-xl border border-sand px-3 py-2 text-sm text-ink">查看原始记录入口</button>
                    </div>
                  </div>
                </section>
              </div>

              <div v-else class="rounded-[24px] bg-paper/70 p-6 text-sm text-ink/70">
                当前项目还没有会议，先从左侧上传会议 JSON 开始。
              </div>
            </SectionCard>

            <SectionCard>
              <div>
                <p class="text-sm uppercase tracking-[0.3em] text-pine">Project Materials</p>
                <h2 class="mt-2 text-xl font-semibold text-ink">项目资料</h2>
                <p class="mt-3 text-sm leading-6 text-ink/65">用于沉淀项目长期背景资料，后续答疑助手也会把这些内容作为回答依据。</p>
              </div>

              <form class="mt-5 grid gap-3 rounded-[24px] bg-paper/75 p-4" @submit.prevent="handleMaterialUpload">
                <select v-model="materialType" required>
                  <option value="" disabled>请选择资料类型</option>
                  <option v-for="option in docTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <input ref="materialInputRef" type="file" required />
                <button type="submit" class="rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white">上传项目资料</button>
                <p v-if="materialHint" class="text-sm" :class="materialHintTone === 'error' ? 'text-rose-600' : 'text-pine'">{{ materialHint }}</p>
              </form>

              <div class="mt-5 flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-medium text-ink">资料筛选</p>
                  <p class="text-xs text-ink/55">按资料类型快速查看当前项目资料。</p>
                </div>
                <select v-model="materialFilter" class="max-w-[180px]">
                  <option value="all">全部类型</option>
                  <option v-for="option in docTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="mt-5 space-y-3">
                <article v-for="material in filteredMaterials" :key="material.id" class="rounded-[22px] bg-paper/75 p-4">
                  <div class="flex items-start justify-between gap-3">
                    <h3 class="text-sm font-medium text-ink">{{ material.title }}</h3>
                    <span class="rounded-full bg-white px-3 py-1 text-xs text-pine">{{ getMaterialDocTypeLabel(material) }}</span>
                  </div>
                  <div class="mt-3 flex flex-wrap gap-2 text-xs text-ink/55">
                    <span>更新时间：{{ material.updatedAt }}</span>
                    <span>处理状态：{{ getMaterialParseStatusLabel(material.parseStatus) }}</span>
                    <span>{{ getMaterialQaStatusLabel(material) }}</span>
                  </div>

                  <div v-if="hasMaterialTaskLinkSuggestion(material)" class="mt-4 rounded-2xl border border-sand/80 bg-white/75 p-4">
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="text-sm font-medium text-ink">检测到可关联待办</p>
                        <p class="mt-1 text-xs text-ink/60">可能对应 {{ getMaterialTaskLinkSuggestionCount(material) }} 条待办</p>
                      </div>
                      <button type="button" class="rounded-xl border border-sand px-3 py-2 text-sm text-ink" @click="openSuggestionModal(material)">
                        查看并确认
                      </button>
                    </div>
                  </div>
                </article>

                <div v-if="!filteredMaterials.length && materials.length" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/60">
                  当前筛选下暂无资料，换一个资料类型看看。
                </div>

                <div v-if="!materials.length" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/60">
                  当前项目还没有资料，可以直接在这里上传项目级文件。
                </div>
              </div>
            </SectionCard>
          </div>
        </SectionCard>
      </template>
    </div>

    <div v-if="activeSuggestion && activeMaterial" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-4">
      <div class="w-full max-w-2xl rounded-[28px] bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.28em] text-pine">Task Link Suggestion</p>
            <h2 class="mt-2 text-2xl font-semibold text-ink">确认资料关联待办</h2>
            <p class="mt-2 text-sm text-ink/65">资料《{{ activeMaterial.title }}》检测到一条可关联待办，确认后才会更新待办状态。</p>
          </div>
          <button type="button" class="rounded-full border border-sand px-3 py-1 text-sm text-ink/70" @click="closeSuggestionModal">关闭</button>
        </div>

        <div class="mt-5 grid gap-3 rounded-[24px] bg-paper/70 p-5 text-sm text-ink/75 md:grid-cols-2">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-pine">待办名称</p>
            <p class="mt-2 text-base font-medium text-ink">{{ activeSuggestion.taskTitle }}</p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-pine">当前负责人</p>
            <p class="mt-2 text-base font-medium text-ink">{{ activeSuggestion.owner }}</p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-pine">当前状态</p>
            <p class="mt-2 text-base font-medium text-ink">{{ getTodoStatusLabel(activeSuggestion.currentStatus) }}</p>
          </div>
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-pine">来源会议</p>
            <p class="mt-2 text-base font-medium text-ink">{{ activeSuggestion.sourceMeetingTitle || '未关联会议' }}</p>
          </div>
        </div>

        <div class="mt-4 rounded-[24px] bg-paper/70 p-5 text-sm text-ink/75">
          <p class="text-xs uppercase tracking-[0.2em] text-pine">建议更新状态</p>
          <select v-model="selectedSuggestedStatus" class="mt-3 max-w-[220px]">
            <option value="pending_confirmation">待确认</option>
            <option value="done">已完成</option>
          </select>
          <p v-if="activeSuggestion.matchReason" class="mt-4 leading-7 text-ink/65">匹配原因：{{ activeSuggestion.matchReason }}</p>
        </div>

        <div class="mt-6 flex items-center justify-end gap-3">
          <button type="button" class="rounded-2xl border border-sand px-4 py-3 text-sm text-ink" @click="handleIgnoreSuggestion">
            暂不处理
          </button>
          <button type="button" class="rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white" @click="handleConfirmSuggestion">
            确认更新
          </button>
        </div>
      </div>
    </div>

    <ConfirmDialog
      :open="confirmMode === 'archive' || confirmMode === 'reopen'"
      :title="confirmMode === 'archive' ? '归档项目' : '重新开启项目'"
      :description="confirmMode === 'archive'
        ? '归档后，项目会进入只读状态。你仍然可以查看历史会议、待办、项目资料和问答记录，但无法继续上传新会议、更新待办或新增资料。'
        : '重新开启后，你可以继续上传会议、更新待办和新增项目资料。'"
      :confirm-label="confirmMode === 'archive' ? '确认归档' : '确认开启'"
      :project-name="project.name"
      :last-updated-at="projectMetrics.lastUpdatedAt"
      :unfinished-todo-count="projectMetrics.unfinishedTodoCount"
      :open-risk-count="projectMetrics.riskCount"
      :warning-text="confirmMode === 'archive' && projectMetrics.unfinishedTodoCount > 0 ? `当前仍有 ${projectMetrics.unfinishedTodoCount} 条未完成待办。` : ''"
      :tone="confirmMode === 'archive' ? 'danger' : 'primary'"
      @cancel="confirmMode = null"
      @confirm="handleConfirmAction"
    />
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import AppShell from '@/components/AppShell.vue';
import ArchivedProjectSummary from '@/components/ArchivedProjectSummary.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import SectionCard from '@/components/SectionCard.vue';
import ToastBanner from '@/components/ToastBanner.vue';
import { DOC_TYPE_OPTIONS, type ProjectDocTypeFilter } from '@/constants/docTypes';
import {
  getMaterialDocType,
  getMaterialDocTypeLabel,
  getMaterialParseStatusLabel,
  getMaterialQaStatusLabel,
  getMaterialTaskLinkSuggestionCount,
  getPendingTaskLinkSuggestions,
  getProjectMetrics,
  getTodoStatusLabel,
  hasMaterialTaskLinkSuggestion,
  type MaterialSuggestedTaskStatus,
  type MeetingRecord,
  type ProjectMaterial,
} from '@/data/prototype';
import { useUiStore } from '@/stores/ui';

const route = useRoute();
const uiStore = useUiStore();
const project = computed(() => uiStore.getProject(String(route.params.projectId)));
const meetings = ref<MeetingRecord[]>([]);
const materials = ref<ProjectMaterial[]>([]);
const selectedMeetingId = ref('');
const uploadHint = ref('');
const meetingUploadState = ref<'idle' | 'uploading' | 'analyzing' | 'success' | 'error'>('idle');
const meetingUploadFileName = ref('');
let meetingUploadPhaseTimer: ReturnType<typeof setTimeout> | null = null;
const materialHint = ref('');
const materialHintTone = ref<'info' | 'error'>('info');
const meetingInputRef = ref<HTMLInputElement | null>(null);
const materialInputRef = ref<HTMLInputElement | null>(null);
const materialType = ref('');
const materialFilter = ref<ProjectDocTypeFilter>('all');
const confirmMode = ref<'archive' | 'reopen' | null>(null);
const activeMaterialId = ref<string | null>(null);
const activeSuggestionId = ref<string | null>(null);
const selectedSuggestedStatus = ref<MaterialSuggestedTaskStatus>('pending_confirmation');

const docTypeOptions = DOC_TYPE_OPTIONS;
const isArchived = computed(() => project.value.status === 'archived');
const projectMetrics = computed(() => getProjectMetrics({ ...project.value, meetings: meetings.value, materials: materials.value }));
const selectedMeeting = computed(() => meetings.value.find((meeting) => meeting.id === selectedMeetingId.value) ?? meetings.value[0]);
const filteredMaterials = computed(() => {
  if (materialFilter.value === 'all') {
    return materials.value;
  }
  return materials.value.filter((material) => getMaterialDocType(material) === materialFilter.value);
});
const activeMaterial = computed(() => materials.value.find((material) => material.id === activeMaterialId.value) ?? null);
const activeSuggestion = computed(() => activeMaterial.value?.taskLinkSuggestions.find((item) => item.id === activeSuggestionId.value && item.status === 'pending') ?? null);

const isMeetingUploadBusy = computed(() => meetingUploadState.value === 'uploading' || meetingUploadState.value === 'analyzing');
const meetingUploadButtonLabel = computed(() => {
  if (meetingUploadState.value === 'uploading') return '上传中';
  if (meetingUploadState.value === 'analyzing') return '分析中';
  return '上传会议';
});
const meetingUploadStatusLabel = computed(() => {
  if (meetingUploadState.value === 'uploading') return '正在上传会议文件';
  if (meetingUploadState.value === 'analyzing') return '会议内容分析中';
  if (meetingUploadState.value === 'success') return '会议处理完成';
  if (meetingUploadState.value === 'error') return '会议处理失败';
  return '';
});
const showMeetingUploadFeedback = computed(() => meetingUploadState.value !== 'idle' || Boolean(uploadHint.value));
const meetingUploadFeedbackClass = computed(() => {
  if (meetingUploadState.value === 'error') return 'border-rose-200 bg-rose-50 text-rose-700';
  if (meetingUploadState.value === 'success') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  return 'border-sand/80 bg-white/75 text-pine';
});

function syncLocalState() {
  meetings.value = project.value.meetings.map((meeting) => ({ ...meeting, actionItems: [...meeting.actionItems] }));
  materials.value = project.value.materials.map((material) => ({ ...material, taskLinkSuggestions: [...material.taskLinkSuggestions] }));
  if (!meetings.value.some((meeting) => meeting.id === selectedMeetingId.value)) {
    selectedMeetingId.value = meetings.value[0]?.id ?? '';
  }
}

async function hydrateProject() {
  try {
    await uiStore.ensureProject(String(route.params.projectId), true);
    syncLocalState();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '项目详情加载失败。', 'info');
  }
}

onMounted(async () => {
  await hydrateProject();
});

watch(
  () => route.params.projectId,
  async () => {
    await hydrateProject();
  },
);

watch(
  () => project.value.updatedAt,
  () => {
    syncLocalState();
  },
  { immediate: true },
);

function visibleBlockers(meeting: MeetingRecord) {
  return meeting.blockers.filter((item) => item !== '无');
}

async function handleMeetingUpload() {
  if (isArchived.value) {
    uiStore.showToast('项目已归档，当前内容仅支持查看。', 'info');
    return;
  }

  const file = meetingInputRef.value?.files?.[0];
  if (!file) return;

  if (meetingUploadPhaseTimer) {
    clearTimeout(meetingUploadPhaseTimer);
    meetingUploadPhaseTimer = null;
  }

  meetingUploadFileName.value = file.name;
  meetingUploadState.value = 'uploading';
  uploadHint.value = '文件已提交，正在上传到后端。';
  meetingUploadPhaseTimer = setTimeout(() => {
    if (meetingUploadState.value === 'uploading') {
      meetingUploadState.value = 'analyzing';
      uploadHint.value = '后端正在解析会议内容并生成摘要、待办和风险，请稍候。';
    }
  }, 800);

  try {
    const response = await uiStore.uploadProjectMeeting(project.value.id, file);
    if (meetingUploadPhaseTimer) {
      clearTimeout(meetingUploadPhaseTimer);
      meetingUploadPhaseTimer = null;
    }
    await hydrateProject();
    selectedMeetingId.value = String(response.meeting_id);
    meetingUploadState.value = 'success';
    uploadHint.value = `已将 ${file.name} 加入会议列表，可在下方查看结构化结果。`;
    if (meetingInputRef.value) meetingInputRef.value.value = '';
  } catch (error) {
    if (meetingUploadPhaseTimer) {
      clearTimeout(meetingUploadPhaseTimer);
      meetingUploadPhaseTimer = null;
    }
    meetingUploadState.value = 'error';
    uploadHint.value = error instanceof Error ? error.message : '上传会议失败。';
  }
}

async function handleMaterialUpload() {
  if (isArchived.value) {
    uiStore.showToast('项目已归档，当前内容仅支持查看。', 'info');
    return;
  }

  const file = materialInputRef.value?.files?.[0];
  if (!materialType.value) {
    materialHintTone.value = 'error';
    materialHint.value = '请选择资料类型后再上传。';
    return;
  }
  if (!file) {
    materialHintTone.value = 'error';
    materialHint.value = '请选择要上传的资料文件。';
    return;
  }

  try {
    await uiStore.uploadProjectMaterial(project.value.id, { title: file.name, docType: materialType.value, file });
    await hydrateProject();
    materialHintTone.value = 'info';
    materialHint.value = `已将 ${file.name} 加入项目资料列表。`;
    materialType.value = '';
    if (materialInputRef.value) materialInputRef.value.value = '';
  } catch (error) {
    materialHintTone.value = 'error';
    materialHint.value = error instanceof Error ? error.message : '上传资料失败。';
  }
}

function openSuggestionModal(material: ProjectMaterial) {
  const suggestion = getPendingTaskLinkSuggestions(material)[0];
  if (!suggestion) return;
  activeMaterialId.value = material.id;
  activeSuggestionId.value = suggestion.id;
  selectedSuggestedStatus.value = suggestion.suggestedStatus;
}

function closeSuggestionModal() {
  activeMaterialId.value = null;
  activeSuggestionId.value = null;
  selectedSuggestedStatus.value = 'pending_confirmation';
}

async function handleConfirmSuggestion() {
  if (!activeMaterial.value || !activeSuggestion.value) return;
  try {
    await uiStore.confirmMaterialTaskLink(project.value.id, activeMaterial.value.id, activeSuggestion.value.id, selectedSuggestedStatus.value);
    await hydrateProject();
    closeSuggestionModal();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '确认关联失败。', 'info');
  }
}

async function handleIgnoreSuggestion() {
  if (!activeMaterial.value || !activeSuggestion.value) return;
  try {
    await uiStore.ignoreMaterialTaskLink(project.value.id, activeMaterial.value.id, activeSuggestion.value.id);
    await hydrateProject();
    closeSuggestionModal();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '忽略建议失败。', 'info');
  }
}

async function handleConfirmAction() {
  try {
    if (confirmMode.value === 'archive') {
      await uiStore.archiveProject(project.value.id);
    }

    if (confirmMode.value === 'reopen') {
      await uiStore.reopenProject(project.value.id);
    }

    await hydrateProject();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '项目状态更新失败。', 'info');
  } finally {
    confirmMode.value = null;
  }
}

async function handleExportSummary() {
  try {
    await uiStore.exportProjectSummary(project.value.id);
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '导出项目总结失败。', 'info');
  }
}
</script>
