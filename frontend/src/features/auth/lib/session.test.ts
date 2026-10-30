import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { session } from './session'

const REFRESH_KEY = 'student-connect.refresh-token'

describe('session storage policy (remember vs tab session)', () => {
  beforeEach(() => {
    session.clear()
    sessionStorage.clear()
    localStorage.clear()
  })

  afterEach(() => {
    session.clear()
    sessionStorage.clear()
    localStorage.clear()
  })

  it('stores token ONLY in sessionStorage and clears localStorage when remember=false', () => {
    // Giả lập trước đó localStorage có token cũ
    localStorage.setItem(REFRESH_KEY, 'old-persisted-token')

    session.start(
      {
        access_token: 'access-123',
        refresh_token: 'refresh-session-only',
        token_type: 'bearer',
      },
      false
    )

    expect(session.accessToken).toBe('access-123')
    expect(session.refreshToken).toBe('refresh-session-only')
    expect(sessionStorage.getItem(REFRESH_KEY)).toBe('refresh-session-only')
    expect(localStorage.getItem(REFRESH_KEY)).toBeNull()
  })

  it('stores token in localStorage and clears sessionStorage when remember=true', () => {
    // Giả lập trước đó sessionStorage có token cũ
    sessionStorage.setItem(REFRESH_KEY, 'old-session-token')

    session.start(
      {
        access_token: 'access-456',
        refresh_token: 'refresh-persisted',
        token_type: 'bearer',
      },
      true
    )

    expect(session.accessToken).toBe('access-456')
    expect(session.refreshToken).toBe('refresh-persisted')
    expect(localStorage.getItem(REFRESH_KEY)).toBe('refresh-persisted')
    expect(sessionStorage.getItem(REFRESH_KEY)).toBeNull()
  })

  it('preserves current storage destination when rotating tokens via save() without remember arg', () => {
    // Trường hợp 1: Ban đầu là remember=true
    session.start(
      {
        access_token: 'acc-1',
        refresh_token: 'ref-1',
        token_type: 'bearer',
      },
      true
    )
    expect(localStorage.getItem(REFRESH_KEY)).toBe('ref-1')

    // RefreshSession xoay vòng token mới (không truyền remember)
    session.save({
      access_token: 'acc-2',
      refresh_token: 'ref-2',
      token_type: 'bearer',
    })
    expect(localStorage.getItem(REFRESH_KEY)).toBe('ref-2')
    expect(sessionStorage.getItem(REFRESH_KEY)).toBeNull()

    // Trường hợp 2: Ban đầu là remember=false
    session.start(
      {
        access_token: 'acc-3',
        refresh_token: 'ref-3',
        token_type: 'bearer',
      },
      false
    )
    expect(sessionStorage.getItem(REFRESH_KEY)).toBe('ref-3')
    expect(localStorage.getItem(REFRESH_KEY)).toBeNull()

    // RefreshSession xoay vòng token mới (không truyền remember)
    session.save({
      access_token: 'acc-4',
      refresh_token: 'ref-4',
      token_type: 'bearer',
    })
    expect(sessionStorage.getItem(REFRESH_KEY)).toBe('ref-4')
    expect(localStorage.getItem(REFRESH_KEY)).toBeNull()
  })

  it('clears all tokens from both sessionStorage and localStorage on clear()', () => {
    sessionStorage.setItem(REFRESH_KEY, 'some-token')
    localStorage.setItem(REFRESH_KEY, 'some-token')

    session.clear()

    expect(session.accessToken).toBeNull()
    expect(session.refreshToken).toBeNull()
    expect(sessionStorage.getItem(REFRESH_KEY)).toBeNull()
    expect(localStorage.getItem(REFRESH_KEY)).toBeNull()
  })
})
