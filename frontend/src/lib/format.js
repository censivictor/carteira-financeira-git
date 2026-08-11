export function formatarMoeda(v) {
  if (v === null || v === undefined) return '—'
  return `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
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
