<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { PiggyBank, LoaderCircle } from '@lucide/vue'

const username = ref('')
const password = ref('')
const erro = ref('')
const carregando = ref(false)

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

async function aoEnviar() {
  erro.value = ''
  carregando.value = true
  try {
    await auth.login(username.value, password.value)
    router.push(route.query.next || { name: 'dashboard' })
  } catch (e) {
    erro.value = e.data?.detail || 'Usuário ou senha inválidos.'
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-sand/40 via-stone-50 to-peach/20 px-4">
    <div class="w-full max-w-sm">
      <div class="mb-8 flex flex-col items-center gap-3">
        <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-wine text-white shadow-lg shadow-wine/20">
          <PiggyBank :size="28" />
        </div>
        <h1 class="text-xl font-bold text-stone-800">Carteira Financeira</h1>
        <p class="text-sm text-stone-500">Entre pra ver seu dashboard</p>
      </div>

      <form class="card space-y-4" @submit.prevent="aoEnviar">
        <div v-if="erro" class="rounded-xl bg-red/10 px-4 py-3 text-sm text-red">
          {{ erro }}
        </div>

        <div>
          <label for="username" class="mb-1.5 block text-sm font-medium text-stone-700">Usuário</label>
          <input id="username" v-model="username" type="text" class="input" autofocus required />
        </div>

        <div>
          <label for="password" class="mb-1.5 block text-sm font-medium text-stone-700">Senha</label>
          <input id="password" v-model="password" type="password" class="input" required />
        </div>

        <button type="submit" class="btn-primary w-full" :disabled="carregando">
          <LoaderCircle v-if="carregando" :size="16" class="animate-spin" />
          Entrar
        </button>
      </form>
    </div>
  </div>
</template>
