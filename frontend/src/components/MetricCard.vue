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

const acentos = {
  gain: 'bg-emerald-500',
  loss: 'bg-red',
  neutral: 'bg-wine/30',
}
</script>

<template>
  <div class="card relative overflow-hidden">
    <div class="absolute inset-x-0 top-0 h-0.5" :class="acentos[variant]" />
    <div class="text-sm text-stone-500">{{ label }}</div>
    <div class="mt-1 text-2xl font-bold tracking-tight tabular-nums" :class="cores[variant]">{{ value }}</div>
    <div v-if="hint" class="mt-0.5 text-xs text-stone-400">{{ hint }}</div>
  </div>
</template>
