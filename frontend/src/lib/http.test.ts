import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { http, publicHttp, refreshSession } from './http'
import { session } from '@/features/auth/lib/session'

const originalHttp = http.defaults.adapter
const originalPublic = publicHttp.defaults.adapter
const oldTokens = { access_token: 'old-access', refresh_token: 'old-refresh', token_type: 'bearer' }
const newTokens = { access_token: 'new-access', refresh_token: 'new-refresh', token_type: 'bearer' }
function response(config: InternalAxiosRequestConfig, data: unknown, status = 200): AxiosResponse {
  return { config, data, status, statusText: String(status), headers: {} }
}
function denied(config: InternalAxiosRequestConfig): never {
  throw new AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', config, undefined,
    response(config, { error: { code: 'TOKEN_REVOKED', message: 'Phiên đăng nhập đã hết hạn.' } }, 401))
}
beforeEach(() => { session.clear(); session.start(oldTokens) })
afterEach(() => { http.defaults.adapter = originalHttp; publicHttp.defaults.adapter = originalPublic; session.clear() })

describe('authenticated HTTP transport', () => {
  it('shares one refresh for parallel 401 responses and retries with the rotated token', async () => {
    const refresh = vi.fn<AxiosAdapter>(async config => {
      await new Promise(resolve => setTimeout(resolve, 10))
      return response(config, newTokens)
    })
    publicHttp.defaults.adapter = refresh
    http.defaults.adapter = async config => {
      if (AxiosHeaders.from(config.headers).get('Authorization') === 'Bearer old-access') denied(config)
      return response(config, { ok: true })
    }
    const result = await Promise.all([http.get('/one'), http.get('/two'), http.get('/three')])
    expect(result.every(item => item.data.ok)).toBe(true)
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(session.accessToken).toBe('new-access')
    expect(session.refreshToken).toBe('new-refresh')
    expect(sessionStorage.getItem('student-connect.access-token')).toBeNull()
  })

  it('clears expired sessions when refresh is rejected, without looping', async () => {
    const refresh = vi.fn<AxiosAdapter>(async config => denied(config))
    publicHttp.defaults.adapter = refresh
    http.defaults.adapter = async config => denied(config)
    await expect(http.get('/private')).rejects.toMatchObject({ status: 401, code: 'TOKEN_REVOKED' })
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(session.refreshToken).toBeNull()
    expect(session.accessToken).toBeNull()
  })

  it('does not resurrect a session when a refresh finishes after logout', async () => {
    let finish!: (response: AxiosResponse) => void
    let config!: InternalAxiosRequestConfig
    publicHttp.defaults.adapter = async value => { config = value; return new Promise(resolve => { finish = resolve }) }
    const pending = refreshSession()
    await vi.waitFor(() => expect(finish).toBeDefined())
    session.clear()
    finish(response(config, newTokens))
    await expect(pending).rejects.toMatchObject({ code: 'SESSION_CHANGED' })
    expect(session.refreshToken).toBeNull()
    expect(session.accessToken).toBeNull()
  })

  it('does not replay a request belonging to a different logged-in user', async () => {
    let reject!: (reason: unknown) => void
    let config!: InternalAxiosRequestConfig
    const adapter = vi.fn<AxiosAdapter>(async value => { config = value; return new Promise((_resolve, rejectPromise) => { reject = rejectPromise }) })
    http.defaults.adapter = adapter
    const pending = http.get('/old-user-resource')
    await vi.waitFor(() => expect(reject).toBeDefined())
    session.start(newTokens)
    reject(new AxiosError('Unauthorized', 'ERR_BAD_RESPONSE', config, undefined, response(config, {}, 401)))
    await expect(pending).rejects.toMatchObject({ code: 'SESSION_CHANGED' })
    expect(adapter).toHaveBeenCalledTimes(1)
    expect(session.accessToken).toBe('new-access')
  })

  it('does not refresh a second time when the retried request is also unauthorized', async () => {
    const refresh = vi.fn<AxiosAdapter>(async config => response(config, newTokens))
    publicHttp.defaults.adapter = refresh
    http.defaults.adapter = async config => denied(config)
    await expect(http.get('/private')).rejects.toMatchObject({ status: 401 })
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(session.accessToken).toBeNull()
  })

  it('preserves the refresh token on a temporary refresh network failure', async () => {
    publicHttp.defaults.adapter = async config => { throw new AxiosError('offline', 'ERR_NETWORK', config) }
    await expect(refreshSession()).rejects.toMatchObject({ code: 'NETWORK_ERROR' })
    expect(session.refreshToken).toBe('old-refresh')
  })
})
