/**
 * TẠM THỜI: bản đăng nhập tối thiểu để chạy các trang của Phong (admin).
 * Quang (xác thực) sẽ thay bằng AuthProvider/RequireRole thật (refresh token, /auth/me...).
 * Giữ nguyên tên `useAuth` và `RequireRole` để các trang không phải sửa.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Button, Result } from 'antd'
import { http, SESSION_EXPIRED_EVENT } from '@/lib/http'
import { clearToken, getRoleFromToken, getToken, setToken } from '@/lib/token'
import type { Role } from '@/lib/types'

interface AuthState {
  token: string | null
  role: Role | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => getToken())

  useEffect(() => {
    const onExpired = () => setTokenState(null)
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    // Endpoint OAuth2 dạng form (cũng là endpoint nút Authorize của Swagger dùng)
    const body = new URLSearchParams({ username: email, password })
    const { data } = await http.post<{ access_token: string }>('/auth/token', body)
    setToken(data.access_token)
    setTokenState(data.access_token)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setTokenState(null)
  }, [])

  const value = useMemo<AuthState>(
    () => ({ token, role: getRoleFromToken(token), login, logout }),
    [token, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth phải nằm trong AuthProvider')
  return ctx
}

/** Chỉ cho phép role chỉ định; chưa đăng nhập thì chuyển về /login. */
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { token, role: current, logout } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (current !== role) {
    return (
      <Result
        status="403"
        title="Không đủ quyền truy cập"
        subTitle="Tài khoản của bạn không có quyền vào khu vực này."
        extra={
          <Button type="primary" onClick={logout}>
            Đăng xuất
          </Button>
        }
      />
    )
  }
  return <>{children}</>
}
