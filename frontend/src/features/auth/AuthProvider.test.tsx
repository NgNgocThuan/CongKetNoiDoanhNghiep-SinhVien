import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './hooks/useAuth'
import { authApi } from './api/auth.api'
import { session } from './lib/session'
import type { User } from './types/auth.types'

vi.mock('./api/auth.api', () => ({ authApi: { login: vi.fn(), me: vi.fn(), logout: vi.fn() } }))
const user: User = { id: 7, email: 'new@test.com', role: 'COMPANY', status: 'ACTIVE' }
const tokens = { access_token: 'test-access', refresh_token: 'test-refresh', token_type: 'bearer' }
function Probe() {
  const auth = useAuth()
  return <><p>{auth.status}</p><p>{auth.user?.email}</p><button onClick={() => void auth.login({ email: user.email, password: 'Password@123' }).catch(() => {})}>Login</button><button onClick={() => void auth.logout().catch(() => {})}>Logout</button></>
}
function fixture() {
  const client = new QueryClient()
  render(<QueryClientProvider client={client}><AuthProvider><Probe /></AuthProvider></QueryClientProvider>)
  return client
}
beforeEach(() => { session.clear(); vi.mocked(authApi.login).mockResolvedValue(tokens); vi.mocked(authApi.me).mockResolvedValue(user); vi.mocked(authApi.logout).mockResolvedValue({} as Awaited<ReturnType<typeof authApi.logout>>) })
describe('auth session lifecycle', () => {
  it('clears previous-user query data on login and logout', async () => {
    const client = fixture()
    await screen.findByText('anonymous')
    client.setQueryData(['old-private-data'], 'private')
    await userEvent.click(screen.getByText('Login'))
    await screen.findByText(user.email)
    expect(client.getQueryData(['old-private-data'])).toBeUndefined()
    client.setQueryData(['current-private-data'], 'private')
    await userEvent.click(screen.getByText('Logout'))
    await screen.findByText('anonymous')
    expect(client.getQueryData(['current-private-data'])).toBeUndefined()
    expect(session.refreshToken).toBeNull()
  })
  it('keeps the user logged out when logout cannot reach the backend', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('offline'))
    fixture()
    await userEvent.click(screen.getByText('Login'))
    await screen.findByText('authenticated')
    await userEvent.click(screen.getByText('Logout'))
    await screen.findByText('anonymous')
    expect(session.accessToken).toBeNull()
  })
  it('does not restore an in-flight login after logout', async () => {
    let resolve!: (user: User) => void
    vi.mocked(authApi.me).mockImplementation(() => new Promise(done => { resolve = done }))
    fixture()
    await userEvent.click(screen.getByText('Login'))
    await waitFor(() => expect(resolve).toBeDefined())
    await userEvent.click(screen.getByText('Logout'))
    resolve(user)
    await waitFor(() => expect(session.accessToken).toBeNull())
    expect(screen.queryByText(user.email)).not.toBeInTheDocument()
  })
})
