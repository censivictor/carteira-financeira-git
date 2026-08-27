<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { LoaderCircle } from '@lucide/vue'
import AuthLayout from '@/components/AuthLayout.vue'
import fluxoMark from '@/assets/brand/fluxo-mark-alpha.png'

const username = ref('')
const password = ref('')
const password2 = ref('')
const erros = ref({})
const carregando = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function aoEnviar() {
  erros.value = {}
  carregando.value = true
  try {
    await auth.signup(username.value, password.value, password2.value)
    router.push({ name: 'dashboard' })
  } catch (e) {
    erros.value = e.data || { username: ['Não deu pra criar a conta agora.'] }
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <div class="mb-8 text-center">
      <img :src="fluxoMark" alt="Fluxo" class="mx-auto h-10 w-auto md:hidden" />
      <h1 class="mt-3 text-xl font-bold text-stone-800 md:mt-0">Crie sua conta</h1>
      <p class="mt-1 text-sm text-stone-500">Leva menos de um minuto</p>
    </div>

    <form class="card space-y-4" @submit.prevent="aoEnviar">
      <div v-if="erros.detail" class="rounded-xl bg-red/10 px-4 py-3 text-sm text-red">
        {{ erros.detail }}
      </div>

      <div>
        <label for="username" class="mb-1.5 block text-sm font-medium text-stone-700">Usuário</label>
        <input id="username" v-model="username" type="text" class="input" autofocus required />
        <p v-if="erros.username" class="mt-1 text-xs text-red">{{ erros.username[0] }}</p>
      </div>

      <div>
        <label for="password" class="mb-1.5 block text-sm font-medium text-stone-700">Senha</label>
        <input id="password" v-model="password" type="password" class="input" required />
        <p v-if="erros.password" class="mt-1 text-xs text-red">{{ erros.password[0] }}</p>
      </div>

      <div>
        <label for="password2" class="mb-1.5 block text-sm font-medium text-stone-700">Confirmar senha</label>
        <input id="password2" v-model="password2" type="password" class="input" required />
        <p v-if="erros.password2" class="mt-1 text-xs text-red">{{ erros.password2[0] }}</p>
      </div>

      <button type="submit" class="btn-primary w-full" :disabled="carregando">
        <LoaderCircle v-if="carregando" :size="16" class="animate-spin" />
        Criar conta
      </button>
    </form>

    <p class="mt-5 text-center text-sm text-stone-500">
      Já tem conta?
      <RouterLink :to="{ name: 'login' }" class="font-medium text-wine hover:underline">Entrar</RouterLink>
    </p>
  </AuthLayout>
</template>
