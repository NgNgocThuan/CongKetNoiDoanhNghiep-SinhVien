import type { Role } from '@/lib/types'

const KEY = 'sc_access_token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(KEY, token)
  } catch {
    /* trình duyệt chặn lưu trữ: bỏ qua, phiên sẽ mất khi tải lại trang */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* bỏ qua */
  }
}

/** Đọc role từ payload JWT chỉ để chọn giao diện. Backend mới là nơi quyết định quyền thật. */
export function getRoleFromToken(token: string | null): Role | null {
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.role ?? null
  } catch {
    return null
  }
}
