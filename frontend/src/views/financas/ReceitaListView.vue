<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import { exportarCsv } from '@/lib/csv'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle, Download } from '@lucide/vue'

const receitas = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  receitas.value = await api.get('/financas/receitas/')
  carregando.value = false
}

function exportar() {
  const hoje = new Date().toISOString().slice(0, 10)
  exportarCsv(
    `receitas-${hoje}.csv`,
    ['Data', 'Descrição', 'Tipo', 'Valor'],
    receitas.value.map((r) => [formatarData(r.data), r.descricao, r.tipo_display, r.valor]),
  )
}

function pedirExclusao(r) {
  confirmExclusao.value = { open: true, item: r }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/financas/receitas/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">Receitas</h1>
      <div class="flex gap-2">
        <button type="button" class="btn-secondary" :disabled="!receitas.length" @click="exportar">
          <Download :size="16" /> Exportar CSV
        </button>
        <RouterLink to="/financas/receitas/nova" class="btn-primary">
          <Plus :size="16" /> Nova receita
        </RouterLink>
      </div>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[560px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Data</th>
            <th class="pb-2 font-medium">Descrição</th>
            <th class="pb-2 font-medium">Tipo</th>
            <th class="pb-2 text-right font-medium">Valor</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in receitas" :key="r.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2">{{ formatarData(r.data) }}</td>
            <td class="py-2">{{ r.descricao }}</td>
            <td class="py-2 text-stone-500">{{ r.tipo_display }}</td>
            <td class="py-2 text-right pr-4">{{ formatarMoeda(r.valor) }}</td>
            <td class="py-2 text-right">
              <RouterLink :to="`/financas/receitas/${r.id}/editar`" class="text-xs font-medium text-stone-500 hover:text-wine">Editar</RouterLink>
              <button type="button" class="ml-3 text-xs font-medium text-red hover:underline" @click="pedirExclusao(r)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!receitas.length">
            <td colspan="5" class="py-10 text-center text-stone-400">Nenhuma receita lançada ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog v-model:open="confirmExclusao.open" title="Excluir receita?" @confirm="confirmarExclusao" />
  </div>
</template>
