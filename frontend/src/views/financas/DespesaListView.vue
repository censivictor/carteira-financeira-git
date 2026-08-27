<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import { exportarCsv } from '@/lib/csv'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import { Plus, LoaderCircle, Download, Upload, ArrowDownCircle, FilterX, Pencil, Trash2 } from '@lucide/vue'

const despesas = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })

// Filtro é só client-side (a lista inteira do usuário já vem numa
// chamada só, sem paginação) — mais simples e instantâneo que ir no
// servidor pra cada mudança de filtro.
const filtroDataInicio = ref('')
const filtroDataFim = ref('')
const filtroCategoria = ref('')

const categoriasDisponiveis = computed(() => {
  const porNome = new Map()
  for (const d of despesas.value) porNome.set(d.categoria_nome, d.categoria_cor)
  return [...porNome.entries()].sort((a, b) => a[0].localeCompare(b[0]))
})

const despesasFiltradas = computed(() => despesas.value.filter((d) => {
  if (filtroDataInicio.value && d.data < filtroDataInicio.value) return false
  if (filtroDataFim.value && d.data > filtroDataFim.value) return false
  if (filtroCategoria.value && d.categoria_nome !== filtroCategoria.value) return false
  return true
}))

const totalFiltrado = computed(() => despesasFiltradas.value.reduce((soma, d) => soma + Number(d.valor), 0))

const temFiltroAtivo = computed(() => !!(filtroDataInicio.value || filtroDataFim.value || filtroCategoria.value))

function limparFiltros() {
  filtroDataInicio.value = ''
  filtroDataFim.value = ''
  filtroCategoria.value = ''
}

async function carregar() {
  carregando.value = true
  despesas.value = await api.get('/financas/despesas/')
  carregando.value = false
}

function exportar() {
  const hoje = new Date().toISOString().slice(0, 10)
  exportarCsv(
    `despesas-${hoje}.csv`,
    ['Data', 'Descrição', 'Categoria', 'Valor'],
    despesasFiltradas.value.map((d) => [formatarData(d.data), d.descricao, d.categoria_nome, d.valor]),
  )
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
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">Despesas</h1>
      <div class="flex gap-2">
        <RouterLink to="/financas/importar" class="btn-secondary">
          <Upload :size="16" /> Importar extrato
        </RouterLink>
        <button type="button" class="btn-secondary" :disabled="!despesasFiltradas.length" @click="exportar">
          <Download :size="16" /> Exportar CSV
        </button>
        <RouterLink to="/financas/despesas/nova" class="btn-primary">
          <Plus :size="16" /> Nova despesa
        </RouterLink>
      </div>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <EmptyState
      v-else-if="!despesas.length"
      :icon="ArrowDownCircle"
      title="Nenhuma despesa lançada ainda"
      description="Lance manualmente ou importe um extrato em CSV pra começar a acompanhar seus gastos."
    >
      <div class="flex flex-wrap items-center justify-center gap-2">
        <RouterLink to="/financas/importar" class="btn-secondary">
          <Upload :size="16" /> Importar extrato
        </RouterLink>
        <RouterLink to="/financas/despesas/nova" class="btn-primary">
          <Plus :size="16" /> Nova despesa
        </RouterLink>
      </div>
    </EmptyState>

    <template v-else>
      <!-- Filtro: só client-side, a lista inteira já está em memória -->
      <div class="card flex flex-wrap items-end gap-3">
        <div>
          <label for="f-data-inicio" class="mb-1.5 block text-sm font-medium text-stone-700">De</label>
          <input id="f-data-inicio" v-model="filtroDataInicio" type="date" class="input" />
        </div>
        <div>
          <label for="f-data-fim" class="mb-1.5 block text-sm font-medium text-stone-700">Até</label>
          <input id="f-data-fim" v-model="filtroDataFim" type="date" class="input" />
        </div>
        <div class="min-w-[180px] flex-1">
          <label for="f-categoria" class="mb-1.5 block text-sm font-medium text-stone-700">Categoria</label>
          <select id="f-categoria" v-model="filtroCategoria" class="input">
            <option value="">Todas as categorias</option>
            <option v-for="[nome] in categoriasDisponiveis" :key="nome" :value="nome">{{ nome }}</option>
          </select>
        </div>
        <button v-if="temFiltroAtivo" type="button" class="btn-secondary" @click="limparFiltros">
          <FilterX :size="16" /> Limpar filtros
        </button>
        <span class="ml-auto text-sm text-stone-500">
          {{ despesasFiltradas.length }} {{ despesasFiltradas.length === 1 ? 'despesa' : 'despesas' }}
          <span class="font-semibold text-stone-700">· {{ formatarMoeda(totalFiltrado) }}</span>
        </span>
      </div>

      <EmptyState
        v-if="!despesasFiltradas.length"
        :icon="ArrowDownCircle"
        title="Nenhuma despesa encontrada"
        description="Nenhum lançamento bate com esse filtro. Tenta ajustar o período ou a categoria."
      >
        <button type="button" class="btn-secondary" @click="limparFiltros">
          <FilterX :size="16" /> Limpar filtros
        </button>
      </EmptyState>

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
            <tr v-for="d in despesasFiltradas" :key="d.id" class="border-b border-stone-100 last:border-0">
              <td class="py-2">{{ formatarData(d.data) }}</td>
              <td class="py-2">
                {{ d.descricao }}
                <span v-if="d.recorrente" class="ml-1 rounded-full bg-stone-100 px-2 py-0.5 text-[10px] text-stone-400">automática</span>
              </td>
              <td class="py-2">
                <span class="rounded-full px-2.5 py-0.5 text-xs font-medium text-white" :style="{ backgroundColor: d.categoria_cor }">{{ d.categoria_nome }}</span>
              </td>
              <td class="py-2 text-right pr-4">{{ formatarMoeda(d.valor) }}</td>
              <td class="py-2 text-right">
                <div class="flex items-center justify-end gap-1">
                  <RouterLink :to="`/financas/despesas/${d.id}/editar`" class="rounded-lg p-1.5 text-stone-400 transition hover:bg-stone-100 hover:text-wine" title="Editar">
                    <Pencil :size="14" />
                  </RouterLink>
                  <button type="button" class="rounded-lg p-1.5 text-stone-400 transition hover:bg-red/10 hover:text-red" title="Excluir" @click="pedirExclusao(d)">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <ConfirmDialog v-model:open="confirmExclusao.open" title="Excluir despesa?" @confirm="confirmarExclusao" />
  </div>
</template>
