import axios, { AxiosHeaders } from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'
import { env } from '@/config/env'
import { expireSession, session } from '@/features/auth/lib/session'
import { tokenSchema } from '@/features/auth/types/auth.types'
import { ApiError, toApiError } from './api-error'

const options = { baseURL: env.apiBaseUrl, timeout: 15_000, paramsSerializer: { indexes: null } }
export const publicHttp = axios.create(options)
export const http = axios.create(options)
let refreshPromise: Promise<void> | null = null
type RetryConfig = InternalAxiosRequestConfig & { _retried?: boolean; _identity?: number }

export function refreshSession(): Promise<void> {
  if (refreshPromise) return refreshPromise
  const token = session.refreshToken
  const version = session.version
  if (!token) return Promise.reject(new ApiError('Phiên đăng nhập đã hết hạn.', 401, 'SESSION_EXPIRED'))
  refreshPromise = publicHttp.post('/auth/refresh', { refresh_token: token })
    .then(({ data }) => {
      if (session.version !== version) throw new ApiError('Phiên đăng nhập đã thay đổi.', 401, 'SESSION_CHANGED')
      session.save(tokenSchema.parse(data))
    })
    .catch((error: unknown) => {
      const normalized = toApiError(error)
      if (session.version === version && (normalized.status === 401 || normalized.status === 403)) expireSession()
      throw normalized
    })
    .finally(() => { refreshPromise = null })
  return refreshPromise
}
http.interceptors.request.use(config => {
  const request = config as RetryConfig
  request._identity ??= session.identity
  if (session.accessToken) config.headers.set('Authorization', 'Bearer ' + session.accessToken)
  return config
})
http.interceptors.response.use(response => response, async (error: unknown) => {
  if (!axios.isAxiosError(error)) throw toApiError(error)
  const config = error.config as RetryConfig | undefined
  if (error.response?.status !== 401 || !config) throw toApiError(error)
  if (config._identity !== session.identity) throw new ApiError('Phiên đăng nhập đã thay đổi.', 401, 'SESSION_CHANGED')
  if (config._retried) { expireSession(); throw toApiError(error) }
  if (!session.refreshToken) { expireSession(); throw toApiError(error) }
  config._retried = true
  const sentToken = AxiosHeaders.from(config.headers).get('Authorization')
  if (!session.accessToken || sentToken === 'Bearer ' + session.accessToken) await refreshSession()
  config.headers.set('Authorization', 'Bearer ' + session.accessToken)
  return http.request(config)
})
publicHttp.interceptors.response.use(response => response, (error: unknown) => Promise.reject(toApiError(error)))
