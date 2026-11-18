


export function isPhone(u) {
  return /^1[3-9]\d{9}$/.test((u || '').trim())
}


export function isStrongPassword(p) {
  const s = p || ''
  if (s.length < 8) return false
  let kinds = 0
  if (/[a-z]/.test(s)) kinds++
  if (/[A-Z]/.test(s)) kinds++
  if (/\d/.test(s)) kinds++
  if (/[^A-Za-z0-9]/.test(s)) kinds++
  return kinds >= 3
}
