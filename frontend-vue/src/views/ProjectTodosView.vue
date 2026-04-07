<template>
  <AppShell background-class="min-h-screen bg-[linear-gradient(180deg,#f8f3ea_0%,#efe5d7_100%)]">
    <ToastBanner v-if="uiStore.toast" :message="uiStore.toast.message" :tone="uiStore.toast.tone" @close="uiStore.closeToast()" />

    <div class="space-y-6">
      <SectionCard>
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <RouterLink :to="`/projects/${project.id}`" class="rounded-full border border-sand px-3 py-1 text-sm text-ink/70">返回项目详情</RouterLink>
            <p class="mt-4 text-sm uppercase tracking-[0.3em] text-pine">Todos</p>
            <h1 class="mt-2 text-3xl font-semibold text-ink">&lt;{{ project.name }}&gt;待办总览</h1>
            <p class="mt-3 max-w-3xl text-sm leading-7 text-ink/70">
              {{ isArchived
                ? '项目已归档，这里用于回看最终推进结果。你可以按完成情况、延期和阻塞状态筛选，快速看清项目收口状态。'
                : '按状态查看整个项目的待办项，保留负责人、截止时间和来源会议。' }}
            </p>
          </div>
          <RouterLink :to="`/projects/${project.id}/qa`" class="inline-flex items-center justify-center rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white">
            去答疑助手
          </RouterLink>
        </div>
      </SectionCard>

      <SectionCard v-if="isArchived" class="border border-slate-200 bg-slate-50/85">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-sm font-medium text-ink">已归档项目只支持查看</p>
            <p class="mt-1 text-sm text-ink/65">你仍然可以查看待办的最终状态、来源会议和最近一次更新会议。</p>
          </div>
          <span class="rounded-full bg-slate-200 px-3 py-1 text-sm text-slate-700">归档时间：{{ project.archivedAt }}</span>
        </div>
      </SectionCard>

      <div class="grid gap-4 md:grid-cols-4">
        <SectionCard>
          <p class="text-xs uppercase tracking-[0.2em] text-pine">待办总数</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.todoCount }}</p>
        </SectionCard>
        <SectionCard>
          <p class="text-xs uppercase tracking-[0.2em] text-pine">已完成</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.completedTodoCount }}</p>
        </SectionCard>
        <SectionCard>
          <p class="text-xs uppercase tracking-[0.2em] text-pine">未完成</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.unfinishedTodoCount }}</p>
        </SectionCard>
        <SectionCard>
          <p class="text-xs uppercase tracking-[0.2em] text-pine">延期 / 阻塞</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.overdueTodoCount }} / {{ metrics.blockedTodoCount }}</p>
        </SectionCard>
      </div>

      <SectionCard>
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.3em] text-pine">Filters</p>
            <h2 class="mt-2 text-2xl font-semibold text-ink">待办筛选</h2>
          </div>
          <div class="flex flex-wrap gap-3">
            <button
              v-for="item in filterOptions"
              :key="item.value"
              type="button"
              class="rounded-2xl px-4 py-2 text-sm transition"
              :class="selectedFilter === item.value ? 'bg-pine text-white' : 'bg-paper text-ink/75'"
              @click="selectedFilter = item.value"
            >
              {{ item.label }}
            </button>
          </div>
        </div>

        <div class="mt-5 space-y-3">
          <article v-for="item in filteredTodos" :key="item.id" class="rounded-[24px] bg-paper/75 p-5 text-sm text-ink/75">
            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p class="text-lg font-medium text-ink">{{ item.task }}</p>
                <div class="mt-3 flex flex-wrap gap-2 text-xs text-ink/60">
                  <span>负责人：{{ item.owner }}</span>
                  <span>截止时间：{{ item.dueDate }}</span>
                  <span>来源会议：{{ item.meetingTitle }}</span>
                  <span>最近一次更新会议：{{ item.lastUpdatedMeetingTitle }}</span>
                </div>
              </div>
              <div class="flex flex-wrap gap-2">
                <span class="rounded-full bg-white px-3 py-1 text-xs text-pine">{{ getTodoStatusLabel(item.status) }}</span>
                <span v-if="item.isOverdue" class="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-700">已延期</span>
                <span v-if="item.isBlocked" class="rounded-full bg-rose-100 px-3 py-1 text-xs text-rose-700">已阻塞</span>
              </div>
            </div>
          </article>

          <div v-if="!filteredTodos.length" class="rounded-[24px] bg-paper/75 p-5 text-sm text-ink/60">当前筛选条件下没有待办项。</div>
        </div>
      </SectionCard>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import AppShell from '@/components/AppShell.vue';
import SectionCard from '@/components/SectionCard.vue';
import ToastBanner from '@/components/ToastBanner.vue';
import { getProjectMetrics, getProjectTodos, getTodoStatusLabel } from '@/data/prototype';
import { useUiStore } from '@/stores/ui';

const route = useRoute();
const uiStore = useUiStore();
const project = computed(() => uiStore.getProject(String(route.params.projectId)));
const isArchived = computed(() => project.value.status === 'archived');
const todos = computed(() => getProjectTodos(project.value));
const metrics = computed(() => getProjectMetrics(project.value));

const selectedFilter = ref('all');

const filterOptions = computed(() =>
  isArchived.value
    ? [
        { value: 'all', label: '全部' },
        { value: 'done', label: '已完成' },
        { value: 'unfinished', label: '未完成' },
        { value: 'overdue', label: '已延期' },
        { value: 'blocked', label: '已阻塞' },
      ]
    : [
        { value: 'all', label: '全部' },
        { value: 'todo', label: '未开始' },
        { value: 'doing', label: '进行中' },
        { value: 'pending_confirmation', label: '待确认' },
        { value: 'done', label: '已完成' },
      ],
);

onMounted(async () => {
  try {
    await uiStore.ensureProject(String(route.params.projectId), true);
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '待办页加载失败。', 'info');
  }
});

watch(
  () => route.params.projectId,
  async () => {
    try {
      await uiStore.ensureProject(String(route.params.projectId), true);
    } catch (error) {
      uiStore.showToast(error instanceof Error ? error.message : '待办页加载失败。', 'info');
    }
  },
);

const filteredTodos = computed(() => {
  const source = [...todos.value].sort((a, b) => a.dueDate.localeCompare(b.dueDate));

  switch (selectedFilter.value) {
    case 'todo':
      return source.filter((item) => item.status === 'todo');
    case 'doing':
      return source.filter((item) => item.status === 'doing');
    case 'pending_confirmation':
      return source.filter((item) => item.status === 'pending_confirmation');
    case 'done':
      return source.filter((item) => item.status === 'done');
    case 'unfinished':
      return source.filter((item) => item.status !== 'done');
    case 'overdue':
      return source.filter((item) => item.isOverdue);
    case 'blocked':
      return source.filter((item) => item.isBlocked);
    default:
      return source;
  }
});
</script>
