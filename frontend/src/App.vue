<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard,
  Wallet,
  ArrowDownCircle,
  ArrowUpCircle,
  Tags,
  Repeat,
  LogOut,
  PiggyBank,
} from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const mostrarLayout = computed(() => !route.meta.publica)

function itemAtivo(item) {
  if (!item.disponivel) return false
  if (item.to === '/') return route.path === '/'
  return route.path.startsWith(item.to)
}

const navItems = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard, disponivel: true },
  { label: 'Investimentos', to: '/investimentos', icon: Wallet, disponivel: true },
  { label: 'Despesas', to: '#', icon: ArrowDownCircle, disponivel: false },
  { label: 'Receitas', to: '#', icon: ArrowUpCircle, disponivel: false },
  { label: 'Categorias', to: '#', icon: Tags, disponivel: false },
  { label: 'Recorrentes', to: '#', icon: Repeat, disponivel: false },
]

async function sair() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div v-if="mostrarLayout" class="flex min-h-screen bg-stone-50">
    <aside class="flex w-64 shrink-0 flex-col border-r border-stone-200 bg-white">
      <div class="flex items-center gap-2.5 px-6 py-6">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-wine text-white">
          <PiggyBank :size="20" />
        </div>
        <span class="text-lg font-bold tracking-tight text-stone-800">Carteira</span>
      </div>

      <nav class="flex-1 space-y-1 px-3">
        <RouterLink
          v-for="item in navItems"
          :key="item.label"
          :to="item.disponivel ? item.to : '#'"
          class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
          :class="[
            item.disponivel
              ? 'text-stone-600 hover:bg-peach/20 hover:text-wine'
              : 'cursor-not-allowed text-stone-300',
            itemAtivo(item) ? 'bg-wine/10 text-wine' : '',
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

    <main class="flex-1 overflow-y-auto p-8">
      <RouterView />
    </main>
  </div>

  <RouterView v-else />
</template>
