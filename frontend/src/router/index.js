import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { publica: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { publica: true },
  },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('@/views/SignupView.vue'),
    meta: { publica: true },
  },
  {
    path: '/app',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
  },
  {
    path: '/investimentos',
    name: 'ativo-list',
    component: () => import('@/views/investimentos/AtivoListView.vue'),
  },
  {
    path: '/investimentos/novo',
    name: 'ativo-create',
    component: () => import('@/views/investimentos/AtivoFormView.vue'),
  },
  {
    path: '/investimentos/:id/editar',
    name: 'ativo-update',
    component: () => import('@/views/investimentos/AtivoFormView.vue'),
  },
  {
    path: '/investimentos/alocacao',
    name: 'alocacao-alvo',
    component: () => import('@/views/investimentos/AlocacaoAlvoView.vue'),
  },
  {
    path: '/investimentos/:id',
    name: 'ativo-detail',
    component: () => import('@/views/investimentos/AtivoDetailView.vue'),
  },
  {
    path: '/financas/categorias',
    name: 'categoria-list',
    component: () => import('@/views/financas/CategoriaListView.vue'),
  },
  {
    path: '/financas/categorias/nova',
    name: 'categoria-create',
    component: () => import('@/views/financas/CategoriaFormView.vue'),
  },
  {
    path: '/financas/categorias/:id/editar',
    name: 'categoria-update',
    component: () => import('@/views/financas/CategoriaFormView.vue'),
  },
  {
    path: '/financas/despesas',
    name: 'despesa-list',
    component: () => import('@/views/financas/DespesaListView.vue'),
  },
  {
    path: '/financas/importar',
    name: 'importar-extrato',
    component: () => import('@/views/financas/ImportarExtratoView.vue'),
  },
  {
    path: '/financas/despesas/nova',
    name: 'despesa-create',
    component: () => import('@/views/financas/DespesaFormView.vue'),
  },
  {
    path: '/financas/despesas/:id/editar',
    name: 'despesa-update',
    component: () => import('@/views/financas/DespesaFormView.vue'),
  },
  {
    path: '/financas/receitas',
    name: 'receita-list',
    component: () => import('@/views/financas/ReceitaListView.vue'),
  },
  {
    path: '/financas/receitas/nova',
    name: 'receita-create',
    component: () => import('@/views/financas/ReceitaFormView.vue'),
  },
  {
    path: '/financas/receitas/:id/editar',
    name: 'receita-update',
    component: () => import('@/views/financas/ReceitaFormView.vue'),
  },
  {
    path: '/financas/recorrentes',
    name: 'recorrente-list',
    component: () => import('@/views/financas/RecorrenteListView.vue'),
  },
  {
    path: '/financas/recorrentes/nova',
    name: 'recorrente-create',
    component: () => import('@/views/financas/RecorrenteFormView.vue'),
  },
  {
    path: '/financas/recorrentes/:id/editar',
    name: 'recorrente-update',
    component: () => import('@/views/financas/RecorrenteFormView.vue'),
  },
  {
    path: '/emprestimos',
    name: 'emprestimo-list',
    component: () => import('@/views/emprestimos/EmprestimoListView.vue'),
  },
  {
    path: '/emprestimos/novo',
    name: 'emprestimo-create',
    component: () => import('@/views/emprestimos/EmprestimoFormView.vue'),
  },
  {
    path: '/emprestimos/:id/editar',
    name: 'emprestimo-update',
    component: () => import('@/views/emprestimos/EmprestimoFormView.vue'),
  },
  {
    path: '/emprestimos/:id',
    name: 'emprestimo-detail',
    component: () => import('@/views/emprestimos/EmprestimoDetailView.vue'),
  },
  {
    path: '/cartoes',
    name: 'cartao-list',
    component: () => import('@/views/cartoes/CartaoListView.vue'),
  },
  {
    path: '/cartoes/novo',
    name: 'cartao-create',
    component: () => import('@/views/cartoes/CartaoFormView.vue'),
  },
  {
    path: '/cartoes/:id/editar',
    name: 'cartao-update',
    component: () => import('@/views/cartoes/CartaoFormView.vue'),
  },
  {
    path: '/cartoes/:id',
    name: 'cartao-detail',
    component: () => import('@/views/cartoes/CartaoDetailView.vue'),
  },
  {
    path: '/metas',
    name: 'meta-list',
    component: () => import('@/views/metas/MetaListView.vue'),
  },
  {
    path: '/metas/nova',
    name: 'meta-create',
    component: () => import('@/views/metas/MetaFormView.vue'),
  },
  {
    path: '/metas/:id/editar',
    name: 'meta-update',
    component: () => import('@/views/metas/MetaFormView.vue'),
  },
  {
    path: '/metas/:id',
    name: 'meta-detail',
    component: () => import('@/views/metas/MetaDetailView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (auth.status === 'idle') {
    await auth.fetchMe()
  }

  if (!to.meta.publica && !auth.isAuthenticated()) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if ((to.name === 'home' || to.name === 'login' || to.name === 'signup') && auth.isAuthenticated()) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
