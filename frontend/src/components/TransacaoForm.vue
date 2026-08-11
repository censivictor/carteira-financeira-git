<script setup>
import { ref } from 'vue'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const props = defineProps({ ativoId: { type: [Number, String], required: true } })
const emit = defineEmits(['created'])

const form = ref({ tipo: '', quantidade: '', preco_unitario: '', data: '', observacao: '' })
const erros = ref({})
const salvando = ref(false)

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    await api.post('/investimentos/transacoes/', { ...form.value, ativo: props.ativoId })
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
        <option value="COMPRA">Compra</option>
        <option value="VENDA">Venda</option>
      </select>
      <p v-if="erros.tipo" class="mt-1 text-xs text-red">{{ erros.tipo[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Quantidade</label>
      <input v-model="form.quantidade" type="number" step="any" class="input" required />
      <p v-if="erros.quantidade" class="mt-1 text-xs text-red">{{ erros.quantidade[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Preço unitário (R$)</label>
      <input v-model="form.preco_unitario" type="number" step="any" class="input" required />
      <p v-if="erros.preco_unitario" class="mt-1 text-xs text-red">{{ erros.preco_unitario[0] }}</p>
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
