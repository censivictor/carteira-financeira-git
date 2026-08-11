import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/lib/api'

export const useAuthStore = defineStore('auth', () => {
  const username = ref(null)
  const status = ref('idle') // 'idle' | 'loading' | 'ready'

  const isAuthenticated = () => username.value !== null

  async function fetchMe() {
    status.value = 'loading'
    try {
      const data = await api.get('/auth/me/')
      username.value = data.username
    } catch {
      username.value = null
    } finally {
      status.value = 'ready'
    }
  }

  async function login(usernameInput, password) {
    const data = await api.post('/auth/login/', { username: usernameInput, password })
    username.value = data.username
  }

  async function logout() {
    await api.post('/auth/logout/')
    username.value = null
  }

  return { username, status, isAuthenticated, fetchMe, login, logout }
})
