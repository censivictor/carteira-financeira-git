<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({ categoria: '', descricao: '', valor: '', dia_do_mes: '', ativa: true })
const categorias = ref([])
const erros = ref({})
const salvando = ref(false)
const carregando = ref(true)

onMounted(async () => {
  categorias.value = await api.get('/financas/categorias/')
  if (editando.value) {
    const r = await api.get(`/financas/recorrentes/${id}/`)
    form.value = { categoria: r.categoria, descricao: r.descricao, valor: r.valor, dia_do_mes: r.dia_do_mes, ativa: r.ativa }
  }
  carregando.value = false
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    if (editando.value) {
      await api.patch(`/financas/recorrentes/${id}/`, form.value)
    } else {
      await api.post('/financas/recorrentes/', form.value)
    }
    router.push('/financas/recorrentes')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
    <h1 class="text-2xl font-bold text-stone-800">{{ editando ? 'Editar despesa recorrente' : 'Nova despesa recorrente' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
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
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Dia do mês</label>
        <input v-model="form.dia_do_mes" type="number" min="1" max="31" class="input" required />
        <p class="mt-1 text-xs text-stone-400">Meses mais curtos usam o último dia disponível.</p>
        <p v-if="erros.dia_do_mes" class="mt-1 text-xs text-red">{{ erros.dia_do_mes[0] }}</p>
      </div>
      <label class="flex items-center gap-2 text-sm text-stone-700">
        <input v-model="form.ativa" type="checkbox" class="h-4 w-4 rounded border-stone-300 text-wine focus:ring-wine/40" />
        Ativa
      </label>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/financas/recorrentes" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
