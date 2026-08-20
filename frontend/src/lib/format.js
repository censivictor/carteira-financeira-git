// Prefixo fixo em vez de Intl.NumberFormat({style:'currency'}) de propósito:
// o app é BRL-first (custo de aquisição, totais, orçamento — tudo sempre em
// BRL, ver investimentos/models.py::Ativo.moeda), então só o preço/valor
// atual de cripto eventualmente pede outro símbolo — por isso o parâmetro
// `moeda` é opcional e default BRL em toda chamada existente.
const SIMBOLOS = { BRL: 'R$', USD: 'US$', EUR: '€' }

export function formatarMoeda(v, moeda = 'BRL') {
  if (v === null || v === undefined) return '—'
  const simbolo = SIMBOLOS[moeda] || moeda
  return `${simbolo} ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// Preço unitário de cripto pode ser uma fração de centavo (ex: R$
// 0,00005971) — com formatarMoeda isso viraria "R$ 0,00", sem sentido.
// Mostra até 8 casas decimais (mesma precisão do backend), cortando os
// zeros à direita que sobrarem.
export function formatarMoedaPrecisa(v, moeda = 'BRL') {
  if (v === null || v === undefined) return '—'
  const simbolo = SIMBOLOS[moeda] || moeda
  return `${simbolo} ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`
}

export function formatarPct(v, casas = 2) {
  if (v === null || v === undefined) return '—'
  return `${v.toFixed(casas)}%`
}

export function formatarData(iso) {
  if (!iso) return '—'
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}
