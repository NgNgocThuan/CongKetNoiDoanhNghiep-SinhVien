import type { TokenPair } from '../types/auth.types'

const KEY = 'student-connect.refresh-token'
let access: string | null = null
let version = 0
let identity = 0
const listeners = new Set<() => void>()

function getStorageItem(key: string): string | null {
  try {
    const sessionVal = sessionStorage.getItem(key)
    if (sessionVal) return sessionVal
    const localVal = typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null
    if (localVal) {
      sessionStorage.setItem(key, localVal)
      return localVal
    }
  } catch {
    /* ignore storage errors */
  }
  return null
}

function setStorageItem(key: string, value: string) {
  try { sessionStorage.setItem(key, value) } catch { /* ignore */ }
  try { if (typeof localStorage !== 'undefined') localStorage.setItem(key, value) } catch { /* ignore */ }
}

function removeStorageItem(key: string) {
  try { sessionStorage.removeItem(key) } catch { /* ignore */ }
  try { if (typeof localStorage !== 'undefined') localStorage.removeItem(key) } catch { /* ignore */ }
}

function save(tokens: TokenPair) {
  access = tokens.access_token
  setStorageItem(KEY, tokens.refresh_token)
  version += 1
}

export const session = {
  get accessToken() { return access },
  get refreshToken() { return getStorageItem(KEY) },
  get version() { return version },
  get identity() { return identity },
  start(tokens: TokenPair) { identity += 1; save(tokens) },
  save,
  clear() {
    access = null
    removeStorageItem(KEY)
    version += 1
    identity += 1
  },
}

export function onSessionExpired(listener: () => void) {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

export function expireSession() {
  session.clear()
  listeners.forEach(listener => listener())
}
