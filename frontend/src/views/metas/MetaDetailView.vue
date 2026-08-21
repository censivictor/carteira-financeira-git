<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda, formatarData } from '@/lib/format'
import Modal from '@/components/Modal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import AporteMetaForm from '@/components/AporteMetaForm.vue'
import { Plus, Minus, LoaderCircle, ArrowLeft, Trophy } from '@lucide/vue'

const route = useRoute()
const metaId = route.params.id

const meta = ref(null)
const aportes = ref([])
const carregando = ref(true)

const modalAporte = ref(false)
const modalRetirada = ref(false)
const confirmExclusao = ref({ open: false, item: null })

async function carregarTudo() {
  carregando.value = true
  const [m, a] = await Promise.all([
    api.get(`/metas/${metaId}/`),
    api.get(`/metas-aportes/?meta=${metaId}`),
  ])
  meta.value = m
  aportes.value = a
  carregando.value = false
}

async function aoRegistrar() {
  modalAporte.value = false
  modalRetirada.value = false
  await carregarTudo()
}

function pedirExclusao(a) {
  confirmExclusao.value = { open: true, item: a }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/metas-aportes/${item.id}/`)
  confirmExclusao.value.open = false
  await carregarTudo()
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
        <RouterLink to="/metas" class="mb-1 flex items-center gap-1 text-sm text-stone-400 hover:text-wine">
          <ArrowLeft :size="14" /> Metas
        </RouterLink>
        <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">{{ meta.nome }}</h1>
      </div>
      <div class="flex gap-2">
        <button type="button" class="btn-secondary" @click="modalRetirada = true">
          <Minus :size="16" /> Retirar
        </button>
        <button type="button" class="btn-primary" @click="modalAporte = true">
          <Plus :size="16" /> Aportar
        </button>
      </div>
    </div>

    <div v-if="meta.concluida" class="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
      <Trophy :size="16" /> Meta concluída — parabéns!
    </div>

    <div class="card">
      <div class="flex items-center justify-between text-sm">
        <span class="font-medium text-stone-700">{{ formatarMoeda(meta.valor_atual) }} guardado</span>
        <span class="text-stone-400">meta de {{ formatarMoeda(meta.valor_alvo) }}{{ meta.data_alvo ? ` até ${formatarData(meta.data_alvo)}` : '' }}</span>
      </div>
      <div class="mt-2 h-3 w-full overflow-hidden rounded-full bg-stone-100">
        <div class="h-full rounded-full transition-all" :class="meta.concluida ? 'bg-emerald-500' : 'bg-wine'" :style="{ width: meta.pct + '%' }" />
      </div>
      <div class="mt-1 text-xs text-stone-400">{{ meta.pct.toFixed(0) }}%</div>
      <div v-if="meta.ativos_detail?.length" class="mt-3 border-t border-stone-100 pt-3 text-xs text-stone-500">
        Inclui {{ meta.ativos_detail.length }} ativo{{ meta.ativos_detail.length > 1 ? 's' : '' }} da carteira:
        <span v-for="(a, i) in meta.ativos_detail" :key="a.id">
          {{ a.ticker }} ({{ formatarMoeda(a.valor_atual) }})<span v-if="i < meta.ativos_detail.length - 1">, </span>
        </span>
      </div>
    </div>

    <div class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Histórico</h3>
      <table class="w-full min-w-[560px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Data</th>
            <th class="pb-2 font-medium">Tipo</th>
            <th class="pb-2 text-right font-medium">Valor</th>
            <th class="pb-2 font-medium">Observação</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in aportes" :key="a.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2">{{ formatarData(a.data) }}</td>
            <td class="py-2">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="a.tipo === 'APORTE' ? 'bg-emerald-100 text-emerald-700' : 'bg-red/10 text-red'">
                {{ a.tipo_display }}
              </span>
            </td>
            <td class="py-2 text-right">{{ formatarMoeda(a.valor) }}</td>
            <td class="py-2 text-stone-500">{{ a.observacao || '—' }}</td>
            <td class="py-2 text-right">
              <button type="button" class="text-xs font-medium text-red hover:underline" @click="pedirExclusao(a)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!aportes.length">
            <td colspan="5" class="py-8 text-center text-stone-400">Nenhum aporte ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal v-model:open="modalAporte" title="Novo aporte">
      <AporteMetaForm :meta-id="metaId" tipo="APORTE" @created="aoRegistrar" />
    </Modal>
    <Modal v-model:open="modalRetirada" title="Nova retirada">
      <AporteMetaForm :meta-id="metaId" tipo="RETIRADA" @created="aoRegistrar" />
    </Modal>

    <ConfirmDialog v-model:open="confirmExclusao.open" title="Excluir esse lançamento?" @confirm="confirmarExclusao" />
  </div>
</template>
