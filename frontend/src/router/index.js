import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { publica: true },
  },
  {
    path: '/',
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
  if (to.name === 'login' && auth.isAuthenticated()) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
