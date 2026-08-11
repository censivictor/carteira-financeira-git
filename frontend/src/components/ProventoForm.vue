<script setup>
import { ref } from 'vue'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const props = defineProps({ ativoId: { type: [Number, String], required: true } })
const emit = defineEmits(['created'])

const form = ref({ tipo: '', valor_por_cota: '', data_com: '', data_pagamento: '', observacao: '' })
const erros = ref({})
const salvando = ref(false)

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    const payload = { ...form.value, ativo: props.ativoId }
    if (!payload.data_pagamento) payload.data_pagamento = null
    await api.post('/investimentos/proventos/', payload)
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
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Tipo</label>
      <select v-model="form.tipo" class="input" required>
        <option value="" disabled>Selecione</option>
        <option value="DIVIDENDO">Dividendo</option>
        <option value="JCP">Juros sobre Capital Próprio</option>
        <option value="RENDIMENTO">Rendimento (FII)</option>
      </select>
      <p v-if="erros.tipo" class="mt-1 text-xs text-red">{{ erros.tipo[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor por ação/cota (R$)</label>
      <input v-model="form.valor_por_cota" type="number" step="any" class="input" required />
      <p v-if="erros.valor_por_cota" class="mt-1 text-xs text-red">{{ erros.valor_por_cota[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Data-base (data-com)</label>
      <input v-model="form.data_com" type="date" class="input" required />
      <p class="mt-1 text-xs text-stone-400">A quantidade que você tinha nesse dia é usada pra calcular o valor recebido.</p>
      <p v-if="erros.data_com" class="mt-1 text-xs text-red">{{ erros.data_com[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Data de pagamento (opcional)</label>
      <input v-model="form.data_pagamento" type="date" class="input" />
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
