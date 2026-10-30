import type { TokenPair } from '../types/auth.types'

const KEY = 'student-connect.refresh-token'
let access: string | null = null
let version = 0
let identity = 0
const listeners = new Set<() => void>()
function save(tokens: TokenPair) {
  access = tokens.access_token
  sessionStorage.setItem(KEY, tokens.refresh_token)
  version += 1
}
export const session = {
  get accessToken() { return access },
  get refreshToken() { return sessionStorage.getItem(KEY) },
  get version() { return version },
  get identity() { return identity },
  start(tokens: TokenPair) { identity += 1; save(tokens) },
  save,
  clear() { access = null; sessionStorage.removeItem(KEY); version += 1; identity += 1 },
}
export function onSessionExpired(listener: () => void) {
  listeners.add(listener); return () => { listeners.delete(listener) }
}
export function expireSession() { session.clear(); listeners.forEach(listener => listener()) }
