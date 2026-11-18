import { clearSession, getToken } from './client'



function authHeaders(json = true) {
  const headers = {}
  if (json) headers['Content-Type'] = 'application/json'
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token
  return headers
}

function handleUnauthorized() {
  
  clearSession()
  location.replace('#/login')
  location.reload()
}

async function requestJson(path, options = {}) {
  const res = await fetch(path, options)
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  if (!res.ok) {
    const message =
      (data && (data.detail || data.message || data.error)) || `请求失败（${res.status}）`
    const error = new Error(message)
    error.status = res.status
    if (res.status === 401 && getToken()) handleUnauthorized()
    throw error
  }
  return data
}

export const api = {
  getOpening() {
    return requestJson('/api/opening')
  },

  getKb() {
    return requestJson('/api/kb')
  },

  getUsage() {
    return requestJson('/api/usage', { headers: authHeaders(false) })
  },

  consume() {
    return requestJson('/api/consume', {
      method: 'POST',
      headers: authHeaders(false)
    })
  },

  getMe() {
    return requestJson('/api/me', { headers: authHeaders(false) })
  },

  checkAccount(username) {
    return requestJson('/api/check_account', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ username })
    })
  },

  register(username, password) {
    return requestJson('/api/register', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ username, password })
    })
  },

  login(username, password) {
    return requestJson('/api/login', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ username, password })
    })
  },

  logout() {
    return requestJson('/api/logout', {
      method: 'POST',
      headers: authHeaders(false)
    })
  },

  updateProfile(industry) {
    return requestJson('/api/profile', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ industry })
    })
  },

  changePassword(oldPassword, newPassword) {
    return requestJson('/api/change_password', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
    })
  },

  deleteAccount(password) {
    return requestJson('/api/delete_account', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ password })
    })
  },

  generateDoc(sessionId, answers) {
    return requestJson('/api/generate_doc', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ session_id: sessionId, answers: answers || [] })
    })
  },

  
  accept(document, confirmItems, resolutions, projectKey) {
    return requestJson('/api/accept', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        document: document || '',
        confirm_items: confirmItems || [],
        resolutions: resolutions || [],
        project_key: projectKey || ''
      })
    })
  },

  
  assessment(document) {
    return requestJson('/api/assessment', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ document: document || '' })
    })
  },

  
  deliverables(document) {
    return requestJson('/api/deliverables', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ document: document || '' })
    })
  },

  
  abPlan(document) {
    return requestJson('/api/ab_plan', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ document: document || '' })
    })
  },

  
  revision(document, instructions) {
    return requestJson('/api/revision', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ document: document || '', instructions: instructions || '' })
    })
  },

  // 生成 PDF 由 deepseek v4 pro 生成。
  async exportPdf(document) {
    const res = await fetch('/api/export_pdf', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ document: document || '' })
    })
    if (res.status === 401 && getToken()) {
      handleUnauthorized()
      throw new Error('登录已过期，请重新登录')
    }
    if (!res.ok) {
      let message = 'PDF 生成失败'
      try {
        const data = await res.json()
        message = data.detail || message
      } catch {
        
      }
      throw new Error(message)
    }
    return res.blob()
  },

  
  nextQuestion(sessionId, answers, forceContinue = false) {
    return requestJson('/api/questionnaire', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ session_id: sessionId, answers, force_continue: forceContinue })
    })
  },

  
  async chatStream(message, sessionId, onEvent) {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        message,
        session_id: sessionId
      })
    })

    if (res.status === 401 && getToken()) {
      handleUnauthorized()
      throw new Error('登录已过期，请重新登录')
    }
    if (res.status === 403) {
      const error = new Error('文档生成次数已用满，对话服务已锁定')
      error.status = 403
      error.locked = true
      throw error
    }
    if (!res.ok || !res.body) {
      throw new Error('HTTP ' + res.status)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let nl
      while ((nl = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, nl).trim()
        buffer = buffer.slice(nl + 1)
        if (!line) continue
        let event
        try {
          event = JSON.parse(line)
        } catch {
          continue
        }
        onEvent(event)
      }
    }
  }
}
