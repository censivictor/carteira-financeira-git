// Exportação simples de CSV pro navegador — sem lib externa. Usa ';' como
// separador (padrão que o Excel brasileiro reconhece de cara) e um BOM UTF-8
// no início, senão acento quebra ao abrir no Excel no Windows.

function escaparCelula(valor) {
  const texto = valor === null || valor === undefined ? '' : String(valor)
  if (/[;"\n]/.test(texto)) {
    return `"${texto.replace(/"/g, '""')}"`
  }
  return texto
}

/**
 * @param {string} nomeArquivo - ex: 'despesas-2026-08.csv'
 * @param {string[]} colunas - cabeçalho, ex: ['Data', 'Descrição', 'Valor']
 * @param {Array<Array<string|number>>} linhas - cada linha na mesma ordem das colunas
 */
// --- Import de extrato: parsing de CSV genérico (não sabemos o formato
// exato do banco de antemão) — delimitador ';' ou ',' auto-detectado,
// suporta campo entre aspas com delimitador/aspas escapada dentro.

function detectarDelimitador(linhaCabecalho) {
  const pontoVirgula = (linhaCabecalho.match(/;/g) || []).length
  const virgula = (linhaCabecalho.match(/,/g) || []).length
  return pontoVirgula >= virgula ? ';' : ','
}

function parseLinhaCsv(linha, delimitador) {
  const campos = []
  let atual = ''
  let dentroAspas = false
  for (let i = 0; i < linha.length; i++) {
    const ch = linha[i]
    if (ch === '"') {
      if (dentroAspas && linha[i + 1] === '"') {
        atual += '"'
        i++
      } else {
        dentroAspas = !dentroAspas
      }
    } else if (ch === delimitador && !dentroAspas) {
      campos.push(atual.trim())
      atual = ''
    } else {
      atual += ch
    }
  }
  campos.push(atual.trim())
  return campos
}

/** @returns {{headers: string[], rows: string[][]}} */
export function parseCsv(texto) {
  const linhas = texto.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').filter((l) => l.trim() !== '')
  if (!linhas.length) return { headers: [], rows: [] }
  const delimitador = detectarDelimitador(linhas[0])
  const headers = parseLinhaCsv(linhas[0], delimitador)
  const rows = linhas.slice(1).map((l) => parseLinhaCsv(l, delimitador))
  return { headers, rows }
}

/** "1.234,56" ou "1234.56" ou "(100,00)" (negativo) -> number. null se inválido. */
export function parseValorBR(texto) {
  if (typeof texto === 'number') return texto
  let limpo = String(texto ?? '').trim().replace(/^R\$\s*/i, '')
  if (!limpo) return null
  const negativo = limpo.startsWith('-') || (limpo.startsWith('(') && limpo.endsWith(')'))
  limpo = limpo.replace(/[()]/g, '').replace(/^-/, '')
  if (limpo.includes(',') && limpo.includes('.')) {
    limpo = limpo.replace(/\./g, '').replace(',', '.')
  } else if (limpo.includes(',')) {
    limpo = limpo.replace(',', '.')
  }
  const numero = parseFloat(limpo)
  if (Number.isNaN(numero)) return null
  return negativo ? -numero : numero
}

/** "DD/MM/YYYY", "DD-MM-YYYY" ou já "YYYY-MM-DD" -> "YYYY-MM-DD". null se inválido. */
export function parseDataBR(texto) {
  const t = String(texto ?? '').trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t
  const m = t.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/)
  if (m) {
    const [, dia, mes, ano] = m
    return `${ano}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`
  }
  return null
}

export function exportarCsv(nomeArquivo, colunas, linhas) {
  const conteudo = [colunas, ...linhas]
    .map((linha) => linha.map(escaparCelula).join(';'))
    .join('\r\n')

  const blob = new Blob(['﻿' + conteudo], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nomeArquivo
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
