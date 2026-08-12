<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const props = defineProps({ ativo: { type: Object, required: true } })
const emit = defineEmits(['created'])

const ehCripto = computed(() => props.ativo.tipo === 'CRIPTO')

const form = ref({ tipo: '', quantidade: '', preco_unitario: '', data: '', observacao: '' })
// Cripto costuma ser comprada por valor (ex: "R$ 100 de Bitcoin"), não por
// quantidade — ninguém sabe de cabeça que R$100 dá 0,00034521 BTC. Em vez de
// pedir a quantidade direto, pedimos o valor + o preço da unidade (já
// pré-preenchido com a cotação atual) e calculamos a quantidade.
const valorTotal = ref('')
const erros = ref({})
const salvando = ref(false)
const buscandoCotacao = ref(false)

const quantidadeCripto = computed(() => {
  const valor = Number(valorTotal.value)
  const preco = Number(form.value.preco_unitario)
  if (!valor || !preco) return null
  return valor / preco
})

onMounted(async () => {
  if (!ehCripto.value) return
  buscandoCotacao.value = true
  try {
    const cotacoes = await api.get('/investimentos/cotacoes/')
    const preco = cotacoes[props.ativo.ticker]?.preco
    if (preco) form.value.preco_unitario = preco
  } catch {
    // sem cotação disponível — usuário ainda pode digitar o preço na mão.
  } finally {
    buscandoCotacao.value = false
  }
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    const payload = { ...form.value, ativo: props.ativo.id }
    if (ehCripto.value) {
      if (!quantidadeCripto.value) {
        erros.value = { quantidade: ['Informe o valor e o preço unitário pra calcular a quantidade.'] }
        return
      }
      payload.quantidade = quantidadeCripto.value.toFixed(8)
    }
    await api.post('/investimentos/transacoes/', payload)
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

    <template v-if="ehCripto">
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor {{ form.tipo === 'VENDA' ? 'vendido' : 'investido' }} (R$)</label>
        <input v-model="valorTotal" type="number" step="any" placeholder="Ex: 100,00" class="input" required />
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Preço unitário (R$)</label>
        <input v-model="form.preco_unitario" type="number" step="any" class="input" required />
        <p class="mt-1 text-xs text-stone-400">
          {{ buscandoCotacao ? 'Buscando cotação atual…' : 'Preenchido com a cotação atual — ajuste se a compra foi em outro momento.' }}
        </p>
        <p v-if="erros.preco_unitario" class="mt-1 text-xs text-red">{{ erros.preco_unitario[0] }}</p>
      </div>
      <div v-if="quantidadeCripto" class="rounded-lg bg-stone-50 px-3 py-2 text-sm text-stone-600">
        Quantidade calculada: <strong>{{ quantidadeCripto.toFixed(8) }}</strong> {{ ativo.ticker }}
      </div>
      <p v-if="erros.quantidade" class="text-xs text-red">{{ erros.quantidade[0] }}</p>
    </template>

    <template v-else>
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
    </template>

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
