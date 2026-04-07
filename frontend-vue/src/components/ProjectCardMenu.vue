<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      class="flex h-10 w-10 items-center justify-center rounded-2xl border border-sand bg-white/90 text-ink/70 transition hover:border-pine hover:text-pine"
      @click.stop="open = !open"
    >
      <svg viewBox="0 0 20 20" class="h-4 w-4 fill-current" aria-hidden="true">
        <path d="M4.75 8.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm5.25 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm5.25 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z" />
      </svg>
    </button>

    <div v-if="open" class="absolute right-0 top-12 z-30 w-44 rounded-2xl border border-white/80 bg-white p-2 shadow-2xl shadow-ink/10">
      <button type="button" class="menu-item" @click="emitView">查看项目</button>
      <button type="button" class="menu-item" @click="emitExport">导出项目总结</button>
      <button v-if="!archived" type="button" class="menu-item text-rose-600" @click="emitArchive">归档项目</button>
      <div v-else class="rounded-xl px-3 py-2 text-sm text-ink/45">项目已归档</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

defineProps<{
  archived: boolean;
}>();

const emit = defineEmits<{
  view: [];
  export: [];
  archive: [];
}>();

const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);

function emitView() {
  open.value = false;
  emit('view');
}

function emitExport() {
  open.value = false;
  emit('export');
}

function emitArchive() {
  open.value = false;
  emit('archive');
}

function onDocumentClick(event: MouseEvent) {
  const root = rootRef.value;
  if (!root) return;
  if (!root.contains(event.target as Node)) {
    open.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
});
</script>

<style scoped>
.menu-item {
  width: 100%;
  border-radius: 0.85rem;
  padding: 0.65rem 0.75rem;
  text-align: left;
  font-size: 0.92rem;
  color: #10212b;
}

.menu-item:hover {
  background: rgba(239, 229, 215, 0.7);
}
</style>
