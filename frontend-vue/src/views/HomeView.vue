<template>
  <AppShell background-class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(201,111,59,0.16),_transparent_28%),linear-gradient(180deg,#f8f3ea_0%,#efe4d6_100%)]">
    <ToastBanner v-if="uiStore.toast" :message="uiStore.toast.message" :tone="uiStore.toast.tone" @close="uiStore.closeToast()" />

    <div class="flex flex-col gap-5">
      <SectionCard>
        <div class="grid gap-4 lg:grid-cols-[1.9fr_240px] lg:items-start">
          <div class="space-y-4">
            <p class="text-xs uppercase tracking-[0.32em] text-pine">Meeting Assistant · Vue 3</p>
            <div class="space-y-2">
              <h1 class="max-w-5xl text-[1.85rem] font-semibold leading-tight text-ink md:text-[2.35rem]">
                项目会议管理助手
              </h1>
              <p class="max-w-4xl text-sm leading-7 text-ink/72">
                将多轮会议中的结论、待办和资料统一沉淀到项目中，帮助你更快查看进展与后续动作。
              </p>
            </div>

            <div class="flex flex-wrap gap-3">
              <button
                class="inline-flex items-center gap-2 rounded-2xl bg-accent px-5 py-3 text-sm font-medium text-white shadow-lg shadow-accent/20"
                @click="uiStore.openCreateModal()"
              >
                <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current" aria-hidden="true">
                  <path d="M9 4h2v5h5v2h-5v5H9v-5H4V9h5V4Z" />
                </svg>
                添加项目
              </button>
            </div>

            <div class="flex flex-wrap gap-3 pt-1">
              <button v-for="item in filters" :key="item.value" type="button" class="rounded-2xl px-4 py-2 text-sm transition" :class="selectedFilter === item.value ? 'bg-pine text-white' : 'bg-paper/80 text-ink/75'" @click="selectedFilter = item.value">
                {{ item.label }}
              </button>
            </div>
          </div>

          <div class="rounded-[28px] bg-paper/75 p-4">
            <div class="rounded-2xl bg-white p-4 shadow-sm">
              <p class="text-sm text-ink/55">项目数量</p>
              <p class="mt-1 text-4xl font-semibold text-ink">{{ filteredProjects.length }}</p>
              <p class="mt-2 text-sm leading-6 text-ink/60">进行中 {{ activeCount }} / 已归档 {{ archivedCount }}</p>
            </div>
          </div>
        </div>
      </SectionCard>

      <section class="flex flex-col gap-3">
        <div class="flex items-end justify-between gap-3">
          <div>
            <p class="text-sm uppercase tracking-[0.3em] text-pine">Projects</p>
            <h2 class="mt-1 text-2xl font-semibold text-ink">已有项目</h2>
          </div>
          <p class="text-sm text-ink/58">进行中项目默认靠前，已归档项目会放到后面。</p>
        </div>

        <div v-if="uiStore.isHydrating && !filteredProjects.length" class="rounded-[28px] bg-white/75 p-6 text-sm text-ink/65">
          正在加载项目列表...
        </div>

        <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <article
            v-for="project in filteredProjects"
            :key="project.id"
            class="flex min-h-[340px] flex-col rounded-[28px] border p-6 shadow-soft transition"
            :class="project.status === 'archived' ? 'border-slate-200 bg-white/72 opacity-90' : 'border-white/70 bg-white/88'"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full px-3 py-1 text-xs" :class="project.status === 'archived' ? 'bg-slate-200 text-slate-700' : 'bg-emerald-100 text-emerald-700'">
                    {{ project.status === 'archived' ? '已归档' : '进行中' }}
                  </span>
                  <span class="text-xs text-ink/45">{{ project.stage }}</span>
                </div>
                <h3 class="mt-3 text-2xl font-semibold text-ink">{{ project.name }}</h3>
              </div>

              <ProjectCardMenu
                :archived="project.status === 'archived'"
                @view="router.push(`/projects/${project.id}`)"
                @export="uiStore.exportProjectSummary(project.id)"
                @archive="openArchiveDialog(project.id)"
              />
            </div>

            <p class="mt-4 flex-1 overflow-hidden text-sm leading-7 text-ink/72 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]">
              {{ project.summary }}
            </p>

            <dl class="mt-5 space-y-2 text-sm text-ink/70">
              <div class="flex items-center justify-between gap-3"><dt>负责人</dt><dd>{{ project.owner }}</dd></div>
              <div class="flex items-center justify-between gap-3"><dt>开始时间</dt><dd>{{ project.startTime }}</dd></div>
              <div class="flex items-center justify-between gap-3"><dt>最后更新时间</dt><dd>{{ project.updatedAt }}</dd></div>
              <template v-if="project.status === 'archived'">
                <div class="flex items-center justify-between gap-3"><dt>归档时间</dt><dd>{{ project.archivedAt }}</dd></div>
                <div class="flex items-center justify-between gap-3"><dt>会议数 / 待办数</dt><dd>{{ getProjectMetrics(project).meetingCount }} / {{ getProjectMetrics(project).todoCount }}</dd></div>
                <div class="flex items-center justify-between gap-3"><dt>未完成待办数</dt><dd>{{ getProjectMetrics(project).unfinishedTodoCount }}</dd></div>
              </template>
              <template v-else>
                <div class="flex items-center justify-between gap-3"><dt>最近会议</dt><dd>{{ project.latestMeetingAt }}</dd></div>
                <div class="flex items-center justify-between gap-3"><dt>待办数量</dt><dd>{{ getProjectMetrics(project).todoCount }}</dd></div>
              </template>
            </dl>

            <div class="mt-6 flex gap-3">
              <RouterLink
                :to="`/projects/${project.id}`"
                class="inline-flex flex-1 items-center justify-center rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white"
              >
                {{ project.status === 'archived' ? '查看总结' : '进入项目' }}
              </RouterLink>

              <RouterLink
                :to="`/projects/${project.id}/qa`"
                class="inline-flex items-center justify-center gap-2 rounded-2xl border border-sand px-4 py-3 text-sm text-ink"
              >
                <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current text-pine" aria-hidden="true">
                  <path d="M10 2C5.582 2 2 4.91 2 8.5c0 1.91 1.015 3.628 2.633 4.82-.13 1.073-.55 2.09-1.222 2.942a.75.75 0 0 0 .854 1.174c1.646-.48 3.047-1.16 4.128-2.003.522.044 1.059.067 1.607.067 4.418 0 8-2.91 8-6.5S14.418 2 10 2Zm-3 5.5A1.5 1.5 0 1 1 7 10.5 1.5 1.5 0 0 1 7 7.5Zm3 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm4.5 1.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
                </svg>
                答疑助手
              </RouterLink>
            </div>
          </article>
        </div>
      </section>
    </div>

    <ConfirmDialog
      :open="Boolean(confirmProject)"
      title="归档项目"
      description="归档后，项目会进入只读状态。你仍然可以查看历史会议、待办、项目资料和问答记录，但无法继续上传新会议、更新待办或新增资料。"
      confirm-label="确认归档"
      :project-name="confirmProject?.name ?? ''"
      :last-updated-at="confirmMetrics?.lastUpdatedAt ?? ''"
      :unfinished-todo-count="confirmMetrics?.unfinishedTodoCount ?? 0"
      :open-risk-count="confirmMetrics?.riskCount ?? 0"
      :warning-text="confirmMetrics && confirmMetrics.unfinishedTodoCount > 0 ? `当前仍有 ${confirmMetrics.unfinishedTodoCount} 条未完成待办。` : ''"
      tone="danger"
      @cancel="confirmTargetId = null"
      @confirm="confirmArchive"
    />

    <div v-if="uiStore.isCreateModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-4">
      <div class="w-full max-w-2xl rounded-[28px] border border-white/70 bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm uppercase tracking-[0.3em] text-pine">Create Project</p>
            <h2 class="mt-2 text-2xl font-semibold text-ink">添加项目</h2>
          </div>
          <button class="rounded-full border border-sand px-3 py-1 text-sm text-ink/70" @click="uiStore.closeCreateModal()">
            关闭
          </button>
        </div>

        <form class="mt-6 grid gap-4" @submit.prevent="handleCreateProject">
          <input v-model="form.name" placeholder="项目名称" required />
          <div class="grid gap-2">
            <textarea v-model="form.summary" rows="4" maxlength="48" placeholder="项目背景 / 需求简介" required></textarea>
            <p class="text-right text-xs text-ink/50">{{ form.summary.length }}/48</p>
          </div>
          <div class="grid gap-4 md:grid-cols-2">
            <input v-model="form.owner" placeholder="负责人" required />
            <input v-model="form.startTime" type="date" />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="rounded-2xl border border-sand px-4 py-2 text-sm text-ink" @click="uiStore.closeCreateModal()">
              取消
            </button>
            <button type="submit" class="rounded-2xl bg-accent px-5 py-2 text-sm font-medium text-white">
              创建并进入详情
            </button>
          </div>
        </form>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import AppShell from '@/components/AppShell.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import ProjectCardMenu from '@/components/ProjectCardMenu.vue';
import SectionCard from '@/components/SectionCard.vue';
import ToastBanner from '@/components/ToastBanner.vue';
import { getProjectMetrics } from '@/data/prototype';
import { useUiStore } from '@/stores/ui';

const router = useRouter();
const uiStore = useUiStore();

const form = reactive({
  name: '',
  summary: '',
  owner: '',
  startTime: '',
});

const filters = [
  { value: 'all', label: '全部' },
  { value: 'active', label: '进行中' },
  { value: 'archived', label: '已归档' },
] as const;

const selectedFilter = ref<(typeof filters)[number]['value']>('all');
const confirmTargetId = ref<string | null>(null);

const sortedProjects = computed(() =>
  [...uiStore.projects].sort((a, b) => {
    if (a.status !== b.status) return a.status === 'active' ? -1 : 1;
    return b.updatedAt.localeCompare(a.updatedAt);
  }),
);

const filteredProjects = computed(() => {
  if (selectedFilter.value === 'all') return sortedProjects.value;
  return sortedProjects.value.filter((project) => project.status === selectedFilter.value);
});

const activeCount = computed(() => uiStore.activeProjects.length);
const archivedCount = computed(() => uiStore.archivedProjects.length);
const confirmProject = computed(() => (confirmTargetId.value ? uiStore.getProject(confirmTargetId.value) : null));
const confirmMetrics = computed(() => (confirmProject.value ? getProjectMetrics(confirmProject.value) : null));

onMounted(async () => {
  try {
    await uiStore.initialize();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '项目列表加载失败。', 'info');
  }
});

async function handleCreateProject() {
  if (!form.name.trim() || !form.summary.trim() || !form.owner.trim()) return;

  try {
    const project = await uiStore.addProject({
      name: form.name.trim(),
      summary: form.summary.trim(),
      owner: form.owner.trim(),
      startTime: form.startTime.trim(),
    });

    form.name = '';
    form.summary = '';
    form.owner = '';
    form.startTime = '';

    router.push(`/projects/${project.id}`);
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '创建项目失败。', 'info');
  }
}

function openArchiveDialog(projectId: string) {
  confirmTargetId.value = projectId;
}

async function confirmArchive() {
  if (!confirmTargetId.value) return;
  try {
    await uiStore.archiveProject(confirmTargetId.value);
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '归档项目失败。', 'info');
  } finally {
    confirmTargetId.value = null;
  }
}
</script>
