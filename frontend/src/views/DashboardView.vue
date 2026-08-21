<script setup>
import { ref, computed, onMounted } from 'vue'
import { Pie, Bar, Line } from 'vue-chartjs'
import { api } from '@/lib/api'
import { PALETA } from '@/lib/chart'
import { formatarMoeda, formatarMoedaPrecisa, formatarPct, formatarData } from '@/lib/format'
import MetricCard from '@/components/MetricCard.vue'
import BudgetBar from '@/components/BudgetBar.vue'
import ChartCard from '@/components/ChartCard.vue'
import { LoaderCircle, TriangleAlert } from '@lucide/vue'

const dados = ref(null)
const carregando = ref(true)
const erro = ref('')

onMounted(async () => {
  try {
    dados.value = await api.get('/dashboard/')
  } catch {
    erro.value = 'Não deu pra carregar o dashboard agora. Tenta recarregar a página.'
  } finally {
    carregando.value = false
  }
})

const opcoesGrafico = { responsive: true, maintainAspectRatio: false }

const chartAlocacao = computed(() => ({
  labels: dados.value.alocacao.map((a) => a.ticker),
  datasets: [{ data: dados.value.alocacao.map((a) => a.valor_atual), backgroundColor: PALETA }],
}))

const chartGastos = computed(() => ({
  labels: dados.value.gastos_por_categoria.map((g) => g.categoria__nome),
  datasets: [{
    data: dados.value.gastos_por_categoria.map((g) => g.total),
    backgroundColor: dados.value.gastos_por_categoria.map((g, i) => g.categoria__cor || PALETA[i % PALETA.length]),
  }],
}))

const chartEvolucao = computed(() => ({
  labels: dados.value.evolucao_labels,
  datasets: [
    { label: 'Receita', data: dados.value.evolucao_receitas, backgroundColor: '#10b981' },
    { label: 'Despesa', data: dados.value.evolucao_despesas, backgroundColor: '#f6464a' },
    {
      label: 'Saldo', data: dados.value.evolucao_saldo, type: 'line',
      borderColor: '#911440', backgroundColor: '#911440', tension: 0.3,
    },
  ],
}))

const chartPatrimonio = computed(() => ({
  labels: dados.value.patrimonio_historico_labels,
  datasets: [{
    label: 'Patrimônio', data: dados.value.patrimonio_historico_valores,
    borderColor: '#911440', backgroundColor: 'rgba(145,20,64,0.12)', fill: true, tension: 0.3,
  }],
}))

const chartComparacao = computed(() => ({
  labels: dados.value.comparacao_labels,
  datasets: [{
    data: dados.value.comparacao_valores,
    backgroundColor: ['#10b981', '#911440', '#ffb48f'],
  }],
}))

// Mesmos limiares visuais do BudgetBar (80%/100%) — categorias estouradas
// aparecem primeiro, "quase lá" depois.
const categoriasEstouradas = computed(() => {
  if (!dados.value) return []
  return dados.value.orcamentos
    .filter((o) => o.pct >= 80)
    .sort((a, b) => b.pct - a.pct)
})

const opcoesComparacao = {
  ...opcoesGrafico,
  indexAxis: 'y',
  plugins: { legend: { display: false } },
  scales: { x: { ticks: { callback: (v) => v + '%' } } },
}
</script>

