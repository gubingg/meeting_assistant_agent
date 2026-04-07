<template>
  <main :class="backgroundClass">
    <div class="mx-auto max-w-[1600px] p-4 md:p-6">
      <slot />
    </div>
  </main>
</template>

<script setup lang="ts">
defineProps<{
  backgroundClass?: string;
}>();
</script>
