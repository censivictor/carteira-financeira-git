<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle } from '@lucide/vue'

const despesas = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  despesas.value = await api.get('/financas/despesas/')
  carregando.value = false
}

function pedirExclusao(d) {
  confirmExclusao.value = { open: true, item: d }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/financas/despesas/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-stone-800">Despesas</h1>
      <RouterLink to="/financas/despesas/nova" class="btn-primary">
        <Plus :size="16" /> Nova despesa
      </RouterLink>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[600px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Data</th>
            <th class="pb-2 font-medium">Descrição</th>
            <th class="pb-2 font-medium">Categoria</th>
            <th class="pb-2 text-right font-medium">Valor</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in despesas" :key="d.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2.5">{{ formatarData(d.data) }}</td>
            <td class="py-2.5">
              {{ d.descricao }}
              <span v-if="d.recorrente" class="ml-1 rounded-full bg-stone-100 px-2 py-0.5 text-[10px] text-stone-400">automática</span>
            </td>
            <td class="py-2.5">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium text-white" :style="{ backgroundColor: d.categoria_cor }">{{ d.categoria_nome }}</span>
            </td>
            <td class="py-2.5 text-right pr-4">{{ formatarMoeda(d.valor) }}</td>
            <td class="py-2.5 text-right">
              <RouterLink :to="`/financas/despesas/${d.id}/editar`" class="text-xs font-medium text-stone-500 hover:text-wine">Editar</RouterLink>
              <button type="button" class="ml-3 text-xs font-medium text-red hover:underline" @click="pedirExclusao(d)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!despesas.length">
            <td colspan="5" class="py-10 text-center text-stone-400">Nenhuma despesa lançada ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog v-model:open="confirmExclusao.open" title="Excluir despesa?" @confirm="confirmarExclusao" />
  </div>
</template>
