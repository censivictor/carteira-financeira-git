<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({ descricao: '', tipo: 'SALARIO', valor: '', data: '' })
const erros = ref({})
const salvando = ref(false)
const carregando = ref(editando.value)

onMounted(async () => {
  if (editando.value) {
    const r = await api.get(`/financas/receitas/${id}/`)
    form.value = { descricao: r.descricao, tipo: r.tipo, valor: r.valor, data: r.data }
    carregando.value = false
  }
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    if (editando.value) {
      await api.patch(`/financas/receitas/${id}/`, form.value)
    } else {
      await api.post('/financas/receitas/', form.value)
    }
    router.push('/financas/receitas')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
    <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">{{ editando ? 'Editar receita' : 'Nova receita' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Descrição</label>
        <input v-model="form.descricao" type="text" class="input" required />
        <p v-if="erros.descricao" class="mt-1 text-xs text-red">{{ erros.descricao[0] }}</p>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Tipo</label>
        <select v-model="form.tipo" class="input">
          <option value="SALARIO">Salário</option>
          <option value="FREELA">Freelance</option>
          <option value="RENDIMENTO">Rendimento</option>
          <option value="OUTRO">Outro</option>
        </select>
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
        <RouterLink to="/financas/receitas" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
