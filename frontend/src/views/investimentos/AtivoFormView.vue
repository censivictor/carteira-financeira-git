<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/lib/api'
import AtivoAutocomplete from '@/components/AtivoAutocomplete.vue'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const ativoId = route.params.id || null
const editando = computed(() => !!ativoId)

const form = ref({
  ticker: '', nome: '', tipo: '', coingecko_id: '', moeda: 'BRL',
  indexador: '', taxa_contratada: '', valor_aplicado: '', data_aplicacao: '',
  ativo_flag: true,
})
const erros = ref({})
const salvando = ref(false)
const carregando = ref(editando.value)

const mostrarAcaoFii = computed(() => ['ACAO', 'FII'].includes(form.value.tipo))
const mostrarCripto = computed(() => form.value.tipo === 'CRIPTO')
const mostrarRendaFixa = computed(() => form.value.tipo === 'RENDA_FIXA')

onMounted(async () => {
  if (editando.value) {
    const a = await api.get(`/investimentos/ativos/${ativoId}/`)
    form.value = {
      ticker: a.ticker, nome: a.nome || '', tipo: a.tipo, coingecko_id: a.coingecko_id || '', moeda: a.moeda || 'BRL',
      indexador: a.indexador || '', taxa_contratada: a.taxa_contratada || '',
      valor_aplicado: a.valor_aplicado || '', data_aplicacao: a.data_aplicacao || '',
      ativo_flag: a.ativo_flag,
    }
    carregando.value = false
  }
})

function aoSelecionarTicker(item) {
  const partes = item.label.split(' — ')
  if (partes.length > 1 && !form.value.nome) form.value.nome = partes[1]
}

function aoSelecionarCripto(item) {
  const match = item.label.match(/^(.*) \(([A-Z0-9]+)\)$/)
  if (match) {
    if (!form.value.nome) form.value.nome = match[1]
    if (!form.value.ticker) form.value.ticker = match[2]
  }
}

async function salvar() {
  erros.value = {}
  salvando.value = true
  const payload = { ...form.value }
  // campos vazios ('') viram null pro backend não reclamar de tipo em branco
  for (const campo of ['coingecko_id', 'indexador', 'taxa_contratada', 'valor_aplicado', 'data_aplicacao']) {
    if (payload[campo] === '') payload[campo] = null
  }

  try {
    let ativo
    if (editando.value) {
      ativo = await api.patch(`/investimentos/ativos/${ativoId}/`, payload)
    } else {
      ativo = await api.post('/investimentos/ativos/', payload)
    }
    if (editando.value || ativo.tipo === 'RENDA_FIXA') {
      router.push('/investimentos')
    } else {
      router.push(`/investimentos/${ativo.id}`)
    }
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-xl space-y-4">
    <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">{{ editando ? 'Editar ativo' : 'Novo ativo' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Tipo</label>
        <select v-model="form.tipo" class="input" required>
          <option value="" disabled>Selecione</option>
          <option value="ACAO">Ação B3</option>
          <option value="FII">Fundo Imobiliário (FII)</option>
          <option value="CRIPTO">Criptomoeda</option>
          <option value="RENDA_FIXA">Renda Fixa (CDI/Selic/Prefixado)</option>
        </select>
        <p v-if="erros.tipo" class="mt-1 text-xs text-red">{{ erros.tipo[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Ticker</label>
        <AtivoAutocomplete
          v-if="mostrarAcaoFii"
          v-model="form.ticker"
          :tipo="form.tipo"
          placeholder="Digite pra buscar (ex: PETR4)"
          @select="aoSelecionarTicker"
        />
        <input v-else v-model="form.ticker" type="text" class="input" placeholder="BTC ou rótulo (renda fixa)" required />
        <p class="mt-1 text-xs text-stone-400">
          Código na B3, símbolo da cripto, ou (renda fixa) um rótulo livre — ex: CDB Banco X.
        </p>
        <p v-if="erros.ticker" class="mt-1 text-xs text-red">{{ erros.ticker[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Nome</label>
        <input v-model="form.nome" type="text" class="input" />
      </div>

      <div v-if="mostrarCripto">
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Criptomoeda (digite o nome pra buscar)</label>
        <AtivoAutocomplete v-model="form.coingecko_id" tipo="CRIPTO" placeholder='ex: digite "bitcoin"' @select="aoSelecionarCripto" />
        <p v-if="erros.coingecko_id" class="mt-1 text-xs text-red">{{ erros.coingecko_id[0] }}</p>
      </div>

      <div v-if="mostrarCripto">
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Moeda de exibição da cotação</label>
        <select v-model="form.moeda" class="input">
          <option value="BRL">Real (R$)</option>
          <option value="USD">Dólar (US$)</option>
          <option value="EUR">Euro (€)</option>
        </select>
        <p class="mt-1 text-xs text-stone-400">
          Só muda como o preço/valor atual é exibido — custo de aquisição e totais do patrimônio continuam sempre em BRL.
        </p>
        <p v-if="erros.moeda" class="mt-1 text-xs text-red">{{ erros.moeda[0] }}</p>
      </div>

      <template v-if="mostrarRendaFixa">
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Indexador</label>
          <select v-model="form.indexador" class="input">
            <option value="" disabled>Selecione</option>
            <option value="CDI">% do CDI</option>
            <option value="SELIC">% da Selic</option>
            <option value="PREFIXADO">Prefixado (taxa fixa ao ano)</option>
          </select>
          <p v-if="erros.indexador" class="mt-1 text-xs text-red">{{ erros.indexador[0] }}</p>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Taxa contratada (%)</label>
          <input v-model="form.taxa_contratada" type="number" step="any" class="input" />
          <p class="mt-1 text-xs text-stone-400">
            CDI/Selic: % do indexador (ex: 110 = 110% do CDI). Prefixado: taxa fixa ao ano (ex: 12.5).
          </p>
          <p v-if="erros.taxa_contratada" class="mt-1 text-xs text-red">{{ erros.taxa_contratada[0] }}</p>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor aplicado (R$)</label>
          <input v-model="form.valor_aplicado" type="number" step="any" class="input" />
          <p v-if="erros.valor_aplicado" class="mt-1 text-xs text-red">{{ erros.valor_aplicado[0] }}</p>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Data da aplicação</label>
          <input v-model="form.data_aplicacao" type="date" class="input" />
          <p v-if="erros.data_aplicacao" class="mt-1 text-xs text-red">{{ erros.data_aplicacao[0] }}</p>
        </div>
      </template>

      <label class="flex items-center gap-2 text-sm text-stone-700">
        <input v-model="form.ativo_flag" type="checkbox" class="h-4 w-4 rounded border-stone-300 text-wine focus:ring-wine/40" />
        Ativo (não arquivado)
      </label>

      <div v-if="mostrarAcaoFii || mostrarCripto" class="rounded-xl bg-peach/15 px-4 py-3 text-sm text-wine">
        Quantidade e preço médio são calculados automaticamente a partir das transações de compra/venda que você lança depois de salvar.
      </div>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/investimentos" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
