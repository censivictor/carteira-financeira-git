<script setup>
defineProps({
  icon: { type: [Object, Function], required: true },
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="card flex flex-col items-center gap-3 py-14 text-center">
    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-coral/15 text-wine">
      <component :is="icon" :size="22" />
    </div>
    <div>
      <h3 class="text-sm font-semibold text-stone-700">{{ title }}</h3>
      <p v-if="description" class="mt-1 max-w-xs text-sm text-stone-400">{{ description }}</p>
    </div>
    <div v-if="$slots.default" class="mt-1">
      <slot />
    </div>
  </div>
</template>
