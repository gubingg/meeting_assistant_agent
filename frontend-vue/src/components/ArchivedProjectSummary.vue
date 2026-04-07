<template>
  <div class="space-y-5">
    <section class="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Archived Summary</p>
        <h2 class="mt-2 text-3xl font-semibold text-ink">项目最终总结</h2>
        <p class="mt-4 text-base leading-8 text-ink/75">{{ project.finalSummary }}</p>
        <div class="mt-6 flex flex-wrap gap-3">
          <RouterLink :to="`/projects/${project.id}/todos`" class="rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white">查看最终待办</RouterLink>
          <RouterLink :to="`/projects/${project.id}/qa`" class="rounded-2xl border border-sand px-4 py-3 text-sm text-ink">历史追溯助手</RouterLink>
        </div>
      </SectionCard>

      <div class="grid gap-4 sm:grid-cols-2">
        <SectionCard class="min-h-[150px]">
          <p class="text-xs uppercase tracking-[0.24em] text-pine">会议总数</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.meetingCount }}</p>
          <p class="mt-2 text-sm text-ink/60">最后更新时间：{{ metrics.lastUpdatedAt }}</p>
        </SectionCard>
        <SectionCard class="min-h-[150px]">
          <p class="text-xs uppercase tracking-[0.24em] text-pine">待办收口</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.completedTodoCount }}/{{ metrics.todoCount }}</p>
          <p class="mt-2 text-sm text-ink/60">已完成 / 总待办</p>
        </SectionCard>
        <SectionCard class="min-h-[150px]">
          <p class="text-xs uppercase tracking-[0.24em] text-pine">关键决策</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.decisionCount }}</p>
          <p class="mt-2 text-sm text-ink/60">累计形成的项目结论</p>
        </SectionCard>
        <SectionCard class="min-h-[150px]">
          <p class="text-xs uppercase tracking-[0.24em] text-pine">风险收口</p>
          <p class="mt-3 text-4xl font-semibold text-ink">{{ metrics.riskCount }}</p>
          <p class="mt-2 text-sm text-ink/60">历史风险记录数</p>
        </SectionCard>
      </div>
    </section>

    <section class="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Decision Timeline</p>
        <h3 class="mt-2 text-2xl font-semibold text-ink">关键决策时间线</h3>
        <div class="mt-5 space-y-3">
          <article v-for="item in decisionTimeline" :key="item.id" class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">{{ item.startedAt }}</p>
            <p class="mt-2 text-sm font-medium text-ink">{{ item.decision }}</p>
            <p class="mt-2 text-sm text-ink/60">来源会议：{{ item.meetingTitle }}</p>
          </article>
        </div>
      </SectionCard>

      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Risk Review</p>
        <h3 class="mt-2 text-2xl font-semibold text-ink">风险收口情况</h3>
        <div class="mt-5 grid gap-3 sm:grid-cols-2">
          <div class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">未关闭风险</p>
            <p class="mt-2 text-3xl font-semibold text-ink">{{ openRiskCount }}</p>
            <p class="mt-2 text-sm text-ink/60">仍需继续追踪的风险事项</p>
          </div>
          <div class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">阻塞待办</p>
            <p class="mt-2 text-3xl font-semibold text-ink">{{ blockedTodos.length }}</p>
            <p class="mt-2 text-sm text-ink/60">归档时仍被标记为阻塞</p>
          </div>
        </div>
        <div class="mt-4 space-y-3">
          <article v-for="risk in riskTimeline" :key="risk.id" class="rounded-[22px] bg-white p-4 text-sm text-ink/75">
            <p class="font-medium text-ink">{{ risk.blocker }}</p>
            <p class="mt-2 text-ink/60">{{ risk.startedAt }} · {{ risk.meetingTitle }}</p>
          </article>
          <div v-if="!riskTimeline.length" class="rounded-[22px] bg-white p-4 text-sm text-ink/60">当前没有历史风险记录。</div>
        </div>
      </SectionCard>
    </section>

    <section class="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Todo Outcome</p>
        <h3 class="mt-2 text-2xl font-semibold text-ink">待办最终状态分布</h3>
        <div class="mt-5 grid gap-3 sm:grid-cols-2">
          <div class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">已完成</p>
            <p class="mt-2 text-3xl font-semibold text-ink">{{ metrics.completedTodoCount }}</p>
          </div>
          <div class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">未完成</p>
            <p class="mt-2 text-3xl font-semibold text-ink">{{ metrics.unfinishedTodoCount }}</p>
          </div>
          <div class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">已延期</p>
            <p class="mt-2 text-3xl font-semibold text-ink">{{ metrics.overdueTodoCount }}</p>
          </div>
          <div class="rounded-[22px] bg-paper/75 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-pine">已阻塞</p>
            <p class="mt-2 text-3xl font-semibold text-ink">{{ metrics.blockedTodoCount }}</p>
          </div>
        </div>
      </SectionCard>

      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Open Items</p>
        <h3 class="mt-2 text-2xl font-semibold text-ink">未完成事项</h3>
        <div class="mt-5 space-y-3">
          <article v-for="item in unfinishedTodos" :key="item.id" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/75">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <p class="font-medium text-ink">{{ item.task }}</p>
              <span class="rounded-full bg-white px-3 py-1 text-xs text-pine">{{ getTodoStatusLabel(item.status) }}</span>
            </div>
            <p class="mt-2">负责人：{{ item.owner }}</p>
            <p class="mt-1">截止时间：{{ item.dueDate }}</p>
            <p class="mt-1">来源会议：{{ item.meetingTitle }}</p>
            <p class="mt-1">最近一次更新会议：{{ item.lastUpdatedMeetingTitle }}</p>
          </article>
          <div v-if="!unfinishedTodos.length" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/60">这个项目归档时没有留下未完成事项。</div>
        </div>
      </SectionCard>
    </section>

    <section class="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Meetings</p>
        <h3 class="mt-2 text-2xl font-semibold text-ink">历史会议入口</h3>
        <div class="mt-5 space-y-3">
          <article v-for="meeting in orderedMeetings" :key="meeting.id" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/75">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-medium text-ink">{{ meeting.title }}</p>
                <p class="mt-2 text-ink/60">{{ meeting.startedAt }}</p>
              </div>
              <span class="rounded-full bg-white px-3 py-1 text-xs text-pine">待办 {{ meeting.actionItems.length }}</span>
            </div>
            <p class="mt-3 leading-6">{{ meeting.summary }}</p>
          </article>
        </div>
      </SectionCard>

      <SectionCard>
        <p class="text-sm uppercase tracking-[0.3em] text-pine">Materials</p>
        <h3 class="mt-2 text-2xl font-semibold text-ink">项目资料入口</h3>
        <p class="mt-3 text-sm leading-6 text-ink/65">该项目已归档，资料区仅支持查看。你仍然可以继续在小助手中追溯这些资料。</p>
        <div class="mt-5 space-y-3">
          <article v-for="material in project.materials" :key="material.id" class="rounded-[22px] bg-paper/75 p-4 text-sm text-ink/75">
            <div class="flex items-start justify-between gap-3">
              <p class="font-medium text-ink">{{ material.title }}</p>
              <span class="rounded-full bg-white px-3 py-1 text-xs text-pine">{{ getMaterialDocTypeLabel(material) }}</span>
            </div>
            <div class="mt-3 flex flex-wrap gap-2 text-xs text-ink/60">
              <span>上传时间：{{ material.updatedAt }}</span>
              <span>{{ getMaterialQaStatusLabel(material) }}</span>
            </div>
          </article>
        </div>
      </SectionCard>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';

import SectionCard from '@/components/SectionCard.vue';
import {
  getMaterialDocTypeLabel,
  getMaterialQaStatusLabel,
  getProjectDecisionTimeline,
  getProjectMetrics,
  getProjectRiskTimeline,
  getProjectTodos,
  getTodoStatusLabel,
  type ProjectRecord,
} from '@/data/prototype';

const props = defineProps<{
  project: ProjectRecord;
}>();

const metrics = computed(() => getProjectMetrics(props.project));
const decisionTimeline = computed(() => getProjectDecisionTimeline(props.project));
const riskTimeline = computed(() => getProjectRiskTimeline(props.project));
const todos = computed(() => getProjectTodos(props.project));
const unfinishedTodos = computed(() => todos.value.filter((item) => item.status !== 'done'));
const blockedTodos = computed(() => todos.value.filter((item) => item.isBlocked));
const openRiskCount = computed(() => Math.max(metrics.value.blockedTodoCount, metrics.value.unfinishedTodoCount > 0 ? riskTimeline.value.length : 0));
const orderedMeetings = computed(() => [...props.project.meetings].sort((a, b) => b.startedAt.localeCompare(a.startedAt)));
</script>
