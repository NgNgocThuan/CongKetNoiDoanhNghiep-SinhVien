import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { AuthContext } from './auth-context'
import { authApi } from './api/auth.api'
import { onSessionExpired, session } from './lib/session'
import { refreshSession } from '@/lib/http'
import { ApiError, toApiError } from '@/lib/api-error'
import type { AuthContextValue } from './auth-context'

type State = Pick<AuthContextValue, 'user' | 'status' | 'error'>
const anonymous: State = { user: null, status: 'anonymous', error: null }

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const operation = useRef(0)
  const [state, setState] = useState<State>({ user: null, status: 'loading', error: null })

  const retry = useCallback(async () => {
    const current = ++operation.current
    if (!session.refreshToken) {
      setState(anonymous)
      return
    }
    setState({ user: null, status: 'loading', error: null })
    try {
      if (!session.accessToken) await refreshSession()
      if (current !== operation.current) return
      const user = await authApi.me()
      if (current === operation.current) setState({ user, status: 'authenticated', error: null })
    } catch (error) {
      if (current !== operation.current) return
      const normalized = toApiError(error)
      if (normalized.status === 401 || normalized.status === 403) {
        session.clear()
        queryClient.clear()
        setState(anonymous)
      } else {
        setState({ user: null, status: 'error', error: normalized })
      }
    }
  }, [queryClient])

  useEffect(() => {
    void retry()
  }, [retry])

  useEffect(
    () =>
      onSessionExpired(() => {
        operation.current += 1
        queryClient.clear()
        setState(anonymous)
      }),
    [queryClient]
  )

  const login: AuthContextValue['login'] = async input => {
    const current = ++operation.current
    const tokens = await authApi.login({ email: input.email, password: input.password })
    if (current !== operation.current) throw new ApiError('Phiên đăng nhập đã thay đổi.', 401, 'SESSION_CHANGED')
    queryClient.clear()
    session.start(tokens, input.remember ?? false)
    try {
      const user = await authApi.me()
      if (current !== operation.current) throw new ApiError('Phiên đăng nhập đã thay đổi.', 401, 'SESSION_CHANGED')
      setState({ user, status: 'authenticated', error: null })
      return user
    } catch (error) {
      if (current === operation.current) {
        session.clear()
        setState(anonymous)
      }
      throw error
    }
  }

  const logout = async () => {
    const access = session.accessToken
    const refresh = session.refreshToken
    operation.current += 1
    session.clear()
    queryClient.clear()
    setState(anonymous)
    if (access) await authApi.logout(access, refresh)
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, retry }}>
      {children}
    </AuthContext.Provider>
  )
}
