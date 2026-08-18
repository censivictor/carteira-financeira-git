<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({ nome: '', limite: '', dia_fechamento: '', dia_vencimento: '' })
const erros = ref({})
const salvando = ref(false)
const carregando = ref(true)

onMounted(async () => {
  if (editando.value) {
    const c = await api.get(`/cartoes/${id}/`)
    form.value = { nome: c.nome, limite: c.limite ?? '', dia_fechamento: c.dia_fechamento, dia_vencimento: c.dia_vencimento }
  }
  carregando.value = false
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  const payload = { ...form.value, limite: form.value.limite === '' ? null : form.value.limite }
  try {
    if (editando.value) {
      await api.patch(`/cartoes/${id}/`, payload)
    } else {
      await api.post('/cartoes/', payload)
    }
    router.push('/cartoes')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-6">
    <h1 class="text-2xl font-bold text-stone-800">{{ editando ? 'Editar cartão' : 'Novo cartão' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Nome</label>
        <input v-model="form.nome" type="text" placeholder="Ex: Nubank, Inter Black" class="input" required />
        <p v-if="erros.nome" class="mt-1 text-xs text-red">{{ erros.nome[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Limite (R$, opcional)</label>
        <input v-model="form.limite" type="number" step="any" min="0" class="input" />
        <p class="mt-1 text-xs text-stone-400">Deixe em branco pra não acompanhar limite.</p>
        <p v-if="erros.limite" class="mt-1 text-xs text-red">{{ erros.limite[0] }}</p>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Dia de fechamento</label>
          <input v-model="form.dia_fechamento" type="number" min="1" max="31" class="input" required />
          <p v-if="erros.dia_fechamento" class="mt-1 text-xs text-red">{{ erros.dia_fechamento[0] }}</p>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Dia de vencimento</label>
          <input v-model="form.dia_vencimento" type="number" min="1" max="31" class="input" required />
          <p v-if="erros.dia_vencimento" class="mt-1 text-xs text-red">{{ erros.dia_vencimento[0] }}</p>
        </div>
      </div>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/cartoes" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
