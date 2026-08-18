<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle, ArrowLeft } from '@lucide/vue'

const TIPOS = [
  { value: 'ACAO', label: 'Ação B3' },
  { value: 'FII', label: 'Fundo Imobiliário (FII)' },
  { value: 'CRIPTO', label: 'Criptomoeda' },
  { value: 'RENDA_FIXA', label: 'Renda Fixa' },
]

const percentuais = ref({ ACAO: '', FII: '', CRIPTO: '', RENDA_FIXA: '' })
const carregando = ref(true)
const salvando = ref(false)
const erro = ref('')
const salvo = ref(false)

const soma = computed(() =>
  TIPOS.reduce((total, t) => total + (Number(percentuais.value[t.value]) || 0), 0)
)

onMounted(async () => {
  const dados = await api.get('/investimentos/alocacao-alvo/')
  for (const t of TIPOS) {
    percentuais.value[t.value] = dados[t.value] ?? ''
  }
  carregando.value = false
})

async function salvar() {
  erro.value = ''
  salvo.value = false
  salvando.value = true
  const payload = {}
  for (const t of TIPOS) {
    if (percentuais.value[t.value] !== '') payload[t.value] = percentuais.value[t.value]
  }
  try {
    await api.put('/investimentos/alocacao-alvo/', payload)
    salvo.value = true
  } catch (e) {
    erro.value = e.data?.detail || 'Não foi possível salvar.'
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-6">
    <div>
      <RouterLink to="/investimentos" class="mb-1 flex items-center gap-1 text-sm text-stone-400 hover:text-wine">
        <ArrowLeft :size="14" /> Investimentos
      </RouterLink>
      <h1 class="text-2xl font-bold text-stone-800">Alocação-alvo</h1>
      <p class="mt-1 text-sm text-stone-500">
        Defina o % desejado de cada classe na sua carteira. O dashboard compara com a alocação atual e sugere ajuste.
      </p>
    </div>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div v-for="t in TIPOS" :key="t.value">
        <label class="mb-1.5 block text-sm font-medium text-stone-700">{{ t.label }} (%)</label>
        <input v-model="percentuais[t.value]" type="number" step="any" min="0" max="100" class="input" placeholder="0" />
      </div>

      <div class="flex items-center justify-between rounded-lg px-3 py-2 text-sm" :class="soma === 100 || soma === 0 ? 'bg-stone-50 text-stone-500' : 'bg-red/10 text-red'">
        <span>Soma dos percentuais</span>
        <strong>{{ soma }}%</strong>
      </div>
      <p class="text-xs text-stone-400">Deixe tudo em branco (soma 0%) pra desligar a comparação. Se preencher, a soma precisa dar exatamente 100%.</p>

      <p v-if="erro" class="text-sm text-red">{{ erro }}</p>
      <p v-if="salvo" class="text-sm text-emerald-600">Salvo! O dashboard já reflete a nova alocação-alvo.</p>

      <button type="submit" class="btn-primary w-full" :disabled="salvando || (soma !== 100 && soma !== 0)">
        <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
        Salvar
      </button>
    </form>
  </div>
</template>
