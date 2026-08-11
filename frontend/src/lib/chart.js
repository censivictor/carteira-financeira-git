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

// Paleta da carteira, na ordem que costumamos usar nos gráficos (pizzas,
// barras de comparação etc.) — mesmas cores do tailwind.config via @theme.
export const PALETA = ['#911440', '#f6464a', '#f68b7b', '#ffb48f', '#c0b19e']
