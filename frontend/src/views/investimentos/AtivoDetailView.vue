<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarMoedaPrecisa, formatarData } from '@/lib/format'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import TransacaoForm from '@/components/TransacaoForm.vue'
import ProventoForm from '@/components/ProventoForm.vue'
import { Plus, LoaderCircle, ArrowLeft } from '@lucide/vue'

const route = useRoute()
const ativoId = route.params.id

const ativo = ref(null)
const transacoes = ref([])
const proventos = ref([])
const carregando = ref(true)

const mostraProventos = computed(() => ativo.value && ['ACAO', 'FII'].includes(ativo.value.tipo))
// Cripto barata tem preço unitário na casa de frações de centavo — usa
// formatação com mais casas decimais pra não virar "R$ 0,00" na tela.
const ehCripto = computed(() => ativo.value?.tipo === 'CRIPTO')
const formatarPreco = (v) => (ehCripto.value ? formatarMoedaPrecisa(v) : formatarMoeda(v))
const proventosTotal = computed(() => proventos.value.reduce((soma, p) => soma + p.valor_total, 0))

const modalTransacao = ref(false)
const modalProvento = ref(false)

// Estado do ConfirmDialog: `open` (booleano, controla visibilidade) fica
// separado do item alvo (`item`) — o AlertDialogAction do reka-ui fecha o
// diálogo (emitindo update:open=false) na MESMA interação de clique que
// dispara @confirm, e a ordem entre os dois não é garantida. Se o item
// alvo fosse zerado junto com o fechamento, o handler de confirmação podia
// ler `null` antes de conseguir o id pra excluir. Por isso o item só é
// sobrescrito na próxima vez que abrimos o diálogo, nunca zerado ao fechar.
const confirmTransacao = ref({ open: false, item: null })
const confirmProvento = ref({ open: false, item: null })

async function carregarTudo() {
  carregando.value = true
  const promessas = [
    api.get(`/investimentos/ativos/${ativoId}/`),
    api.get(`/investimentos/transacoes/?ativo=${ativoId}`),
  ]
  const [a, t] = await Promise.all(promessas)
  ativo.value = a
  transacoes.value = t
  if (['ACAO', 'FII'].includes(a.tipo)) {
    proventos.value = await api.get(`/investimentos/proventos/?ativo=${ativoId}`)
  }
  carregando.value = false
}

async function aoCriarTransacao() {
  modalTransacao.value = false
  await carregarTudo()
}

async function aoCriarProvento() {
  modalProvento.value = false
  await carregarTudo()
}

function pedirExclusaoTransacao(t) {
  confirmTransacao.value = { open: true, item: t }
}

function pedirExclusaoProvento(p) {
  confirmProvento.value = { open: true, item: p }
}

async function confirmarExclusaoTransacao() {
  const item = confirmTransacao.value.item
  if (!item) return
  await api.delete(`/investimentos/transacoes/${item.id}/`)
  confirmTransacao.value.open = false
  await carregarTudo()
}

async function confirmarExclusaoProvento() {
  const item = confirmProvento.value.item
  if (!item) return
  await api.delete(`/investimentos/proventos/${item.id}/`)
  confirmProvento.value.open = false
  await carregarTudo()
}

onMounted(carregarTudo)
</script>

