<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  variant: { type: String, default: 'neutral' }, // 'gain' | 'loss' | 'neutral'
  hint: { type: String, default: '' },
})

const cores = {
  gain: 'text-emerald-600',
  loss: 'text-red',
  neutral: 'text-stone-800',
}
</script>

<template>
  <div class="card">
    <div class="text-sm text-stone-500">{{ label }}</div>
    <div class="mt-0.5 text-xl font-bold" :class="cores[variant]">{{ value }}</div>
    <div v-if="hint" class="mt-0.5 text-xs text-stone-400">{{ hint }}</div>
  </div>
</template>
