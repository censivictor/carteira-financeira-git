<script setup>
defineProps({
  title: { type: String, required: true },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: 'Sem dados ainda.' },
})
</script>

<template>
  <div class="card">
    <h3 class="mb-2 text-sm font-semibold text-stone-700">{{ title }}</h3>
    <div v-if="empty" class="py-8 text-center text-sm text-stone-400">
      {{ emptyText }}
      <slot name="empty-link" />
    </div>
    <div v-else class="h-56">
      <slot />
    </div>
  </div>
</template>
