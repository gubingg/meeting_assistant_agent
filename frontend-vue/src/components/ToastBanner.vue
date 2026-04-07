<template>
  <div class="fixed right-4 top-4 z-50 flex w-full max-w-sm items-start gap-3 rounded-[24px] border border-white/80 px-4 py-3 shadow-2xl shadow-ink/10" :class="toneClass">
    <div class="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-white/80">
      <svg v-if="tone === 'success'" viewBox="0 0 20 20" class="h-4 w-4 fill-current text-emerald-600" aria-hidden="true">
        <path d="M10 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16Zm3.78-10.53-4.53 4.97-2.97-2.59-1.06 1.22 4.08 3.56 5.66-6.2-1.18-.96Z" />
      </svg>
      <svg v-else viewBox="0 0 20 20" class="h-4 w-4 fill-current text-pine" aria-hidden="true">
        <path d="M10 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16Zm-.75-10.5v5h1.5v-5h-1.5Zm0 6.5v1.5h1.5V14h-1.5Z" />
      </svg>
    </div>
    <div class="min-w-0 flex-1 text-sm leading-6 text-ink">
      {{ message }}
    </div>
    <button type="button" class="rounded-full px-2 py-1 text-sm text-ink/50" @click="$emit('close')">×</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  message: string;
  tone?: 'success' | 'info';
}>();

defineEmits<{
  close: [];
}>();

const toneClass = computed(() =>
  props.tone === 'success'
    ? 'bg-emerald-50/95'
    : 'bg-paper/95',
);
</script>
