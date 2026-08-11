<script setup>
const props = defineProps({
  categoria: { type: String, required: true },
  total: { type: Number, required: true },
  orcamento: { type: Number, required: true },
  pct: { type: Number, required: true },
})

const corBarra = () => {
  if (props.pct >= 100) return 'bg-red'
  if (props.pct >= 80) return 'bg-peach'
  return 'bg-emerald-500'
}

const formatarMoeda = (v) => v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
</script>

<template>
  <div class="mb-3 last:mb-0">
    <div class="mb-1 flex items-center justify-between text-sm">
      <span class="font-medium text-stone-700">{{ categoria }}</span>
      <span class="text-stone-500">R$ {{ formatarMoeda(total) }} de R$ {{ formatarMoeda(orcamento) }} ({{ pct.toFixed(0) }}%)</span>
    </div>
    <div class="h-2 w-full overflow-hidden rounded-full bg-stone-100">
      <div class="h-full rounded-full transition-all" :class="corBarra()" :style="{ width: Math.min(pct, 100) + '%' }" />
    </div>
  </div>
</template>
