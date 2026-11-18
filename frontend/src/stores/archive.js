import { defineStore } from 'pinia'

const STORAGE_KEY = 'jg_archive'

function nowText() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function loadItems() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []
  } catch {
    return []
  }
}

function saveItems(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}


export const useArchiveStore = defineStore('archive', {
  state: () => ({
    items: loadItems()
  }),

  actions: {
    add(document, confirmItems, assessment) {
      const title =
        (String(document || '').match(/^#\s+(.+)$/m) || [])[1] || '需求诊断报告'
      const item = {
        id: 'doc-' + Date.now(),
        title,
        document,
        confirmItems: Array.isArray(confirmItems) ? confirmItems : [],
        assessment: assessment || null,
        deliverables: null, 
        abPlan: null, 
        acceptance: null, 
        versions: [], 
        created_at: nowText()
      }
      this.items.unshift(item)
      saveItems(this.items)
      return item
    },

    
    setAcceptance(id, info) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.acceptance = info || null
      if (info && info.version) {
        const snap = {
          version: info.version,
          doc_hash: info.doc_hash,
          accepted_at: info.accepted_at,
          diff: info.diff || ''
        }
        const i = item.versions.findIndex((v) => v.version === snap.version)
        if (i >= 0) item.versions[i] = snap
        else item.versions.push(snap)
        item.versions.sort((a, b) => a.version - b.version)
      }
      saveItems(this.items)
    },

    setAssessment(id, assessment) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.assessment = assessment || null
      saveItems(this.items)
    },

    setDeliverables(id, d) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.deliverables = d || null
      saveItems(this.items)
    },

    setAbPlan(id, p) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.abPlan = p || null
      saveItems(this.items)
    },

    
    updateDocument(id, document, confirmItems, assessment) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.document = document
      if (confirmItems !== undefined) item.confirmItems = Array.isArray(confirmItems) ? confirmItems : []
      if (assessment !== undefined) item.assessment = assessment || null
      saveItems(this.items)
    },

    getById(id) {
      return this.items.find((item) => item.id === id)
    },

    clear() {
      this.items = []
      localStorage.removeItem(STORAGE_KEY)
    }
  }
})
