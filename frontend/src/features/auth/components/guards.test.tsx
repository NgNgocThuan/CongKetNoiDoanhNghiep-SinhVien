import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthContext } from '../auth-context'
import type { AuthContextValue } from '../auth-context'
import { RequireAuth, RequireRole } from './guards'
import type { User } from '../types/auth.types'

const user: User = { id: 1, email: 'student@test.com', role: 'STUDENT', status: 'ACTIVE' }
function fixture(value: Partial<AuthContextValue>) {
  const context: AuthContextValue = { user: null, status: 'anonymous', error: null,
    login: vi.fn(async () => user), logout: vi.fn(async () => {}), retry: vi.fn(async () => {}), ...value }
  render(<AuthContext.Provider value={context}><MemoryRouter initialEntries={['/admin']}><Routes>
    <Route path="/login" element={<h1>Đăng nhập</h1>} /><Route path="/403" element={<h1>Không có quyền</h1>} />
    <Route element={<RequireAuth />}><Route element={<RequireRole role="ADMIN" />}><Route path="/admin" element={<h1>Dữ liệu quản trị</h1>} /></Route></Route>
  </Routes></MemoryRouter></AuthContext.Provider>)
}
describe('route guards', () => {
  it('redirects anonymous users before rendering private content', () => {
    fixture({})
    expect(screen.getByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument()
    expect(screen.queryByText('Dữ liệu quản trị')).not.toBeInTheDocument()
  })
  it('blocks a different actor even when they type the protected URL directly', () => {
    fixture({ user, status: 'authenticated' })
    expect(screen.getByRole('heading', { name: 'Không có quyền' })).toBeInTheDocument()
  })
  it('renders the matching role', () => {
    fixture({ user: { ...user, role: 'ADMIN' }, status: 'authenticated' })
    expect(screen.getByRole('heading', { name: 'Dữ liệu quản trị' })).toBeInTheDocument()
  })
  it('waits for bootstrap rather than briefly showing the login or protected page', () => {
    fixture({ status: 'loading' })
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })
  it('shows a recoverable connection error without logging the user out', () => {
    fixture({ status: 'error', error: new Error('Không thể kết nối') })
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeInTheDocument()
  })
})
