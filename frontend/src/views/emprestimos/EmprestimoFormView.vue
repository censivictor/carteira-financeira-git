<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { LoaderCircle } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const id = route.params.id || null
const editando = computed(() => !!id)

const form = ref({
  descricao: '',
  valor_total: '',
  taxa_juros: '',
  periodo_taxa: 'MENSAL',
  sistema_amortizacao: 'PRICE',
  numero_parcelas: '',
  data_primeira_parcela: '',
})
const erros = ref({})
const salvando = ref(false)
const carregando = ref(true)
// Depois que a 1ª parcela é paga, o back trava valor/taxa/prazo/sistema —
// só a descrição continua editável (ver EmprestimoSerializer.validate).
const travado = ref(false)

onMounted(async () => {
  if (editando.value) {
    const e = await api.get(`/emprestimos/${id}/`)
    form.value = {
      descricao: e.descricao,
      valor_total: e.valor_total,
      taxa_juros: e.taxa_juros,
      periodo_taxa: e.periodo_taxa,
      sistema_amortizacao: e.sistema_amortizacao,
      numero_parcelas: e.numero_parcelas,
      data_primeira_parcela: e.data_primeira_parcela,
    }
    travado.value = e.parcelas_pagas_count > 0
  }
  carregando.value = false
})

async function salvar() {
  erros.value = {}
  salvando.value = true
  try {
    if (editando.value) {
      await api.patch(`/emprestimos/${id}/`, form.value)
    } else {
      await api.post('/emprestimos/', form.value)
    }
    router.push('/emprestimos')
  } catch (e) {
    erros.value = e.data || {}
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-md space-y-4">
    <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">{{ editando ? 'Editar empréstimo' : 'Novo empréstimo' }}</h1>

    <div v-if="carregando" class="flex h-40 items-center justify-center text-stone-400">
      <LoaderCircle :size="24" class="animate-spin" />
    </div>

    <form v-else class="card space-y-4" @submit.prevent="salvar">
      <p v-if="travado" class="rounded-lg bg-peach/15 px-3 py-2 text-xs text-wine">
        Já tem parcela paga nesse empréstimo — valor, juros, prazo e sistema não dá mais pra mudar (só a descrição).
      </p>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Descrição</label>
        <input v-model="form.descricao" type="text" placeholder="Ex: Financiamento do carro" class="input" required />
        <p v-if="erros.descricao" class="mt-1 text-xs text-red">{{ erros.descricao[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor total (R$)</label>
        <input v-model="form.valor_total" type="number" step="any" min="0.01" class="input" required :disabled="travado" />
        <p v-if="erros.valor_total" class="mt-1 text-xs text-red">{{ erros.valor_total[0] }}</p>
      </div>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Juros</label>
          <input v-model="form.taxa_juros" type="number" step="any" min="0" placeholder="Ex: 1,5" class="input" required :disabled="travado" />
          <p v-if="erros.taxa_juros" class="mt-1 text-xs text-red">{{ erros.taxa_juros[0] }}</p>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Período</label>
          <select v-model="form.periodo_taxa" class="input" :disabled="travado">
            <option value="MENSAL">Ao mês</option>
            <option value="ANUAL">Ao ano</option>
          </select>
        </div>
      </div>
      <p class="-mt-2 text-xs text-stone-400">Se a taxa for ao ano, o sistema converte pra mensal automaticamente (juros compostos) pra montar as parcelas.</p>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Sistema de amortização</label>
        <select v-model="form.sistema_amortizacao" class="input" :disabled="travado">
          <option value="PRICE">Price (parcela fixa)</option>
          <option value="SAC">SAC (parcela decrescente)</option>
        </select>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Número de parcelas</label>
        <input v-model="form.numero_parcelas" type="number" min="1" class="input" required :disabled="travado" />
        <p v-if="erros.numero_parcelas" class="mt-1 text-xs text-red">{{ erros.numero_parcelas[0] }}</p>
      </div>

      <div>
        <label class="mb-1.5 block text-sm font-medium text-stone-700">Data da 1ª parcela</label>
        <input v-model="form.data_primeira_parcela" type="date" class="input" required :disabled="travado" />
        <p v-if="erros.data_primeira_parcela" class="mt-1 text-xs text-red">{{ erros.data_primeira_parcela[0] }}</p>
      </div>

      <p v-if="erros.non_field_errors" class="text-xs text-red">{{ erros.non_field_errors[0] }}</p>

      <div class="flex gap-2 pt-2">
        <button type="submit" class="btn-primary" :disabled="salvando">
          <LoaderCircle v-if="salvando" :size="16" class="animate-spin" />
          Salvar
        </button>
        <RouterLink to="/emprestimos" class="btn-secondary">Cancelar</RouterLink>
      </div>
    </form>
  </div>
</template>
