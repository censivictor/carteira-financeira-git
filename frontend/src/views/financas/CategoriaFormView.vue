<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({ nome: '', cor: '#6c757d', orcamento_mensal: '' })
const erros = ref({})
const salvando = ref(false)
const carregando = ref(editando.value)

onMounted(async () => {
  if (editando.value) {
    const c = await api.get(`/financas/categorias/${id}/`)
    form.value = { nome: c.nome, cor: c.cor, orcamento_mensal: c.orcamento_mensal || '' }
    carregando.value = false
  }
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  const payload = { ...form.value, orcamento_mensal: form.value.orcamento_mensal || null }
  try {
    if (editando.value) {
      await api.patch(`/financas/categorias/${id}/`, payload)
    } else {
      await api.post('/financas/categorias/', payload)
    }
    router.push('/financas/categorias')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
    <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">{{ editando ? 'Editar categoria' : 'Nova categoria' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Nome</label>
        <input v-model="form.nome" type="text" class="input" required />
        <p v-if="erros.nome" class="mt-1 text-xs text-red">{{ erros.nome[0] }}</p>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Cor (legenda do gráfico)</label>
        <input v-model="form.cor" type="color" class="h-11 w-20 rounded-lg border border-stone-300" />
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Orçamento mensal (R$)</label>
        <input v-model="form.orcamento_mensal" type="number" step="any" class="input" />
        <p class="mt-1 text-xs text-stone-400">Deixe em branco pra não definir um limite de gasto pra essa categoria.</p>
        <p v-if="erros.orcamento_mensal" class="mt-1 text-xs text-red">{{ erros.orcamento_mensal[0] }}</p>
      </div>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/financas/categorias" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
