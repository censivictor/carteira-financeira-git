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
