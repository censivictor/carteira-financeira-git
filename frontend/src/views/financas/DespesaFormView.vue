<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({ categoria: '', descricao: '', valor: '', data: '' })
const categorias = ref([])
const erros = ref({})
const salvando = ref(false)
const carregando = ref(true)

onMounted(async () => {
  categorias.value = await api.get('/financas/categorias/')
  if (editando.value) {
    const d = await api.get(`/financas/despesas/${id}/`)
    form.value = { categoria: d.categoria, descricao: d.descricao, valor: d.valor, data: d.data }
  }
  carregando.value = false
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    if (editando.value) {
      await api.patch(`/financas/despesas/${id}/`, form.value)
    } else {
      await api.post('/financas/despesas/', form.value)
    }
    router.push('/financas/despesas')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
    <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">{{ editando ? 'Editar despesa' : 'Nova despesa' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div v-if="!categorias.length" class="rounded-xl bg-peach/15 px-4 py-3 text-sm text-wine">
        Você ainda não tem categorias cadastradas.
        <RouterLink to="/financas/categorias/nova" class="font-medium underline">Criar categoria</RouterLink>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Categoria</label>
        <select v-model="form.categoria" class="input" required>
          <option value="" disabled>Selecione</option>
          <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
        </select>
        <p v-if="erros.categoria" class="mt-1 text-xs text-red">{{ erros.categoria[0] }}</p>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Descrição</label>
        <input v-model="form.descricao" type="text" class="input" required />
        <p v-if="erros.descricao" class="mt-1 text-xs text-red">{{ erros.descricao[0] }}</p>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor (R$)</label>
        <input v-model="form.valor" type="number" step="any" class="input" required />
        <p v-if="erros.valor" class="mt-1 text-xs text-red">{{ erros.valor[0] }}</p>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Data</label>
        <input v-model="form.data" type="date" class="input" required />
        <p v-if="erros.data" class="mt-1 text-xs text-red">{{ erros.data[0] }}</p>
      </div>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/financas/despesas" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