<template>
  <div v-if="carregando" class="flex h-64 items-center justify-center text-stone-400">
    <LoaderCircle :size="28" class="animate-spin" />
  </div>

  <div v-else-if="erro" class="card text-red">{{ erro }}</div>

  <div v-else class="space-y-4">
    <h1 class="text-3xl font-extrabold tracking-tight text-stone-800">Dashboard</h1>

    <!-- Alerta de orçamento -->
    <div v-if="categoriasEstouradas.length" class="card border-l-4 border-l-red bg-red/5">
      <div class="flex items-start gap-3">
        <TriangleAlert :size="20" class="mt-0.5 shrink-0 text-red" />
        <div class="flex-1">
          <h3 class="text-sm font-semibold text-stone-800">Atenção ao orçamento deste mês</h3>
          <ul class="mt-1.5 space-y-1 text-sm text-stone-600">
            <li v-for="o in categoriasEstouradas" :key="o.categoria">
              <strong :class="o.pct >= 100 ? 'text-red' : 'text-wine'">{{ o.categoria }}</strong>:
              {{ formatarMoeda(o.total) }} de {{ formatarMoeda(o.orcamento) }}
              ({{ o.pct.toFixed(0) }}%{{ o.pct >= 100 ? ' — estourou' : ' — quase no limite' }})
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Métricas principais -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        class="animate-rise-in"
        style="animation-delay: 0ms"
        label="Patrimônio investido"
        :value="formatarMoeda(dados.patrimonio_total)"
      />
      <MetricCard
        class="animate-rise-in"
        style="animation-delay: 60ms"
        label="Ganho/perda da carteira"
        :value="formatarPct(dados.ganho_perda_total_pct)"
        :variant="dados.ganho_perda_total_pct >= 0 ? 'gain' : 'loss'"
      />
      <MetricCard
        class="animate-rise-in"
        style="animation-delay: 120ms"
        label="Saldo do mês (renda - gastos)"
        :value="formatarMoeda(dados.saldo_mes_atual)"
        :variant="dados.saldo_mes_atual >= 0 ? 'gain' : 'loss'"
      />
      <MetricCard
        class="animate-rise-in"
        style="animation-delay: 180ms"
        label="% da renda gasto no mês"
        :value="dados.pct_gasto_da_renda !== null ? formatarPct(dados.pct_gasto_da_renda, 1) : '—'"
      />
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <MetricCard label="Proventos recebidos (mês)" :value="formatarMoeda(dados.proventos_mes)" variant="gain" />
      <MetricCard
        label="Retorno total (ganho de capital + proventos)"
        :value="formatarPct(dados.retorno_total_pct)"
        :variant="dados.retorno_total_pct >= 0 ? 'gain' : 'loss'"
      />
    </div>

    <div v-if="dados.divida_total > 0" class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <MetricCard label="Patrimônio líquido (investido - dívidas)" :value="formatarMoeda(dados.patrimonio_liquido)" />
      <MetricCard label="Dívida em empréstimos" :value="formatarMoeda(dados.divida_emprestimos)" variant="loss" />
      <MetricCard label="Faturas de cartão em aberto" :value="formatarMoeda(dados.divida_cartoes)" variant="loss" hint="Compras já feitas, ainda não pagas." />
    </div>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div class="card">
        <div class="text-sm text-stone-500">Receita deste mês</div>
        <div class="mt-1 text-xl font-bold tracking-tight tabular-nums text-stone-800">{{ formatarMoeda(dados.receita_mes_atual) }}</div>
        <span
          v-if="dados.variacao_receita_pct !== null"
          class="mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
          :class="dados.variacao_receita_pct >= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-red/10 text-red'"
        >
          {{ formatarPct(dados.variacao_receita_pct, 1) }} vs mês anterior
        </span>
        <span v-else class="mt-2 inline-block rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-400">sem dados do mês anterior</span>
      </div>
      <div class="card">
        <div class="text-sm text-stone-500">Despesas deste mês</div>
        <div class="mt-1 text-xl font-bold tracking-tight tabular-nums text-stone-800">{{ formatarMoeda(dados.despesa_mes_atual) }}</div>
        <span
          v-if="dados.variacao_despesa_pct !== null"
          class="mt-2 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
          :class="dados.variacao_despesa_pct <= 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-red/10 text-red'"
        >
          {{ formatarPct(dados.variacao_despesa_pct, 1) }} vs mês anterior
        </span>
        <span v-else class="mt-2 inline-block rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-400">sem dados do mês anterior</span>
      </div>
    </div>

    <!-- Gráficos de pizza -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <ChartCard title="Alocação da carteira" :empty="!dados.tem_ativos" empty-text="Nenhum ativo cadastrado ainda.">
        <Pie :data="chartAlocacao" :options="opcoesGrafico" />
        <template #empty-link>
          <RouterLink to="/investimentos/novo" class="font-medium text-wine hover:underline">Adicionar ativo</RouterLink>
        </template>
      </ChartCard>
      <ChartCard title="Gastos por categoria (mês atual)" :empty="!dados.gastos_por_categoria.length" empty-text="Nenhuma despesa lançada este mês.">
        <Pie :data="chartGastos" :options="opcoesGrafico" />
        <template #empty-link>
          <RouterLink to="/financas/despesas/nova" class="font-medium text-wine hover:underline">Adicionar despesa</RouterLink>
        </template>
      </ChartCard>
    </div>

    <!-- Alocação-alvo -->
    <div v-if="dados.alocacao_alvo.length" class="card overflow-x-auto">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-stone-700">Alocação-alvo</h3>
        <RouterLink to="/investimentos/alocacao" class="text-xs font-medium text-wine hover:underline">Editar alvo</RouterLink>
      </div>
      <table class="w-full min-w-[560px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Classe</th>
            <th class="pb-2 text-right font-medium">Atual</th>
            <th class="pb-2 text-right font-medium">Alvo</th>
            <th class="pb-2 text-right font-medium">Desvio</th>
            <th class="pb-2 font-medium">Sugestão</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in dados.alocacao_alvo" :key="a.tipo" class="border-b border-stone-100 last:border-0">
            <td class="py-2 font-medium text-stone-700">{{ a.tipo_display }}</td>
            <td class="py-2 text-right">{{ formatarPct(a.pct_atual, 1) }}</td>
            <td class="py-2 text-right text-stone-500">{{ formatarPct(a.pct_alvo, 1) }}</td>
            <td class="py-2 text-right font-medium" :class="Math.abs(a.desvio_pct) < 2 ? 'text-stone-400' : a.desvio_pct > 0 ? 'text-red' : 'text-wine'">
              {{ a.desvio_pct > 0 ? '+' : '' }}{{ formatarPct(a.desvio_pct, 1) }}
            </td>
            <td class="py-2 text-stone-500">
              <span v-if="Math.abs(a.desvio_pct) < 2">dentro do alvo</span>
              <span v-else-if="a.valor_para_ajustar > 0">comprar ~{{ formatarMoeda(a.valor_para_ajustar) }}</span>
              <span v-else>reduzir ~{{ formatarMoeda(-a.valor_para_ajustar) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Orçamento por categoria -->
    <div v-if="dados.orcamentos.length" class="card">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Orçamento por categoria (mês atual)</h3>
      <BudgetBar
        v-for="o in dados.orcamentos"
        :key="o.categoria"
        :categoria="o.categoria"
        :total="o.total"
        :orcamento="o.orcamento"
        :pct="o.pct"
      />
      <RouterLink to="/financas/categorias" class="mt-2 inline-block text-xs font-medium text-wine hover:underline">
        Gerenciar categorias e orçamentos
      </RouterLink>
    </div>

    <!-- Comparação com o mercado -->
    <div v-if="dados.data_inicio_investimentos" class="card">
      <h3 class="text-sm font-semibold text-stone-700">Comparação com o mercado</h3>
      <p class="mb-3 text-xs text-stone-400">Desde {{ formatarData(dados.data_inicio_investimentos) }} (1ª transação de Ação/FII/Cripto)</p>
      <div class="h-48">
        <Bar :data="chartComparacao" :options="opcoesComparacao" />
      </div>
      <ul class="mt-3 space-y-1 text-sm">
        <li><strong class="text-stone-700">Sua carteira (Ação/FII/Cripto):</strong> {{ formatarPct(dados.retorno_mercado_pct) }}</li>
        <li><strong class="text-stone-700">CDI:</strong> {{ dados.variacao_cdi_pct !== null ? formatarPct(dados.variacao_cdi_pct) : 'indisponível no momento' }}</li>
        <li>
          <strong class="text-stone-700">Ibovespa:</strong>
          <template v-if="dados.comparacao_ibovespa">
            {{ formatarPct(dados.comparacao_ibovespa.variacao_pct) }}
            <span v-if="dados.comparacao_ibovespa.periodo_limitado" class="text-stone-400">
              (desde {{ formatarData(dados.comparacao_ibovespa.data_inicio_real) }} — limite do plano gratuito da API, máximo 3 meses)
            </span>
          </template>
          <template v-else>indisponível no momento</template>
        </li>
      </ul>
    </div>

    <!-- Evolução mensal -->
    <ChartCard title="Evolução mensal (últimos 12 meses)">
      <Bar :data="chartEvolucao" :options="opcoesGrafico" />
    </ChartCard>

    <!-- Patrimônio histórico -->
    <ChartCard
      title="Patrimônio ao longo do tempo"
      :empty="dados.patrimonio_historico_labels.length <= 1"
      empty-text="Histórico começa a partir de agora — volte aqui em outro dia pra ver a evolução."
    >
      <Line :data="chartPatrimonio" :options="opcoesGrafico" />
    </ChartCard>

    <!-- Tabela de ativos -->
    <div class="card overflow-x-auto">
      <h3 class="mb-3 text-sm font-semibold text-stone-700">Ativos</h3>
      <table class="w-full min-w-[640px] text-sm">
        <thead>
          <tr class="border-b border-stone-200 text-left text-stone-500">
            <th class="pb-2 font-medium">Ticker</th>
            <th class="pb-2 font-medium">Tipo</th>
            <th class="pb-2 text-right font-medium">Quantidade</th>
            <th class="pb-2 text-right font-medium">Preço atual</th>
            <th class="pb-2 text-right font-medium">Valor atual</th>
            <th class="pb-2 text-right font-medium">Ganho/perda</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in dados.alocacao" :key="a.ticker" class="border-b border-stone-100 last:border-0">
            <td class="py-2 font-medium text-stone-800">{{ a.ticker }}</td>
            <td class="py-2 text-stone-500">{{ a.tipo }}</td>
            <td class="py-2 text-right text-stone-700">{{ a.quantidade ?? '—' }}</td>
            <td class="py-2 text-right text-stone-700">
              {{ a.preco_atual !== null ? (a.tipo_code === 'CRIPTO' ? formatarMoedaPrecisa(a.preco_atual) : formatarMoeda(a.preco_atual)) : '—' }}
              <span v-if="!a.cotacao_disponivel" class="ml-1 rounded-full bg-peach/30 px-2 py-0.5 text-[10px] text-wine">estimativa</span>
              <!-- preco_atual acima é sempre BRL (alimenta o total do patrimônio) — isso é só a leitura extra na moeda de exibição escolhida pro ativo -->
              <div v-if="a.preco_atual_nativo !== null" class="text-xs text-stone-400">
                ≈ {{ formatarMoedaPrecisa(a.preco_atual_nativo, a.moeda) }}
              </div>
            </td>
            <td class="py-2 text-right text-stone-700">{{ formatarMoeda(a.valor_atual) }}</td>
            <td class="py-2 text-right font-medium" :class="a.ganho_perda_pct >= 0 ? 'text-emerald-600' : 'text-red'">
              {{ formatarPct(a.ganho_perda_pct) }}
            </td>
          </tr>
          <tr v-if="!dados.alocacao.length">
            <td colspan="6" class="py-8 text-center text-stone-400">Nenhum ativo cadastrado.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
