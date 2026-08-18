<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import CompraCartaoForm from '@/components/CompraCartaoForm.vue'
import { Plus, LoaderCircle, ArrowLeft, Check } from '@lucide/vue'

const route = useRoute()
const cartaoId = route.params.id

const cartao = ref(null)
const compras = ref([])
const faturas = ref([])
const carregando = ref(true)

const modalCompra = ref(false)
const confirmPagamento = ref({ open: false, item: null })
const confirmExclusaoCompra = ref({ open: false, item: null })
const erroExclusaoCompra = ref('')

const usoPct = computed(() => {
  if (!cartao.value || !cartao.value.limite) return null
  return Math.min((cartao.value.limite_utilizado / cartao.value.limite) * 100, 100)
})

async function carregarTudo() {
  carregando.value = true
  const [c, comp, fat] = await Promise.all([
    api.get(`/cartoes/${cartaoId}/`),
    api.get(`/cartoes-compras/?cartao=${cartaoId}`),
    api.get(`/cartoes-faturas/?cartao=${cartaoId}`),
  ])
  cartao.value = c
  compras.value = comp
  faturas.value = fat
  carregando.value = false
}

async function aoCriarCompra() {
  modalCompra.value = false
  await carregarTudo()
}

const erroPagamento = ref('')

function pedirPagamento(fatura) {
  erroPagamento.value = ''
  confirmPagamento.value = { open: true, item: fatura }
}

async function confirmarPagamento() {
  const fatura = confirmPagamento.value.item
  if (!fatura) return
  try {
    await api.post(`/cartoes-faturas/${fatura.id}/pagar/`, {})
    confirmPagamento.value.open = false
    await carregarTudo()
  } catch (e) {
    confirmPagamento.value.open = false
    erroPagamento.value = e.data?.detail || 'Não foi possível pagar essa fatura.'
  }
}

function pedirExclusaoCompra(compra) {
  erroExclusaoCompra.value = ''
  confirmExclusaoCompra.value = { open: true, item: compra }
}

async function confirmarExclusaoCompra() {
  const compra = confirmExclusaoCompra.value.item
  if (!compra) return
  try {
    await api.delete(`/cartoes-compras/${compra.id}/`)
    confirmExclusaoCompra.value.open = false
    await carregarTudo()
  } catch (e) {
    confirmExclusaoCompra.value.open = false
    erroExclusaoCompra.value = e.data?.detail || 'Não foi possível excluir essa compra.'
  }
}

onMounted(carregarTudo)
</script>

<template>
  <div v-if="carregando" class="flex h-64 items-center justify-center text-stone-400">
    <LoaderCircle :size="28" class="animate-spin" />
  </div>

  <div v-else class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <RouterLink to="/cartoes" class="mb-1 flex items-center gap-1 text-sm text-stone-400 hover:text-wine">
          <ArrowLeft :size="14" /> Cartões
        </RouterLink>
        <h1 class="text-2xl font-bold text-stone-800">{{ cartao.nome }}</h1>
      </div>
      <button type="button" class="btn-primary" @click="modalCompra = true">
        <Plus :size="16" /> Nova compra
      </button>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <div class="card">
        <div class="text-sm text-stone-500">Utilizado</div>
        <div class="mt-1 text-xl font-bold text-stone-800">{{ formatarMoeda(cartao.limite_utilizado) }}</div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Disponível</div>
        <div class="mt-1 text-xl font-bold text-stone-800">
          {{ cartao.limite_disponivel !== null ? formatarMoeda(cartao.limite_disponivel) : 'sem limite definido' }}
        </div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Fechamento / Vencimento</div>
        <div class="mt-1 text-xl font-bold text-stone-800">dia {{ cartao.dia_fechamento }} / dia {{ cartao.dia_vencimento }}</div>
      </div>
    </div>

    <div v-if="usoPct !== null" class="card">
      <div class="h-2 w-full overflow-hidden rounded-full bg-stone-100">
        <div class="h-full rounded-full" :class="usoPct >= 100 ? 'bg-red' : usoPct >= 80 ? 'bg-peach' : 'bg-emerald-500'" :style="{ width: usoPct + '%' }" />
      </div>
    </div>

    <div v-if="erroPagamento" class="rounded-xl bg-red/10 px-4 py-3 text-sm text-red">{{ erroPagamento }}</div>

    <div class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Faturas</h3>
      <table class="w-full min-w-[560px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Mês</th>
            <th class="pb-2 text-right font-medium">Valor</th>
            <th class="pb-2 font-medium">Vencimento</th>
            <th class="pb-2 font-medium">Status</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in faturas" :key="f.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2.5">{{ String(f.mes).padStart(2, '0') }}/{{ f.ano }}</td>
            <td class="py-2.5 text-right font-medium">{{ formatarMoeda(f.valor_total) }}</td>
            <td class="py-2.5">{{ formatarData(f.data_vencimento) }}</td>
            <td class="py-2.5">
              <span v-if="f.paga" class="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                <Check :size="12" /> Paga
              </span>
              <span v-else class="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-medium text-stone-500">Aberta</span>
            </td>
            <td class="py-2.5 text-right">
              <button v-if="!f.paga" type="button" class="text-xs font-medium text-wine hover:underline" @click="pedirPagamento(f)">Pagar fatura</button>
              <span v-else class="text-xs text-stone-400">{{ formatarData(f.data_pagamento) }}</span>
            </td>
          </tr>
          <tr v-if="!faturas.length">
            <td colspan="5" class="py-8 text-center text-stone-400">Nenhuma fatura ainda — lance uma compra pra começar.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="erroExclusaoCompra" class="rounded-xl bg-red/10 px-4 py-3 text-sm text-red">{{ erroExclusaoCompra }}</div>

    <div class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Compras</h3>
      <table class="w-full min-w-[560px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Data</th>
            <th class="pb-2 font-medium">Descrição</th>
            <th class="pb-2 text-right font-medium">Valor total</th>
            <th class="pb-2 text-right font-medium">Parcelas</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in compras" :key="c.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2.5">{{ formatarData(c.data_compra) }}</td>
            <td class="py-2.5">{{ c.descricao }}</td>
            <td class="py-2.5 text-right">{{ formatarMoeda(c.valor_total) }}</td>
            <td class="py-2.5 text-right">{{ c.numero_parcelas }}x</td>
            <td class="py-2.5 text-right">
              <button type="button" class="text-xs font-medium text-red hover:underline" @click="pedirExclusaoCompra(c)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!compras.length">
            <td colspan="5" class="py-8 text-center text-stone-400">Nenhuma compra lançada ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal v-model:open="modalCompra" title="Nova compra">
      <CompraCartaoForm :cartao-id="cartaoId" @created="aoCriarCompra" />
    </Modal>

    <ConfirmDialog
      v-model:open="confirmPagamento.open"
      :title="`Pagar fatura ${String(confirmPagamento.item?.mes).padStart(2, '0')}/${confirmPagamento.item?.ano}?`"
      description="Lança uma despesa com o valor total da fatura, com data de hoje."
      confirm-label="Pagar"
      variant="primary"
      @confirm="confirmarPagamento"
    />
    <ConfirmDialog
      v-model:open="confirmExclusaoCompra.open"
      :title="`Excluir ${confirmExclusaoCompra.item?.descricao}?`"
      description="Apaga todas as parcelas dessa compra que ainda não caíram numa fatura paga."
      @confirm="confirmarExclusaoCompra"
    />
  </div>
</template>
