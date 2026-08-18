<script setup>
import { ref } from 'vue'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const props = defineProps({ metaId: { type: [String, Number], required: true }, tipo: { type: String, required: true } })
const emit = defineEmits(['created'])

const form = ref({ valor: '', data: new Date().toISOString().slice(0, 10), observacao: '' })
const erros = ref({})
const salvando = ref(false)

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    await api.post('/metas-aportes/', { ...form.value, meta: props.metaId, tipo: props.tipo })
    emit('created')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="salvar">
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor (R$)</label>
      <input v-model="form.valor" type="number" step="any" min="0.01" class="input" required autofocus />
      <p v-if="erros.valor" class="mt-1 text-xs text-red">{{ erros.valor[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Data</label>
      <input v-model="form.data" type="date" class="input" required />
      <p v-if="erros.data" class="mt-1 text-xs text-red">{{ erros.data[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Observação (opcional)</label>
      <input v-model="form.observacao" type="text" class="input" />
    </div>
    <button type="submit" class="btn-primary w-full" :disabled="salvando">
      <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
      Salvar
    </button>
  </form>
</template>
