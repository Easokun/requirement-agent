import { defineStore } from 'pinia'
import { useUserStore } from './user'
import { useChatStore } from './chat'
import { useQuestionnaireStore } from './questionnaire'

const DRAFT_KEY = 'jg_analysis_draft'

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return null
    const d = JSON.parse(raw)
    return d && d.mode ? d : null
  } catch {
    return null
  }
}


export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    mode: '' 
  }),

  getters: {
    active: (s) => s.mode !== ''
  },

  actions: {
    start(mode) {
      this.mode = mode
    },

    
    saveDraft() {
      if (!this.mode) {
        localStorage.removeItem(DRAFT_KEY)
        return
      }
      const chat = useChatStore()
      const quiz = useQuestionnaireStore()
      const user = useUserStore()
      const draft = {
        username: user.username,
        mode: this.mode,
        sessionId: chat.sessionId,
        quiz: {
          answered: quiz.answered,
          current: quiz.current,
          finished: quiz.finished,
          summary: quiz.summary
        },
        chat: { messages: chat.messages.filter((m) => m.done) },
        savedAt: Date.now()
      }
      try {
        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
      } catch {
        
      }
    },

    
    restoreDraft() {
      const draft = loadDraft()
      if (!draft) return false
      const user = useUserStore()
      if (draft.username && user.username && draft.username !== user.username) {
        localStorage.removeItem(DRAFT_KEY)
        return false
      }
      const chat = useChatStore()
      const quiz = useQuestionnaireStore()
      this.mode = draft.mode
      if (draft.sessionId) chat.sessionId = draft.sessionId
      if (draft.quiz) {
        quiz.started = true
        quiz.sessionId = draft.sessionId || quiz.sessionId
        quiz.answered = draft.quiz.answered || []
        quiz.current = draft.quiz.current || null
        quiz.finished = !!draft.quiz.finished
        quiz.summary = draft.quiz.summary || ''
      }
      if (draft.chat && Array.isArray(draft.chat.messages) && draft.chat.messages.length) {
        chat.messages = draft.chat.messages
      }
      return true
    },

    
    abandon() {
      this.mode = ''
      try {
        localStorage.removeItem(DRAFT_KEY)
      } catch {
        
      }
    }
  }
})
