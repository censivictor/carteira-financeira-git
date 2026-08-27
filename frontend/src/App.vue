<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import fluxoLogo from '@/assets/brand/fluxo-logo-horizontal-alpha.png'
import {
  LayoutDashboard,
  Wallet,
  ArrowDownCircle,
  ArrowUpCircle,
  Tags,
  Repeat,
  Landmark,
  CreditCard,
  Target,
  LogOut,
  Menu,
  X,
} from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const mostrarLayout = computed(() => !route.meta.publica)

// Drawer do menu no mobile — fecha sozinho ao navegar e trava o scroll do
// body enquanto tá aberto (senão o conteúdo por trás rola junto).
const menuAberto = ref(false)
watch(() => route.fullPath, () => { menuAberto.value = false })
watch(menuAberto, (aberto) => {
  document.body.style.overflow = aberto ? 'hidden' : ''
})

function itemAtivo(item) {
  if (!item.disponivel) return false
  if (item.to === '/app') return route.path === '/app'
  return route.path.startsWith(item.to)
}

const navItems = [
  { label: 'Dashboard', to: '/app', icon: LayoutDashboard, disponivel: true },
  { label: 'Investimentos', to: '/investimentos', icon: Wallet, disponivel: true },
  { label: 'Despesas', to: '/financas/despesas', icon: ArrowDownCircle, disponivel: true },
  { label: 'Receitas', to: '/financas/receitas', icon: ArrowUpCircle, disponivel: true },
  { label: 'Categorias', to: '/financas/categorias', icon: Tags, disponivel: true },
  { label: 'Recorrentes', to: '/financas/recorrentes', icon: Repeat, disponivel: true },
  { label: 'Empréstimos', to: '/emprestimos', icon: Landmark, disponivel: true },
  { label: 'Cartões', to: '/cartoes', icon: CreditCard, disponivel: true },
  { label: 'Metas', to: '/metas', icon: Target, disponivel: true },
]

async function sair() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div v-if="mostrarLayout" class="min-h-screen bg-stone-50 md:flex">
    <!-- Backdrop do drawer (só mobile) -->
    <Transition
      enter-active-class="transition-opacity duration-200"
      leave-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="menuAberto"
        class="fixed inset-0 z-30 bg-stone-900/40 md:hidden"
        @click="menuAberto = false"
      />
    </Transition>

    <aside
      class="fixed inset-y-0 left-0 z-40 flex h-screen w-64 shrink-0 -translate-x-full flex-col border-r border-stone-200 bg-white transition-transform duration-200 ease-out md:translate-x-0"
      :class="menuAberto ? 'translate-x-0' : ''"
    >
      <div class="flex items-center px-6 py-6">
        <img :src="fluxoLogo" alt="Fluxo" class="h-8 w-auto" />
        <button
          type="button"
          class="ml-auto text-stone-400 transition hover:text-stone-600 md:hidden"
          @click="menuAberto = false"
        >
          <X :size="20" />
        </button>
      </div>

      <nav class="flex-1 space-y-0.5 overflow-y-auto px-3">
        <RouterLink
          v-for="item in navItems"
          :key="item.label"
          :to="item.disponivel ? item.to : '#'"
          class="flex items-center gap-3 border-l-2 py-2 pl-3 pr-3 text-sm font-medium transition-colors"
          :class="[
            item.disponivel
              ? 'text-stone-600 hover:border-peach hover:text-wine'
              : 'cursor-not-allowed border-transparent text-stone-300',
            itemAtivo(item) ? 'border-wine text-wine' : item.disponivel ? 'border-transparent' : '',
          ]"
        >
          <component :is="item.icon" :size="18" />
          {{ item.label }}
          <span v-if="!item.disponivel" class="ml-auto rounded-full bg-stone-100 px-2 py-0.5 text-[10px] text-stone-400">
            em breve
          </span>
        </RouterLink>
      </nav>

      <div class="border-t border-stone-200 p-4">
        <div class="mb-3 flex items-center gap-2.5 px-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-coral/30 text-sm font-semibold text-wine">
            {{ auth.username?.[0]?.toUpperCase() }}
          </div>
          <span class="text-sm font-medium text-stone-700">{{ auth.username }}</span>
        </div>
        <button type="button" class="btn-secondary w-full" @click="sair">
          <LogOut :size="16" />
          Sair
        </button>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col md:ml-64">
      <!-- Topbar (só mobile) -->
      <header class="flex items-center gap-3 border-b border-stone-200 bg-white px-4 py-3 md:hidden">
        <button
          type="button"
          class="-ml-1 rounded-lg p-1.5 text-stone-500 transition hover:bg-stone-100 hover:text-wine"
          @click="menuAberto = true"
        >
          <Menu :size="22" />
        </button>
        <img :src="fluxoLogo" alt="Fluxo" class="h-6 w-auto" />
      </header>

      <main class="flex-1 overflow-y-auto p-4 md:p-8">
        <RouterView />
      </main>
    </div>
  </div>

  <RouterView v-else />
</template>
