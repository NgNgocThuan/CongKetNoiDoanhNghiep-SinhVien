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
    if (localVal) return localVal
  } catch {
    /* ignore storage errors */
  }
  return null
}

function save(tokens: TokenPair, remember?: boolean) {
  access = tokens.access_token

  // Xác định chế độ lưu:
  // - Nếu remember được chỉ định (true/false): tuân thủ tuyệt đối lựa chọn của người dùng.
  // - Nếu remember === undefined (ví dụ khi refreshSession xoay vòng token):
  //   giữ nguyên phân vùng lưu trữ hiện tại (nếu đang ở localStorage thì tiếp tục lưu localStorage).
  const isRemember =
    remember !== undefined
      ? remember
      : typeof localStorage !== 'undefined' && localStorage.getItem(KEY) !== null

  try {
    if (isRemember) {
      if (typeof localStorage !== 'undefined') localStorage.setItem(KEY, tokens.refresh_token)
      sessionStorage.removeItem(KEY)
    } else {
      sessionStorage.setItem(KEY, tokens.refresh_token)
      if (typeof localStorage !== 'undefined') localStorage.removeItem(KEY)
    }
  } catch {
    /* ignore storage errors */
  }

  version += 1
}

export const session = {
  get accessToken() {
    return access
  },
  get refreshToken() {
    return getStorageItem(KEY)
  },
  get version() {
    return version
  },
  get identity() {
    return identity
  },
  start(tokens: TokenPair, remember?: boolean) {
    identity += 1
    save(tokens, remember)
  },
  save,
  clear() {
    access = null
    try {
      sessionStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
    try {
      if (typeof localStorage !== 'undefined') localStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
    version += 1
    identity += 1
  },
}

export function onSessionExpired(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function expireSession() {
  session.clear()
  listeners.forEach(listener => listener())
}
