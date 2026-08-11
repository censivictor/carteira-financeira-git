<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle } from '@lucide/vue'

const recorrentes = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  recorrentes.value = await api.get('/financas/recorrentes/')
  carregando.value = false
}

function pedirExclusao(r) {
  confirmExclusao.value = { open: true, item: r }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/financas/recorrentes/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-stone-800">Despesas recorrentes</h1>
      <RouterLink to="/financas/recorrentes/nova" class="btn-primary">
        <Plus :size="16" /> Nova recorrência
      </RouterLink>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[620px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Descrição</th>
            <th class="pb-2 font-medium">Categoria</th>
            <th class="pb-2 text-right font-medium">Valor</th>
            <th class="pb-2 pr-4 text-right font-medium">Dia do mês</th>
            <th class="pb-2 font-medium">Status</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in recorrentes" :key="r.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2.5">{{ r.descricao }}</td>
            <td class="py-2.5 text-stone-500">{{ r.categoria_nome }}</td>
            <td class="py-2.5 text-right pr-4">{{ formatarMoeda(r.valor) }}</td>
            <td class="py-2.5 text-right pr-4">{{ r.dia_do_mes }}</td>
            <td class="py-2.5">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="r.ativa ? 'bg-emerald-100 text-emerald-700' : 'bg-stone-100 text-stone-500'">
                {{ r.ativa ? 'Ativa' : 'Pausada' }}
              </span>
            </td>
            <td class="py-2.5 text-right">
              <RouterLink :to="`/financas/recorrentes/${r.id}/editar`" class="text-xs font-medium text-stone-500 hover:text-wine">Editar</RouterLink>
              <button type="button" class="ml-3 text-xs font-medium text-red hover:underline" @click="pedirExclusao(r)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!recorrentes.length">
            <td colspan="6" class="py-10 text-center text-stone-400">Nenhuma despesa recorrente cadastrada ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog v-model:open="confirmExclusao.open" title="Excluir despesa recorrente?" description="As despesas já geradas por ela não são apagadas." @confirm="confirmarExclusao" />
  </div>
</template>
