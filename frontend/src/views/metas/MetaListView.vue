<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle, Trophy } from '@lucide/vue'

const metas = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  metas.value = await api.get('/metas/')
  carregando.value = false
}

function pedirExclusao(m) {
  confirmExclusao.value = { open: true, item: m }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/metas/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-stone-800">Metas financeiras</h1>
      <RouterLink to="/metas/nova" class="btn-primary">
        <Plus :size="16" /> Nova meta
      </RouterLink>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink v-for="m in metas" :key="m.id" :to="`/metas/${m.id}`" class="card block transition hover:border-wine/40 hover:shadow-md">
        <div class="flex items-start justify-between">
          <h3 class="font-semibold text-stone-800">{{ m.nome }}</h3>
          <button type="button" class="text-xs font-medium text-red hover:underline" @click.prevent="pedirExclusao(m)">Excluir</button>
        </div>
        <div v-if="m.data_alvo" class="mt-1 text-xs text-stone-400">até {{ formatarData(m.data_alvo) }}</div>

        <div class="mt-3 flex items-center justify-between text-sm">
          <span class="font-medium text-stone-700">{{ formatarMoeda(m.valor_atual) }}</span>
          <span class="text-stone-400">de {{ formatarMoeda(m.valor_alvo) }}</span>
        </div>
        <div class="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-stone-100">
          <div class="h-full rounded-full transition-all" :class="m.concluida ? 'bg-emerald-500' : 'bg-wine'" :style="{ width: m.pct + '%' }" />
        </div>
        <div class="mt-1.5 flex items-center gap-1 text-xs" :class="m.concluida ? 'text-emerald-600' : 'text-stone-400'">
          <Trophy v-if="m.concluida" :size="12" />
          {{ m.pct.toFixed(0) }}%{{ m.concluida ? ' — concluída!' : '' }}
        </div>
      </RouterLink>
      <div v-if="!metas.length" class="card col-span-full py-10 text-center text-stone-400">
        Nenhuma meta cadastrada ainda.
      </div>
    </div>

    <ConfirmDialog
      v-model:open="confirmExclusao.open"
      :title="`Excluir ${confirmExclusao.item?.nome}?`"
      description="O histórico de aportes e retiradas dessa meta também é apagado."
      @confirm="confirmarExclusao"
    />
  </div>
</template>
