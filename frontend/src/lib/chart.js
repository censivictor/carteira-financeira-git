// Registro único dos elementos do Chart.js usados no dashboard (pizza,
// barra, linha). Importar este arquivo uma vez (main.js) antes de qualquer
// componente vue-chartjs ser montado.
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  PointElement,
  LineElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  ArcElement,
  BarElement,
  PointElement,
  LineElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
)

// Sem isso o Chart.js cai no font-family padrão dele (Helvetica-ish) — dá
// pra notar a costura entre o título do ChartCard (Manrope) e os labels
// dentro do gráfico. Cores também alinhadas à paleta stone do resto do app
// em vez do cinza genérico default.
ChartJS.defaults.font.family = "'Manrope', ui-sans-serif, system-ui, sans-serif"
ChartJS.defaults.color = '#78716c' // stone-500
ChartJS.defaults.borderColor = '#e7e5e4' // stone-200
ChartJS.defaults.plugins.tooltip.backgroundColor = '#292524' // stone-800
ChartJS.defaults.plugins.tooltip.padding = 10
ChartJS.defaults.plugins.tooltip.cornerRadius = 8
ChartJS.defaults.plugins.tooltip.titleFont = { family: "'Manrope', ui-sans-serif, system-ui, sans-serif", weight: '600' }
ChartJS.defaults.plugins.tooltip.bodyFont = { family: "'Manrope', ui-sans-serif, system-ui, sans-serif" }

// Paleta da carteira, na ordem que costumamos usar nos gráficos (pizzas,
// barras de comparação etc.) — mesmas cores do tailwind.config via @theme.
export const PALETA = ['#911440', '#f6464a', '#f68b7b', '#ffb48f', '#c0b19e']
