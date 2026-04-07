<template>
  <RouterView />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { RouterView } from 'vue-router';

import { useUiStore } from '@/stores/ui';

const uiStore = useUiStore();

onMounted(async () => {
  try {
    await uiStore.initialize();
  } catch (error) {
    uiStore.showToast(error instanceof Error ? error.message : '项目列表加载失败。', 'info');
  }
});
</script>
