<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarMoedaPrecisa, formatarData } from '@/lib/format'

// Cripto barata tem preço médio na casa de frações de centavo — formatarMoeda
// arredondaria pra "R$ 0,00", sem sentido.
function formatarPreco(valor, tipo) {
  return tipo === 'CRIPTO' ? formatarMoedaPrecisa(valor) : formatarMoeda(valor)
}
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import { Plus, LoaderCircle, Target, Wallet, Pencil, Trash2 } from '@lucide/vue'

const ativos = ref([])
const carregando = ref(true)
// `open` fica separado do item alvo — ver comentário em AtivoDetailView.vue
// sobre a corrida entre o fechamento automático do AlertDialogAction e o
// handler de confirmação.
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  ativos.value = await api.get('/investimentos/ativos/')
  carregando.value = false
}

function pedirExclusao(ativo) {
  confirmExclusao.value = { open: true, item: ativo }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/investimentos/ativos/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">Investimentos</h1>
      <div class="flex gap-2">
        <RouterLink to="/investimentos/alocacao" class="btn-secondary">
          <Target :size="16" /> Alocação-alvo
        </RouterLink>
        <RouterLink to="/investimentos/novo" class="btn-primary">
          <Plus :size="16" /> Novo ativo
        </RouterLink>
      </div>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <EmptyState
      v-else-if="!ativos.length"
      :icon="Wallet"
      title="Nenhum ativo cadastrado ainda"
      description="Cadastre suas ações, FIIs, cripto ou renda fixa pra acompanhar a carteira aqui."
    >
      <RouterLink to="/investimentos/novo" class="btn-primary">
        <Plus :size="16" /> Novo ativo
      </RouterLink>
    </EmptyState>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[720px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Ticker</th>
            <th class="pb-2 font-medium">Nome</th>
            <th class="pb-2 font-medium">Tipo</th>
            <th class="pb-2 text-right font-medium">Quantidade / Indexador</th>
            <th class="pb-2 text-right font-medium">Preço médio / Aplicado desde</th>
            <th class="pb-2 text-right font-medium">Valor investido</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in ativos" :key="a.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2 font-medium text-wine">
              <RouterLink v-if="a.tipo !== 'RENDA_FIXA'" :to="`/investimentos/${a.id}`" class="hover:underline">
                {{ a.ticker }}
              </RouterLink>
              <span v-else>{{ a.ticker }}</span>
            </td>
            <td class="py-2 text-stone-500">{{ a.nome || '—' }}</td>
            <td class="py-2 text-stone-500">{{ a.tipo_display }}</td>
            <template v-if="a.tipo === 'RENDA_FIXA'">
              <td class="py-2 text-right text-stone-700">{{ a.indexador_display }} · {{ a.taxa_contratada }}%</td>
              <td class="py-2 text-right text-stone-700">desde {{ formatarData(a.data_aplicacao) }}</td>
            </template>
            <template v-else>
              <td class="py-2 text-right text-stone-700">{{ a.quantidade }}</td>
              <td class="py-2 text-right text-stone-700">{{ formatarPreco(a.preco_medio_compra, a.tipo) }}</td>
            </template>
            <td class="py-2 text-right text-stone-700">{{ formatarMoeda(a.valor_investido) }}</td>
            <td class="py-2 text-right">
              <div class="flex items-center justify-end gap-1">
                <RouterLink :to="`/investimentos/${a.id}/editar`" class="rounded-lg p-1.5 text-stone-400 transition hover:bg-stone-100 hover:text-wine" title="Editar">
                  <Pencil :size="14" />
                </RouterLink>
                <button type="button" class="rounded-lg p-1.5 text-stone-400 transition hover:bg-red/10 hover:text-red" title="Excluir" @click="pedirExclusao(a)">
                  <Trash2 :size="14" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog
      v-model:open="confirmExclusao.open"
      :title="`Excluir ${confirmExclusao.item?.ticker}?`"
      description="Isso também apaga as transações e proventos ligados a esse ativo."
      @confirm="confirmarExclusao"
    />
  </div>
</template>
