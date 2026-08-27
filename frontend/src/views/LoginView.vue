<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { LoaderCircle } from '@lucide/vue'
import AuthLayout from '@/components/AuthLayout.vue'
import fluxoMark from '@/assets/brand/fluxo-mark-alpha.png'

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
  <AuthLayout>
    <div class="mb-8 text-center">
      <img :src="fluxoMark" alt="Fluxo" class="mx-auto h-10 w-auto md:hidden" />
      <h1 class="mt-3 text-xl font-bold text-stone-800 md:mt-0">Bem-vindo de volta</h1>
      <p class="mt-1 text-sm text-stone-500">Entre pra ver seu dashboard</p>
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
  </AuthLayout>
</template>
