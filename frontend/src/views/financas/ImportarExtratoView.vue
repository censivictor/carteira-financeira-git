<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/lib/api'
import { parseCsv, parseValorBR, parseDataBR } from '@/lib/csv'
import { formatarMoeda, formatarData } from '@/lib/format'
import { ArrowLeft, Upload, LoaderCircle } from '@lucide/vue'

// etapas: 'upload' -> 'mapear' -> 'preview' -> 'resultado'
const etapa = ref('upload')
const erroArquivo = ref('')
const categorias = ref([])

const headers = ref([])
const rows = ref([])
const mapeamento = ref({ data: '', descricao: '', valor: '' })

const linhas = ref([]) // [{id, data, descricao, valor, tipo, incluir, categoria, invalida}]
const categoriaPadrao = ref('')
const importando = ref(false)
const resultado = ref(null)
const erroImportacao = ref('')

onMounted(async () => {
  categorias.value = await api.get('/financas/categorias/')
})

function pistaColuna(header, palavras) {
  const h = header.toLowerCase()
  return palavras.some((p) => h.includes(p))
}

function aoEscolherArquivo(ev) {
  erroArquivo.value = ''
  const arquivo = ev.target.files[0]
  if (!arquivo) return

  const leitor = new FileReader()
  leitor.onload = () => {
    const { headers: h, rows: r } = parseCsv(String(leitor.result))
    if (!h.length || !r.length) {
      erroArquivo.value = 'Não consegui ler nenhuma linha desse CSV.'
      return
    }
    headers.value = h
    rows.value = r
    mapeamento.value = {
      data: h.findIndex((x) => pistaColuna(x, ['data', 'date'])),
      descricao: h.findIndex((x) => pistaColuna(x, ['descri', 'histor', 'lançamento', 'lancamento', 'memo'])),
      valor: h.findIndex((x) => pistaColuna(x, ['valor', 'amount', 'value'])),
    }
    for (const campo in mapeamento.value) {
      if (mapeamento.value[campo] === -1) mapeamento.value[campo] = ''
    }
    etapa.value = 'mapear'
  }
  leitor.onerror = () => { erroArquivo.value = 'Não consegui ler esse arquivo.' }
  leitor.readAsText(arquivo, 'utf-8')
}

const mapeamentoCompleto = computed(() =>
  mapeamento.value.data !== '' && mapeamento.value.descricao !== '' && mapeamento.value.valor !== ''
)

function processarLinhas() {
  const iData = Number(mapeamento.value.data)
  const iDescricao = Number(mapeamento.value.descricao)
  const iValor = Number(mapeamento.value.valor)

  linhas.value = rows.value.map((cols, idx) => {
    const dataIso = parseDataBR(cols[iData])
    const valorNum = parseValorBR(cols[iValor])
    const descricao = (cols[iDescricao] || '').trim()
    const invalida = !dataIso || valorNum === null || valorNum === 0 || !descricao
    return {
      id: idx,
      data: dataIso,
      descricao,
      valor: valorNum !== null ? Math.abs(valorNum) : null,
      tipo: valorNum !== null && valorNum < 0 ? 'DESPESA' : 'RECEITA',
      incluir: !invalida,
      categoria: '',
      invalida,
    }
  })
  etapa.value = 'preview'
}

function aplicarCategoriaPadrao() {
  if (!categoriaPadrao.value) return
  for (const l of linhas.value) {
    if (l.tipo === 'DESPESA' && !l.invalida) l.categoria = categoriaPadrao.value
  }
}

const totalIncluidas = computed(() => linhas.value.filter((l) => l.incluir).length)
const despesasSemCategoria = computed(() =>
  linhas.value.some((l) => l.incluir && l.tipo === 'DESPESA' && !l.categoria)
)

