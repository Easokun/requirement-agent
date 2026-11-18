import { defineStore } from 'pinia'
import { api } from '../api'
import { newSessionId } from '../api/client'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessionId: newSessionId(),
    messages: [],
    usage: { used: 0, remaining: 5, max: 5, locked: false },
    kb: { files: [], chars: 0 },
    busy: false,
    started: false, 
    initialized: false
  }),

  getters: {
    locked: (state) => Boolean(state.usage.locked)
  },

  actions: {
    async init() {
      if (this.initialized) return
      this.initialized = true

      try {
        this.usage = await api.getUsage()
      } catch {
        
      }
      try {
        this.kb = await api.getKb()
      } catch {
        
      }

      if (!this.messages.length) {
        let content = '你好，我是你的需求诊断顾问。先说说你想做的需求大概是什么？'
        try {
          const data = await api.getOpening()
          if (data && data.content) content = data.content
        } catch {
          
        }
        this.messages.push({ role: 'assistant', content, done: true, fresh: true })
      }
    },

    applyUsage(usage) {
      if (usage) this.usage = usage
    },

    async refreshUsage() {
      try {
        this.usage = await api.getUsage()
      } catch {
        
      }
    },

    resetSession() {
      this.sessionId = newSessionId()
      this.messages = []
      this.started = false
      this.initialized = false
      this.init()
    }
  }
})
