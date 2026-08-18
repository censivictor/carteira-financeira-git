<script setup>
import { ref } from 'vue'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const props = defineProps({ cartaoId: { type: [String, Number], required: true } })
const emit = defineEmits(['created'])

const form = ref({ descricao: '', valor_total: '', numero_parcelas: 1, data_compra: '' })
const erros = ref({})
const salvando = ref(false)

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    await api.post('/cartoes-compras/', { ...form.value, cartao: props.cartaoId })
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
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Descrição</label>
      <input v-model="form.descricao" type="text" class="input" required />
      <p v-if="erros.descricao" class="mt-1 text-xs text-red">{{ erros.descricao[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor total (R$)</label>
      <input v-model="form.valor_total" type="number" step="any" min="0.01" class="input" required />
      <p v-if="erros.valor_total" class="mt-1 text-xs text-red">{{ erros.valor_total[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Parcelas</label>
      <input v-model="form.numero_parcelas" type="number" min="1" class="input" required />
      <p class="mt-1 text-xs text-stone-400">Divide o valor total igualmente, 1 parcela por fatura.</p>
      <p v-if="erros.numero_parcelas" class="mt-1 text-xs text-red">{{ erros.numero_parcelas[0] }}</p>
    </div>
    <div>
      <label class="mb-1.5 block text-sm font-medium text-stone-700">Data da compra</label>
      <input v-model="form.data_compra" type="date" class="input" required />
      <p v-if="erros.data_compra" class="mt-1 text-xs text-red">{{ erros.data_compra[0] }}</p>
    </div>
    <button type="submit" class="btn-primary w-full" :disabled="salvando">
      <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
      Salvar
    </button>
  </form>
</template>
