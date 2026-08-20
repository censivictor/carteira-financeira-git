<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({ nome: '', valor_alvo: '', data_alvo: '', ativos: [] })
const erros = ref({})
const salvando = ref(false)
const carregando = ref(true)
const ativosDisponiveis = ref([])

// Agrupado por tipo (Ação/FII/Cripto/Renda Fixa) pra facilitar achar o ativo
// certo numa carteira com muita coisa cadastrada.
const gruposAtivos = computed(() => {
  const grupos = {}
  for (const a of ativosDisponiveis.value) {
    if (!grupos[a.tipo_display]) grupos[a.tipo_display] = []
    grupos[a.tipo_display].push(a)
  }
  return grupos
})

onMounted(async () => {
  const [ativos] = await Promise.all([
    api.get('/investimentos/ativos/'),
    editando.value
      ? api.get(`/metas/${id}/`).then((m) => {
          form.value = { nome: m.nome, valor_alvo: m.valor_alvo, data_alvo: m.data_alvo || '', ativos: m.ativos || [] }
        })
      : Promise.resolve(),
  ])
  ativosDisponiveis.value = ativos
  carregando.value = false
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  const payload = { ...form.value, data_alvo: form.value.data_alvo || null }
  try {
    if (editando.value) {
      await api.patch(`/metas/${id}/`, payload)
    } else {
      await api.post('/metas/', payload)
    }
    router.push('/metas')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
    <h1 class="text-2xl font-bold text-stone-800">{{ editando ? 'Editar meta' : 'Nova meta' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Nome</label>
        <input v-model="form.nome" type="text" placeholder="Ex: Reserva de emergência" class="input" required />
        <p v-if="erros.nome" class="mt-1 text-xs text-red">{{ erros.nome[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor alvo (R$)</label>
        <input v-model="form.valor_alvo" type="number" step="any" min="0.01" class="input" required />
        <p v-if="erros.valor_alvo" class="mt-1 text-xs text-red">{{ erros.valor_alvo[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Data alvo (opcional)</label>
        <input v-model="form.data_alvo" type="date" class="input" />
        <p v-if="erros.data_alvo" class="mt-1 text-xs text-red">{{ erros.data_alvo[0] }}</p>
      </div>

      <div v-if="ativosDisponiveis.length">
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Vincular ativos (opcional)</label>
        <p class="mb-2 text-xs text-stone-400">
          O valor de mercado atual dos ativos marcados soma no progresso da meta, além dos aportes manuais.
        </p>
        <div class="max-h-56 space-y-3 overflow-y-auto rounded-xl border border-stone-300 p-3">
          <div v-for="(itens, tipo) in gruposAtivos" :key="tipo">
            <div class="mb-1 text-xs font-semibold uppercase tracking-wide text-stone-400">{{ tipo }}</div>
            <label v-for="a in itens" :key="a.id" class="flex items-center gap-2 py-1 text-sm text-stone-700">
              <input v-model="form.ativos" type="checkbox" :value="a.id" class="rounded border-stone-300 text-wine focus:ring-wine/30" />
              {{ a.ticker }}
            </label>
          </div>
        </div>
      </div>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/metas" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
