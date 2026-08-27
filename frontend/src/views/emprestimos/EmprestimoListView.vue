<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EmptyState from '@/components/EmptyState.vue'
import { Plus, LoaderCircle, Landmark, Banknote, Pencil, Trash2 } from '@lucide/vue'

const emprestimos = ref([])
const carregando = ref(true)
// `open` fica separado do item alvo — ver comentário em AtivoDetailView.vue
// sobre a corrida entre o fechamento automático do AlertDialogAction e o
// handler de confirmação.
const confirmExclusao = ref({ open: false, item: null })
const confirmPagamento = ref({ open: false, item: null })
const erroPagamento = ref('')

async function carregar() {
  carregando.value = true
  emprestimos.value = await api.get('/emprestimos/')
  carregando.value = false
}

function pedirExclusao(e) {
  confirmExclusao.value = { open: true, item: e }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/emprestimos/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

function pedirPagamento(e) {
  erroPagamento.value = ''
  confirmPagamento.value = { open: true, item: e }
}

async function confirmarPagamento() {
  const item = confirmPagamento.value.item
  if (!item) return
  confirmPagamento.value.open = false
  try {
    // Parcelas são pagas em ordem — a próxima pendente é sempre
    // parcelas_pagas_count + 1 (mesma lógica da tela de detalhe).
    await api.post(`/emprestimos/${item.id}/pagar-parcela/`, { numero: item.parcelas_pagas_count + 1 })
    await carregar()
  } catch (e2) {
    erroPagamento.value = e2.data?.detail || 'Não deu pra registrar o pagamento agora.'
  }
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">Empréstimos</h1>
      <RouterLink to="/emprestimos/novo" class="btn-primary">
        <Plus :size="16" /> Novo empréstimo
      </RouterLink>
    </div>

    <div v-if="erroPagamento" class="rounded-xl bg-red/10 px-4 py-3 text-sm text-red">{{ erroPagamento }}</div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <EmptyState
      v-else-if="!emprestimos.length"
      :icon="Landmark"
      title="Nenhum empréstimo cadastrado ainda"
      description="Cadastre um financiamento ou empréstimo pra simular amortizações e acompanhar o saldo devedor."
    >
      <RouterLink to="/emprestimos/novo" class="btn-primary">
        <Plus :size="16" /> Novo empréstimo
      </RouterLink>
    </EmptyState>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[720px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Descrição</th>
            <th class="pb-2 font-medium">Sistema</th>
            <th class="pb-2 text-right font-medium">Valor total</th>
            <th class="pb-2 text-right font-medium">Saldo devedor</th>
            <th class="pb-2 text-right font-medium">Parcelas</th>
            <th class="pb-2 font-medium">Status</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in emprestimos" :key="e.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2 font-medium text-wine">
              <RouterLink :to="`/emprestimos/${e.id}`" class="hover:underline">{{ e.descricao }}</RouterLink>
            </td>
            <td class="py-2 text-stone-500">{{ e.sistema_amortizacao_display }}</td>
            <td class="py-2 text-right text-stone-700">{{ formatarMoeda(e.valor_total) }}</td>
            <td class="py-2 text-right font-medium" :class="e.quitado ? 'text-emerald-600' : 'text-stone-800'">
              {{ formatarMoeda(e.saldo_devedor) }}
            </td>
            <td class="py-2 text-right text-stone-700">{{ e.parcelas_pagas_count }}/{{ e.numero_parcelas }}</td>
            <td class="py-2">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="e.quitado ? 'bg-emerald-100 text-emerald-700' : 'bg-peach/30 text-wine'">
                {{ e.quitado ? 'Quitado' : 'Em andamento' }}
              </span>
            </td>
            <td class="py-2 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  v-if="!e.quitado"
                  type="button"
                  class="mr-1 inline-flex items-center gap-1 rounded-lg border border-wine/30 px-2 py-1 text-xs font-semibold text-wine transition hover:bg-wine/5"
                  @click="pedirPagamento(e)"
                >
                  <Banknote :size="13" /> Pagar
                </button>
                <RouterLink :to="`/emprestimos/${e.id}/editar`" class="rounded-lg p-1.5 text-stone-400 transition hover:bg-stone-100 hover:text-wine" title="Editar">
                  <Pencil :size="14" />
                </RouterLink>
                <button type="button" class="rounded-lg p-1.5 text-stone-400 transition hover:bg-red/10 hover:text-red" title="Excluir" @click="pedirExclusao(e)">
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
      :title="`Excluir ${confirmExclusao.item?.descricao}?`"
      description="As despesas já geradas pelas parcelas pagas não são apagadas."
      @confirm="confirmarExclusao"
    />

    <ConfirmDialog
      v-model:open="confirmPagamento.open"
      :title="`Marcar parcela ${confirmPagamento.item ? confirmPagamento.item.parcelas_pagas_count + 1 : ''} de ${confirmPagamento.item?.descricao} como paga?`"
      description="Lança uma despesa de mesmo valor na categoria Empréstimos, com data de hoje."
      confirm-label="Pagar"
      variant="primary"
      @confirm="confirmarPagamento"
    />
  </div>
</template>