<template>
  <div v-if="carregando" class="flex h-64 items-center justify-center text-stone-400">
    <LoaderCircle :size="28" class="animate-spin" />
  </div>

  <div v-else class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <RouterLink to="/investimentos" class="mb-1 flex items-center gap-1 text-sm text-stone-400 hover:text-wine">
          <ArrowLeft :size="14" /> Investimentos
        </RouterLink>
        <h1 class="text-2xl font-bold text-stone-800">
          {{ ativo.ticker }}
          <span class="text-base font-normal text-stone-400">{{ ativo.tipo_display }}{{ ativo.nome ? ' — ' + ativo.nome : '' }}</span>
        </h1>
      </div>
      <div class="flex gap-2">
        <button type="button" class="btn-primary" @click="modalTransacao = true">
          <Plus :size="16" /> Nova transação
        </button>
        <button v-if="mostraProventos" type="button" class="btn-secondary" @click="modalProvento = true">
          <Plus :size="16" /> Novo provento
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3" :class="mostraProventos ? 'lg:grid-cols-4' : ''">
      <div class="card">
        <div class="text-sm text-stone-500">Quantidade atual</div>
        <div class="mt-1 text-xl font-bold text-stone-800">{{ ativo.quantidade ?? 0 }}</div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Preço médio</div>
        <div class="mt-1 text-xl font-bold text-stone-800">{{ formatarPreco(ativo.preco_medio_compra) }}</div>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Valor investido</div>
        <div class="mt-1 text-xl font-bold text-stone-800">{{ formatarMoeda(ativo.valor_investido) }}</div>
      </div>
      <div v-if="mostraProventos" class="card">
        <div class="text-sm text-stone-500">Proventos recebidos (total)</div>
        <div class="mt-1 text-xl font-bold text-emerald-600">{{ formatarMoeda(proventosTotal) }}</div>
      </div>
    </div>

    <div v-if="!transacoes.length" class="rounded-xl bg-peach/15 px-4 py-3 text-sm text-wine">
      Nenhuma transação lançada ainda — a posição fica zerada até você registrar a primeira compra.
    </div>

    <div class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Transações</h3>
      <table class="w-full min-w-[640px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Data</th>
            <th class="pb-2 font-medium">Tipo</th>
            <th class="pb-2 text-right font-medium">Quantidade</th>
            <th class="pb-2 text-right font-medium">Preço unitário</th>
            <th class="pb-2 pr-4 text-right font-medium">Total</th>
            <th class="pb-2 font-medium">Observação</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in transacoes" :key="t.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2">{{ formatarData(t.data) }}</td>
            <td class="py-2">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="t.tipo === 'COMPRA' ? 'bg-emerald-100 text-emerald-700' : 'bg-red/10 text-red'">
                {{ t.tipo_display }}
              </span>
            </td>
            <td class="py-2 text-right">{{ t.quantidade }}</td>
            <td class="py-2 text-right">{{ formatarPreco(t.preco_unitario) }}</td>
            <td class="py-2 pr-4 text-right">{{ formatarMoeda(t.valor_total) }}</td>
            <td class="py-2 text-stone-500">{{ t.observacao || '—' }}</td>
            <td class="py-2 text-right">
              <button type="button" class="text-xs font-medium text-red hover:underline" @click="pedirExclusaoTransacao(t)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!transacoes.length">
            <td colspan="7" class="py-8 text-center text-stone-400">Nenhuma transação ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="mostraProventos" class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Proventos</h3>
      <table class="w-full min-w-[640px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Data-com</th>
            <th class="pb-2 font-medium">Tipo</th>
            <th class="pb-2 text-right font-medium">Valor/cota</th>
            <th class="pb-2 text-right font-medium">Quantidade na data</th>
            <th class="pb-2 pr-4 text-right font-medium">Total</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in proventos" :key="p.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2">{{ formatarData(p.data_com) }}</td>
            <td class="py-2"><span class="rounded-full bg-coral/20 px-2.5 py-0.5 text-xs font-medium text-wine">{{ p.tipo_display }}</span></td>
            <td class="py-2 text-right">R$ {{ Number(p.valor_por_cota).toFixed(6) }}</td>
            <td class="py-2 text-right">{{ p.quantidade_na_data }}</td>
            <td class="py-2 text-right">{{ formatarMoeda(p.valor_total) }}</td>
            <td class="py-2 text-right">
              <button type="button" class="text-xs font-medium text-red hover:underline" @click="pedirExclusaoProvento(p)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!proventos.length">
            <td colspan="6" class="py-8 text-center text-stone-400">Nenhum provento lançado ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal v-model:open="modalTransacao" title="Nova transação">
      <TransacaoForm :ativo="ativo" @created="aoCriarTransacao" />
    </Modal>

    <Modal v-model:open="modalProvento" title="Novo provento">
      <ProventoForm :ativo-id="ativoId" @created="aoCriarProvento" />
    </Modal>

    <ConfirmDialog
      v-model:open="confirmTransacao.open"
      title="Excluir transação?"
      @confirm="confirmarExclusaoTransacao"
    />
    <ConfirmDialog
      v-model:open="confirmProvento.open"
      title="Excluir provento?"
      @confirm="confirmarExclusaoProvento"
    />
  </div>
</template>
