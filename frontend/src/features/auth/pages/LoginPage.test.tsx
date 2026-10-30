import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from './LoginPage'
import { ApiError } from '@/lib/api-error'

const mockLogin = vi.fn()
const mockAuth = {
  user: null,
  status: 'anonymous',
  login: mockLogin,
  logout: vi.fn(),
  retry: vi.fn(),
  error: null,
}

vi.mock('@/features/auth', () => ({
  useAuth: () => mockAuth,
  roleHome: {
    STUDENT: '/student',
    COMPANY: '/company',
    ADMIN: '/admin',
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuth.user = null
    mockAuth.status = 'anonymous'
  })

  it('renders login form elements and Stitch branding without SSO buttons', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Đăng nhập tài khoản')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/tennguoidung@school.edu.vn/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Nhập mật khẩu của bạn/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Đăng nhập/i })).toBeInTheDocument()
    expect(screen.getByText(/Đăng ký tài khoản Doanh nghiệp/i)).toBeInTheDocument()
    expect(screen.getByText(/Quên mật khẩu\?/i)).toBeInTheDocument()

    // Đảm bảo không có nút SSO/Google
    expect(screen.queryByText(/Google/i)).not.toBeInTheDocument()
  })

  it('toggles password visibility when eye button is clicked', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )

    const pwdInput = screen.getByPlaceholderText(/Nhập mật khẩu của bạn/i)
    expect(pwdInput).toHaveAttribute('type', 'password')

    const toggleBtn = screen.getByRole('button', { name: /Hiện mật khẩu/i })
    await userEvent.click(toggleBtn)
    expect(pwdInput).toHaveAttribute('type', 'text')

    const hideBtn = screen.getByRole('button', { name: /Ẩn mật khẩu/i })
    await userEvent.click(hideBtn)
    expect(pwdInput).toHaveAttribute('type', 'password')
  })

  it('displays PENDING_APPROVAL warning banner when account is waiting for school approval', async () => {
    mockLogin.mockRejectedValueOnce(
      new ApiError('Tài khoản đang chờ nhà trường phê duyệt', 403, 'ACCOUNT_PENDING_APPROVAL')
    )

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )

    await userEvent.type(screen.getByPlaceholderText(/tennguoidung@school.edu.vn/i), 'hr@fpt.com')
    await userEvent.type(screen.getByPlaceholderText(/Nhập mật khẩu của bạn/i), 'Secret@123')
    await userEvent.click(screen.getByRole('button', { name: /Đăng nhập/i }))

    await waitFor(() => {
      expect(screen.getByText('PENDING_APPROVAL')).toBeInTheDocument()
      expect(screen.getByText(/Tài khoản doanh nghiệp đang chờ nhà trường phê duyệt/i)).toBeInTheDocument()
    })
  })

  it('displays LOCKED warning banner with reason when account is locked', async () => {
    mockLogin.mockRejectedValueOnce(
      new ApiError('Cung cấp thông tin không xác thực', 403, 'ACCOUNT_LOCKED')
    )

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )

    await userEvent.type(screen.getByPlaceholderText(/tennguoidung@school.edu.vn/i), 'locked@student.edu.vn')
    await userEvent.type(screen.getByPlaceholderText(/Nhập mật khẩu của bạn/i), 'Secret@123')
    await userEvent.click(screen.getByRole('button', { name: /Đăng nhập/i }))

    await waitFor(() => {
      expect(screen.getByText('LOCKED')).toBeInTheDocument()
      expect(screen.getByText(/Cung cấp thông tin không xác thực/i)).toBeInTheDocument()
      expect(screen.getByText(/Vui lòng liên hệ Quản trị viên/i)).toBeInTheDocument()
    })
  })

  it('displays TOO_MANY_ATTEMPTS banner when rate limited', async () => {
    mockLogin.mockRejectedValueOnce(
      new ApiError('Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau 1 phút.', 429, 'TOO_MANY_ATTEMPTS')
    )

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    )

    await userEvent.type(screen.getByPlaceholderText(/tennguoidung@school.edu.vn/i), 'brute@force.com')
    await userEvent.type(screen.getByPlaceholderText(/Nhập mật khẩu của bạn/i), 'WrongPass')
    await userEvent.click(screen.getByRole('button', { name: /Đăng nhập/i }))

    await waitFor(() => {
      expect(screen.getByText(/Tạm khóa do quá nhiều lần thử/i)).toBeInTheDocument()
    })
  })
})
