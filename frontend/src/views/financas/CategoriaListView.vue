<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { formatarMoeda } from '@/lib/format'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, LoaderCircle } from '@lucide/vue'

const categorias = ref([])
const carregando = ref(true)
const confirmExclusao = ref({ open: false, item: null })
const erroExclusao = ref('')

async function carregar() {
  carregando.value = true
  categorias.value = await api.get('/financas/categorias/')
  carregando.value = false
}

function pedirExclusao(cat) {
  erroExclusao.value = ''
  confirmExclusao.value = { open: true, item: cat }
}

async function confirmarExclusao() {
  const item = confirmExclusao.value.item
  if (!item) return
  try {
    await api.delete(`/financas/categorias/${item.id}/`)
    confirmExclusao.value.open = false
    await carregar()
  } catch (e) {
    confirmExclusao.value.open = false
    erroExclusao.value = e.data?.detail || 'Não foi possível excluir essa categoria.'
  }
}

onMounted(carregar)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">Categorias de despesa</h1>
      <RouterLink to="/financas/categorias/nova" class="btn-primary">
        <Plus :size="16" /> Nova categoria
      </RouterLink>
    </div>

    <div v-if="erroExclusao" class="rounded-xl bg-red/10 px-4 py-3 text-sm text-red">{{ erroExclusao }}</div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full min-w-[560px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Nome</th>
            <th class="pb-2 font-medium">Cor</th>
            <th class="pb-2 text-right font-medium">Orçamento mensal</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in categorias" :key="c.id" class="border-b border-stone-100 last:border-0">
            <td class="py-2">
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium text-white" :style="{ backgroundColor: c.cor }">{{ c.nome }}</span>
            </td>
            <td class="py-2 text-stone-500">{{ c.cor }}</td>
            <td class="py-2 text-right text-stone-700">{{ c.orcamento_mensal ? formatarMoeda(c.orcamento_mensal) : '—' }}</td>
            <td class="py-2 text-right">
              <RouterLink :to="`/financas/categorias/${c.id}/editar`" class="text-xs font-medium text-stone-500 hover:text-wine">Editar</RouterLink>
              <button type="button" class="ml-3 text-xs font-medium text-red hover:underline" @click="pedirExclusao(c)">Excluir</button>
            </td>
          </tr>
          <tr v-if="!categorias.length">
            <td colspan="4" class="py-10 text-center text-stone-400">Nenhuma categoria cadastrada ainda.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ConfirmDialog
      v-model:open="confirmExclusao.open"
      :title="`Excluir ${confirmExclusao.item?.nome}?`"
      @confirm="confirmarExclusao"
    />
  </div>
</template>
