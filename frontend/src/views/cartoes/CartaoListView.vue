<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle } from '@lucide/vue'

const cartoes = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })

async function carregar() {
  carregando.value = true
  cartoes.value = await api.get('/cartoes/')
  carregando.value = false
}

function pedirExclusao(c) {
  confirmExclusao.value = { open: true, item: c }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  await api.delete(`/cartoes/${item.id}/`)
  confirmExclusao.value.open = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-stone-800">Cartões de crédito</h1>
      <RouterLink to="/cartoes/novo" class="btn-primary">
        <Plus :size="16" /> Novo cartão
      </RouterLink>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink v-for="c in cartoes" :key="c.id" :to="`/cartoes/${c.id}`" class="card block transition hover:border-wine/40 hover:shadow-md">
        <div class="flex items-start justify-between">
          <h3 class="font-semibold text-stone-800">{{ c.nome }}</h3>
          <button type="button" class="text-xs font-medium text-red hover:underline" @click.prevent="pedirExclusao(c)">Excluir</button>
        </div>
        <div class="mt-3 text-sm text-stone-500">Fecha dia {{ c.dia_fechamento }} · Vence dia {{ c.dia_vencimento }}</div>
        <div class="mt-3">
          <div class="text-xs text-stone-400">Utilizado</div>
          <div class="text-lg font-bold text-stone-800">{{ formatarMoeda(c.limite_utilizado) }}</div>
        </div>
        <template v-if="c.limite !== null">
          <div class="mt-2 h-2 w-full overflow-hidden rounded-full bg-stone-100">
            <div
              class="h-full rounded-full"
              :class="c.limite_utilizado / c.limite >= 1 ? 'bg-red' : c.limite_utilizado / c.limite >= 0.8 ? 'bg-peach' : 'bg-emerald-500'"
              :style="{ width: Math.min((c.limite_utilizado / c.limite) * 100, 100) + '%' }"
            />
          </div>
          <div class="mt-1 text-xs text-stone-400">{{ formatarMoeda(c.limite_disponivel) }} disponível de {{ formatarMoeda(c.limite) }}</div>
        </template>
      </RouterLink>
      <div v-if="!cartoes.length" class="card col-span-full py-10 text-center text-stone-400">
        Nenhum cartão cadastrado ainda.
      </div>
    </div>

    <ConfirmDialog
      v-model:open="confirmExclusao.open"
      :title="`Excluir ${confirmExclusao.item?.nome}?`"
      description="Isso também apaga as compras e faturas ligadas a esse cartão."
      @confirm="confirmarExclusao"
    />
  </div>
</template>
