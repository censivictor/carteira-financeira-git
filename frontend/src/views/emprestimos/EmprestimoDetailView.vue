<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import AmortizacaoExtraForm from '@/components/AmortizacaoExtraForm.vue'
import { Plus, LoaderCircle, ArrowLeft, Check } from '@lucide/vue'

const route = useRoute()
const emprestimoId = route.params.id

const emprestimo = ref(null)
const parcelas = ref([])
const carregando = ref(true)

const modalAmortizar = ref(false)
const confirmPagamento = ref({ open: false, item: null })
const mensagemAmortizacao = ref('')

const proximaParcela = computed(() => parcelas.value.find((p) => !p.paga) || null)

async function carregarTudo() {
  carregando.value = true
  const [e, p] = await Promise.all([
    api.get(`/emprestimos/${emprestimoId}/`),
    api.get(`/emprestimos-parcelas/?emprestimo=${emprestimoId}`),
  ])
  emprestimo.value = e
  parcelas.value = p
  carregando.value = false
}

function pedirPagamento(parcela) {
  confirmPagamento.value = { open: true, item: parcela }
}

async function confirmarPagamento() {
  const parcela = confirmPagamento.value.item
  if (!parcela) return
  await api.post(`/emprestimos/${emprestimoId}/pagar-parcela/`, { numero: parcela.numero })
  confirmPagamento.value.open = false
  await carregarTudo()
}

async function aoAmortizar() {
  modalAmortizar.value = false
  const pendentesAntes = parcelas.value.filter((p) => !p.paga).length
  await carregarTudo()
  const pendentesDepois = parcelas.value.filter((p) => !p.paga).length
  const diferenca = pendentesAntes - pendentesDepois
  if (emprestimo.value.quitado) {
    mensagemAmortizacao.value = 'Empréstimo quitado com esse abatimento — nenhuma parcela pendente.'
  } else if (diferenca > 0) {
    mensagemAmortizacao.value = `Abatimento aplicado — o empréstimo agora tem ${pendentesDepois} parcela${pendentesDepois === 1 ? '' : 's'} pendente${pendentesDepois === 1 ? '' : 's'} (eram ${pendentesAntes}).`
  } else {
    mensagemAmortizacao.value = `Abatimento aplicado — mesma quantidade de parcelas, valor de cada uma reduzido.`
  }
}

onMounted(carregarTudo)
</script>

<template>
  <div v-if="carregando" class="flex h-64 items-center justify-center text-stone-400">
    <LoaderCircle :size="28" class="animate-spin" />
  </div>

  <div v-else class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <RouterLink to="/emprestimos" class="mb-1 flex items-center gap-1 text-sm text-stone-400 hover:text-wine">
          <ArrowLeft :size="14" /> Empréstimos
        </RouterLink>
        <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">
          {{ emprestimo.descricao }}
          <span class="text-base font-normal text-stone-400">{{ emprestimo.sistema_amortizacao_display }}</span>
        </h1>
      </div>
      <button v-if="!emprestimo.quitado" type="button" class="btn-primary" @click="modalAmortizar = true">
        <Plus :size="16" /> Abater valor extra
      </button>
    </div>

    <div v-if="mensagemAmortizacao" class="flex items-start justify-between gap-3 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
      <span>{{ mensagemAmortizacao }}</span>
      <button type="button" class="shrink-0 font-medium text-emerald-600 hover:underline" @click="mensagemAmortizacao = ''">Ok</button>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div class="card">
        <div class="text-sm text-stone-500">Valor total</div>
        <div class="mt-1 text-xl font-bold tracking-tight tabular-nums text-stone-800">{{ formatarMoeda(emprestimo.valor_total) }}</div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Saldo devedor</div>
        <div class="mt-1 text-xl font-bold tracking-tight tabular-nums" :class="emprestimo.quitado ? 'text-emerald-600' : 'text-stone-800'">
          {{ formatarMoeda(emprestimo.saldo_devedor) }}
        </div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Juros</div>
        <div class="mt-1 text-xl font-bold tracking-tight tabular-nums text-stone-800">{{ emprestimo.taxa_juros }}% {{ emprestimo.periodo_taxa_display.toLowerCase() }}</div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Parcelas pagas</div>
        <div class="mt-1 text-xl font-bold tracking-tight tabular-nums text-stone-800">{{ emprestimo.parcelas_pagas_count }}/{{ emprestimo.numero_parcelas }}</div>
      </div>
    </div>

    <div v-if="emprestimo.quitado" class="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
      Empréstimo quitado — nenhuma parcela pendente.
    </div>
    <div v-else-if="proximaParcela" class="rounded-xl bg-peach/15 px-4 py-3 text-sm text-wine">
      Próxima parcela: <strong>{{ formatarMoeda(proximaParcela.valor_parcela) }}</strong> em {{ formatarData(proximaParcela.data_vencimento) }}.
    </div>

    <div class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Parcelas</h3>
      <table class="w-full min-w-[720px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">#</th>
            <th class="pb-2 font-medium">Vencimento</th>
            <th class="pb-2 text-right font-medium">Parcela</th>
            <th class="pb-2 text-right font-medium">Juros</th>
            <th class="pb-2 text-right font-medium">Amortização</th>
            <th class="pb-2 text-right font-medium">Saldo devedor</th>
            <th class="pb-2 font-medium">Status</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in parcelas" :key="p.id" class="border-b border-stone-100 last:border-0" :class="p.paga ? 'text-stone-400' : 'text-stone-700'">
            <td class="py-2">{{ p.numero }}</td>
            <td class="py-2">{{ formatarData(p.data_vencimento) }}</td>
            <td class="py-2 text-right font-medium">{{ formatarMoeda(p.valor_parcela) }}</td>
            <td class="py-2 text-right">{{ formatarMoeda(p.valor_juros) }}</td>
            <td class="py-2 text-right">{{ formatarMoeda(p.valor_amortizacao) }}</td>
            <td class="py-2 text-right">{{ formatarMoeda(p.saldo_devedor) }}</td>
            <td class="py-2">
              <span v-if="p.paga" class="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                <Check :size="12" /> Paga
              </span>
              <span v-else class="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-500">Pendente</span>
            </td>
            <td class="py-2 text-right">
              <button v-if="!p.paga" type="button" class="text-xs font-medium text-wine hover:underline" @click="pedirPagamento(p)">
                Marcar como paga
              </button>
              <span v-else class="text-xs text-stone-400">{{ formatarData(p.data_pagamento) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal v-model:open="modalAmortizar" title="Abater valor extra">
      <AmortizacaoExtraForm :emprestimo="emprestimo" @done="aoAmortizar" />
    </Modal>

    <ConfirmDialog
      v-model:open="confirmPagamento.open"
      :title="`Marcar parcela ${confirmPagamento.item?.numero} como paga?`"
      description="Lança uma despesa de mesmo valor na categoria Empréstimos, com data de hoje."
      confirm-label="Pagar"
      variant="primary"
      @confirm="confirmarPagamento"
    />
  </div>
</template>
