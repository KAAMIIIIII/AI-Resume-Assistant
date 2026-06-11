import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import type { User } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  // 初始化时从 localStorage 恢复 token，避免刷新后丢失登录态
  const token = ref<string | null>(localStorage.getItem('token'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const res = await api.post('/auth/login', { email, password })
    token.value = res.data.access_token
    localStorage.setItem('token', res.data.access_token)
    // 登录后立即拉取用户信息，确保 user 和 token 同步
    await fetchUser()
  }

  async function register(email: string, username: string, password: string) {
    await api.post('/auth/register', { email, username, password })
  }

  async function fetchUser() {
    const res = await api.get('/auth/me')
    user.value = res.data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { user, token, isLoggedIn, login, register, fetchUser, logout }
})
