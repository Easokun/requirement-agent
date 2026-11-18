export const SESSION_KEY = 'jg_current_user'


export function getToken() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw).token || '' : ''
  } catch {
    return ''
  }
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}

export function newSessionId() {
  return 'web-' + Math.random().toString(36).slice(2, 10)
}
