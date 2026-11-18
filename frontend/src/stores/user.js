import { defineStore } from 'pinia'
import { api } from '../api'
import { SESSION_KEY } from '../api/client'

// 登录 / 注册由 deepseek v4 pro 生成。
export const useUserStore = defineStore('user', {
  state: () => {
    let username = ''
    let token = ''
    try {
      const raw = localStorage.getItem(SESSION_KEY)
      if (raw) {
        const s = JSON.parse(raw)
        username = s.username || ''
        token = s.token || ''
      }
    } catch {
      
    }
    return {
      username,
      token,
      industry: '',
      usage: { used: 0, remaining: 5, max: 5, locked: false }
    }
  },

  getters: {
    isLoggedIn: (state) => Boolean(state.token)
  },

  actions: {
    async checkAccount(username) {
      const { exists } = await api.checkAccount(username)
      return exists
    },

    async register(username, password) {
      await api.register(username, password)
    },

    async login(username, password) {
      const data = await api.login(username, password)
      this.username = data.username || username
      this.token = data.token || ''
      localStorage.setItem(
        SESSION_KEY,
        JSON.stringify({ username: this.username, token: this.token })
      )
    },

    async fetchMe() {
      const data = await api.getMe()
      this.username = data.username || this.username
      this.industry = data.industry || ''
      this.usage = data.usage || this.usage
      return data
    },

    async updateIndustry(industry) {
      await api.updateProfile(industry)
      this.industry = industry
    },

    async changePassword(oldPassword, newPassword) {
      await api.changePassword(oldPassword, newPassword)
    },

    async deleteAccount(password) {
      await api.deleteAccount(password)
      this.username = ''
      this.token = ''
      this.industry = ''
      this.usage = { used: 0, remaining: 5, max: 5, locked: false }
      localStorage.removeItem(SESSION_KEY)
    },

    async logout() {
      try {
        await api.logout()
      } catch {
        
      }
      this.username = ''
      this.token = ''
      this.industry = ''
      this.usage = { used: 0, remaining: 5, max: 5, locked: false }
      localStorage.removeItem(SESSION_KEY)
    }
  }
})
