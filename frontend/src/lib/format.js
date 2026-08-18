export function formatarMoeda(v) {
  if (v === null || v === undefined) return '—'
  return `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// Preço unitário de cripto pode ser uma fração de centavo (ex: R$
// 0,00005971) — com formatarMoeda isso viraria "R$ 0,00", sem sentido.
// Mostra até 8 casas decimais (mesma precisão do backend), cortando os
// zeros à direita que sobrarem.
export function formatarMoedaPrecisa(v) {
  if (v === null || v === undefined) return '—'
  return `R$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}`
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
