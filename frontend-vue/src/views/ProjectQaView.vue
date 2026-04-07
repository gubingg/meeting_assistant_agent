<template>
  <AppShell background-class="h-screen overflow-hidden bg-[radial-gradient(circle_at_top_right,_rgba(53,82,74,0.13),_transparent_28%),linear-gradient(180deg,#f7f2e9_0%,#efe2d1_100%)]">
    <ToastBanner v-if="uiStore.toast" :message="uiStore.toast.message" :tone="uiStore.toast.tone" @close="uiStore.closeToast()" />

    <div class="flex h-[calc(100vh-2rem)] flex-col gap-4 overflow-hidden md:h-[calc(100vh-3rem)]">
      <SectionCard>
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div class="space-y-2">
            <RouterLink :to="`/projects/${project.id}`" class="inline-flex rounded-full border border-sand px-3 py-1 text-sm text-ink/70">
              返回项目详情
            </RouterLink>
            <p class="text-sm uppercase tracking-[0.3em] text-pine">答疑助手</p>
            <div class="flex items-center gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-pine text-white">
                <svg viewBox="0 0 20 20" class="h-5 w-5 fill-current" aria-hidden="true">
                  <path d="M10 2C5.582 2 2 4.91 2 8.5c0 1.91 1.015 3.628 2.633 4.82-.13 1.073-.55 2.09-1.222 2.942a.75.75 0 0 0 .854 1.174c1.646-.48 3.047-1.16 4.128-2.003.522.044 1.059.067 1.607.067 4.418 0 8-2.91 8-6.5S14.418 2 10 2Zm-3 5.5A1.5 1.5 0 1 1 7 10.5 1.5 1.5 0 0 1 7 7.5Zm3 0a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm4.5 1.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
                </svg>
              </div>
              <div>
                <h1 class="text-2xl font-semibold text-ink md:text-3xl">&lt;{{ project.name }}&gt;助手</h1>
                <p class="text-sm leading-6 text-ink/70">
                  {{ isArchived
                    ? '你正在查看归档项目，可继续追问历史会议、待办状态和项目资料。'
                    : '可以直接提问整个项目，也可以指定某次会议，例如“第一次会议 xxx 完成了吗？”' }}
                </p>
              </div>
            </div>
          </div>

          <RouterLink
            :to="`/projects/${project.id}/todos`"
            class="inline-flex items-center gap-2 rounded-2xl bg-pine px-4 py-3 text-sm font-medium text-white"
          >
            <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current" aria-hidden="true">
              <path d="M7.5 2a2 2 0 0 0-1.937 1.5H4.5A2.5 2.5 0 0 0 2 6v9.5A2.5 2.5 0 0 0 4.5 18h11a2.5 2.5 0 0 0 2.5-2.5V6a2.5 2.5 0 0 0-2.5-2.5h-1.063A2 2 0 0 0 12.5 2h-5ZM10 4a.75.75 0 1 1 0 1.5A.75.75 0 0 1 10 4Zm-2.1 5.2 1.2 1.2 3-3 1.1 1.1-4.1 4.1-2.3-2.3 1.1-1.1Zm0 4 1.2 1.2 3-3 1.1 1.1-4.1 4.1-2.3-2.3 1.1-1.1Z" />
            </svg>
            待办看板
          </RouterLink>
        </div>
      </SectionCard>

      <SectionCard class="min-h-0 flex-1">
        <div class="flex h-full min-h-0 flex-col">
          <div class="rounded-[26px] bg-paper/70 p-3 text-sm text-ink/65">
            当前覆盖范围：{{ project.meetings.length }} 次会议 / {{ project.materials.length }} 份项目资料
            <span v-if="isArchived"> · 当前项目已归档，适合继续做历史追溯。</span>
          </div>

          <div class="mt-3 min-h-0 flex-1 rounded-[26px] bg-white/80 p-4 md:p-5">
            <div ref="messagesContainerRef" class="scroll-panel flex h-full flex-col gap-3 overflow-y-auto pr-1">
              <article
                v-for="message in messages"
                :key="message.id"
                class="max-w-[94%] rounded-[22px] px-4 py-3 text-sm leading-7 shadow-sm"
                :class="message.role === 'user' ? 'ml-auto bg-pine text-white' : 'bg-paper text-ink'"
              >
                <p class="whitespace-pre-wrap">{{ message.content }}</p>
                <div v-if="message.citations?.length" class="mt-3 flex flex-wrap gap-2">
                  <span v-for="citation in message.citations" :key="citation" class="rounded-full bg-white/80 px-2.5 py-1 text-xs text-pine">
                    来源：{{ citation }}
                  </span>
                </div>
              </article>

              <div v-if="!messages.length" class="rounded-[22px] bg-paper px-4 py-3 text-sm text-ink/65">
                当前项目还没有历史提问，直接在下方输入问题即可开始和小助手对话。
              </div>
            </div>
          </div>

          <form class="mt-3 grid gap-3" @submit.prevent="handleAsk">
            <textarea v-model="question" rows="3"></textarea>

            <div class="flex items-center justify-between gap-3">
              <button type="submit" class="inline-flex items-center gap-2 rounded-2xl bg-accent px-5 py-3 text-sm font-medium text-white">
                <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current" aria-hidden="true">
                  <path d="M17.94 2.72a.75.75 0 0 0-.8-.12L2.64 8.85a.75.75 0 0 0 .07 1.41l5.62 1.87 1.87 5.62a.75.75 0 0 0 1.41.07l6.25-14.5a.75.75 0 0 0-.12-.8ZM9.6 11.46 5 9.92l9.16-3.95-3.95 9.16-1.54-4.6a.75.75 0 0 1 .18-.77l4.15-4.15-1.06-1.06-4.15 4.15a.75.75 0 0 0-.19.76Z" />
                </svg>
                发送消息
              </button>
            </div>
          </form>
        </div>
      </SectionCard>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute } from 'vue-router';

import AppShell from '@/components/AppShell.vue';
import SectionCard from '@/components/SectionCard.vue';
import ToastBanner from '@/components/ToastBanner.vue';
import { type QaMessage } from '@/data/prototype';
import { useUiStore } from '@/stores/ui';

const route = useRoute();
const uiStore = useUiStore();
const project = computed(() => uiStore.getProject(String(route.params.projectId)));
const isArchived = computed(() => project.value.status === 'archived');
const messages = ref<QaMessage[]>([]);
const question = ref('');
const messagesContainerRef = ref<HTMLDivElement | null>(null);

async function hydrateProject() {
  try {
    await uiStore.ensureProject(String(route.params.projectId), true);
    messages.value = [...project.value.qaMessages];
    await nextTick();
    scrollMessagesToBottom();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '小助手加载失败。', 'info');
  }
}

watch(
  () => project.value.updatedAt,
  () => {
    messages.value = [...project.value.qaMessages];
  },
);

watch(
  () => route.params.projectId,
  async () => {
    await hydrateProject();
  },
);

onMounted(async () => {
  await hydrateProject();
});

function scrollMessagesToBottom() {
  const container = messagesContainerRef.value;
  if (!container) return;
  container.scrollTop = container.scrollHeight;
}

async function handleAsk() {
  const trimmed = question.value.trim();
  if (!trimmed) return;

  try {
    await uiStore.askProjectQuestion(project.value.id, trimmed);
    messages.value = [...project.value.qaMessages];
    question.value = '';
    await nextTick();
    scrollMessagesToBottom();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '发送问题失败。', 'info');
  }
}
</script>
