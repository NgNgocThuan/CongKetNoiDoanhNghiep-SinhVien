import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { clearToken, setToken } from '@/lib/token'
import { AuthProvider, RequireRole } from './AuthProvider'

const jwt = (role: string) => `h.${btoa(JSON.stringify({ role }))}.s`

function renderAt(path = '/admin') {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/login" element={<div>Trang đăng nhập</div>} />
          <Route
            path="/admin"
            element={
              <RequireRole role="ADMIN">
                <div>Khu vực quản trị</div>
              </RequireRole>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

afterEach(() => clearToken())

describe('RequireRole', () => {
  it('chưa đăng nhập thì chuyển về trang đăng nhập', () => {
    renderAt()
    expect(screen.getByText('Trang đăng nhập')).toBeInTheDocument()
    expect(screen.queryByText('Khu vực quản trị')).not.toBeInTheDocument()
  })

  it('đúng role ADMIN thì vào được', () => {
    setToken(jwt('ADMIN'))
    renderAt()
    expect(screen.getByText('Khu vực quản trị')).toBeInTheDocument()
  })

  it('sai role (sinh viên) bị chặn, không thấy nội dung quản trị', () => {
    setToken(jwt('STUDENT'))
    renderAt()
    expect(screen.getByText('Không đủ quyền truy cập')).toBeInTheDocument()
    expect(screen.queryByText('Khu vực quản trị')).not.toBeInTheDocument()
  })
})
