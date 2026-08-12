<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { LoaderCircle } from '@lucide/vue'
import fluxoLogo from '@/assets/brand/fluxo-logo-stacked.png'

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
        <img :src="fluxoLogo" alt="Fluxo" class="h-24 w-auto" />
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

      <p class="mt-5 text-center text-sm text-stone-500">
        Ainda não tem conta?
        <RouterLink :to="{ name: 'signup' }" class="font-medium text-wine hover:underline">Criar conta</RouterLink>
      </p>
    </div>
  </div>
</template>
