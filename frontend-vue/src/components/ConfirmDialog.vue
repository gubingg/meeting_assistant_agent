<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-4">
    <div class="w-full max-w-2xl rounded-[28px] border border-white/75 bg-white p-6 shadow-2xl">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-[0.28em] text-pine">Confirm</p>
          <h2 class="mt-2 text-2xl font-semibold text-ink">{{ title }}</h2>
        </div>
        <button type="button" class="rounded-full border border-sand px-3 py-1 text-sm text-ink/70" @click="$emit('cancel')">关闭</button>
      </div>

      <p class="mt-4 text-sm leading-7 text-ink/72">{{ description }}</p>

      <div class="mt-5 grid gap-3 rounded-[24px] bg-paper/70 p-4 md:grid-cols-2">
        <div class="rounded-2xl bg-white px-4 py-3 text-sm text-ink/75">
          <p class="text-xs uppercase tracking-[0.2em] text-pine">项目名称</p>
          <p class="mt-2 font-medium text-ink">{{ projectName }}</p>
        </div>
        <div class="rounded-2xl bg-white px-4 py-3 text-sm text-ink/75">
          <p class="text-xs uppercase tracking-[0.2em] text-pine">最近一次更新时间</p>
          <p class="mt-2 font-medium text-ink">{{ lastUpdatedAt }}</p>
        </div>
        <div class="rounded-2xl bg-white px-4 py-3 text-sm text-ink/75">
          <p class="text-xs uppercase tracking-[0.2em] text-pine">未完成待办数</p>
          <p class="mt-2 font-medium text-ink">{{ unfinishedTodoCount }}</p>
        </div>
        <div class="rounded-2xl bg-white px-4 py-3 text-sm text-ink/75">
          <p class="text-xs uppercase tracking-[0.2em] text-pine">未关闭风险数</p>
          <p class="mt-2 font-medium text-ink">{{ openRiskCount }}</p>
        </div>
      </div>

      <p v-if="warningText" class="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {{ warningText }}
      </p>

      <div class="mt-6 flex justify-end gap-3">
        <button type="button" class="rounded-2xl border border-sand px-4 py-2 text-sm text-ink" @click="$emit('cancel')">取消</button>
        <button
          type="button"
          class="rounded-2xl px-5 py-2 text-sm font-medium text-white"
          :class="tone === 'danger' ? 'bg-rose-600' : 'bg-pine'"
          @click="$emit('confirm')"
        >
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  projectName: string;
  lastUpdatedAt: string;
  unfinishedTodoCount: number;
  openRiskCount: number;
  warningText?: string;
  tone?: 'danger' | 'primary';
}>();

defineEmits<{
  cancel: [];
  confirm: [];
}>();
</script>