async function confirmarImportacao() {
  erroImportacao.value = ''
  importando.value = true
  const despesas = linhas.value
    .filter((l) => l.incluir && l.tipo === 'DESPESA')
    .map((l) => ({ descricao: l.descricao, valor: l.valor, data: l.data, categoria: l.categoria }))
  const receitas = linhas.value
    .filter((l) => l.incluir && l.tipo === 'RECEITA')
    .map((l) => ({ descricao: l.descricao, valor: l.valor, data: l.data }))

  try {
    resultado.value = await api.post('/financas/importar/', { despesas, receitas })
    etapa.value = 'resultado'
  } catch (e) {
    erroImportacao.value = e.data?.detail || 'Não foi possível importar — tenta de novo.'
  } finally {
    importando.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <div>
      <RouterLink to="/financas/despesas" class="mb-1 flex items-center gap-1 text-sm text-stone-400 hover:text-wine">
        <ArrowLeft :size="14" /> Despesas
      </RouterLink>
      <h1 class="text-2xl font-bold text-stone-800">Importar extrato</h1>
    </div>

    <!-- Upload -->
    <div v-if="etapa === 'upload'" class="card space-y-4">
      <p class="text-sm text-stone-500">
        Envie um CSV exportado do seu banco. Valor negativo (ou entre parênteses) vira despesa; valor positivo vira receita.
      </p>
      <label class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-stone-300 px-6 py-10 text-stone-500 hover:border-wine/40 hover:text-wine">
        <Upload :size="24" />
        <span class="text-sm font-medium">Clique pra escolher um arquivo .csv</span>
        <input type="file" accept=".csv,text/csv" class="hidden" @change="aoEscolherArquivo" />
      </label>
      <p v-if="erroArquivo" class="text-sm text-red">{{ erroArquivo }}</p>
    </div>

    <!-- Mapeamento de colunas -->
    <div v-else-if="etapa === 'mapear'" class="card space-y-4">
      <h3 class="text-sm font-semibold text-stone-700">Qual coluna é qual?</h3>
      <p class="text-xs text-stone-400">{{ rows.length }} linhas encontradas. Já tentei adivinhar — confira antes de continuar.</p>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Data</label>
          <select v-model="mapeamento.data" class="input">
            <option value="" disabled>Selecione</option>
            <option v-for="(h, i) in headers" :key="i" :value="i">{{ h }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Descrição</label>
          <select v-model="mapeamento.descricao" class="input">
            <option value="" disabled>Selecione</option>
            <option v-for="(h, i) in headers" :key="i" :value="i">{{ h }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Valor</label>
          <select v-model="mapeamento.valor" class="input">
            <option value="" disabled>Selecione</option>
            <option v-for="(h, i) in headers" :key="i" :value="i">{{ h }}</option>
          </select>
        </div>
      </div>

      <div v-if="rows[0]" class="overflow-x-auto rounded-lg bg-stone-50 p-3 text-xs text-stone-500">
        <strong class="mb-1 block text-stone-600">Prévia da 1ª linha:</strong>
        {{ headers.map((h, i) => `${h}: ${rows[0][i]}`).join(' · ') }}
      </div>

      <button type="button" class="btn-primary" :disabled="!mapeamentoCompleto" @click="processarLinhas">Continuar</button>
    </div>

    <!-- Preview editável -->
    <div v-else-if="etapa === 'preview'" class="space-y-4">
      <div class="card flex flex-wrap items-end gap-3">
        <div class="flex-1">
          <label class="mb-1.5 block text-sm font-medium text-stone-700">Categoria padrão pras despesas</label>
          <select v-model="categoriaPadrao" class="input" @change="aplicarCategoriaPadrao">
            <option value="" disabled>Selecione</option>
            <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
          </select>
        </div>
        <p class="text-xs text-stone-400">Aplica em todas as despesas marcadas abaixo — dá pra trocar linha a linha depois.</p>
      </div>

      <div class="card overflow-x-auto">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-stone-700">{{ totalIncluidas }} de {{ linhas.length }} linhas selecionadas</h3>
        </div>
        <table class="w-full min-w-[720px] text-sm">
          <thead>
            <tr class="border-b border-stone-200 text-left text-stone-500">
              <th class="pb-2"></th>
              <th class="pb-2 font-medium">Data</th>
              <th class="pb-2 font-medium">Descrição</th>
              <th class="pb-2 text-right font-medium">Valor</th>
              <th class="pb-2 font-medium">Tipo</th>
              <th class="pb-2 font-medium">Categoria</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in linhas" :key="l.id" class="border-b border-stone-100 last:border-0" :class="l.invalida ? 'opacity-50' : ''">
              <td class="py-2">
                <input v-model="l.incluir" type="checkbox" :disabled="l.invalida" class="h-4 w-4 rounded border-stone-300 text-wine focus:ring-wine/40" />
              </td>
              <td class="py-2">{{ l.data ? formatarData(l.data) : '— data inválida' }}</td>
              <td class="py-2">{{ l.descricao || '— sem descrição' }}</td>
              <td class="py-2 text-right">{{ l.valor !== null ? formatarMoeda(l.valor) : '— valor inválido' }}</td>
              <td class="py-2">
                <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="l.tipo === 'DESPESA' ? 'bg-red/10 text-red' : 'bg-emerald-100 text-emerald-700'">
                  {{ l.tipo === 'DESPESA' ? 'Despesa' : 'Receita' }}
                </span>
              </td>
              <td class="py-2">
                <select v-if="l.tipo === 'DESPESA' && l.incluir" v-model="l.categoria" class="input py-1 text-xs">
                  <option value="" disabled>Selecione</option>
                  <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
                </select>
                <span v-else class="text-stone-400">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="despesasSemCategoria" class="text-sm text-red">Toda despesa selecionada precisa de uma categoria.</p>
      <p v-if="erroImportacao" class="text-sm text-red">{{ erroImportacao }}</p>

      <div class="flex gap-2">
        <button
          type="button"
          class="btn-primary"
          :disabled="!totalIncluidas || despesasSemCategoria || importando"
          @click="confirmarImportacao"
        >
          <LoaderCircle v-if="importando" :size="16" class="animate-spin" />
          Confirmar importação
        </button>
        <button type="button" class="btn-secondary" @click="etapa = 'mapear'">Voltar</button>
      </div>
    </div>

    <!-- Resultado -->
    <div v-else-if="etapa === 'resultado'" class="card space-y-3">
      <h3 class="text-lg font-semibold text-stone-800">Importação concluída</h3>
      <ul class="space-y-1 text-sm text-stone-600">
        <li>{{ resultado.criadas_despesas }} despesa(s) criada(s){{ resultado.duplicadas_despesas ? ` (${resultado.duplicadas_despesas} já existiam, ignoradas)` : '' }}</li>
        <li>{{ resultado.criadas_receitas }} receita(s) criada(s){{ resultado.duplicadas_receitas ? ` (${resultado.duplicadas_receitas} já existiam, ignoradas)` : '' }}</li>
      </ul>
      <div v-if="resultado.erros.length" class="rounded-lg bg-red/10 p-3 text-xs text-red">
        <strong class="block">{{ resultado.erros.length }} linha(s) com problema:</strong>
        <ul class="mt-1 list-inside list-disc">
          <li v-for="(e, i) in resultado.erros" :key="i">{{ e }}</li>
        </ul>
      </div>
      <div class="flex gap-2 pt-2">
        <RouterLink to="/financas/despesas" class="btn-primary">Ver despesas</RouterLink>
        <RouterLink to="/financas/receitas" class="btn-secondary">Ver receitas</RouterLink>
      </div>
    </div>
  </div>
</template>
