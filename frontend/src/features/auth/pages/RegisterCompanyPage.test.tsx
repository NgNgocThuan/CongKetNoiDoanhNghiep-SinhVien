import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import RegisterCompanyPage from './RegisterCompanyPage'
import { authApi } from '../api/auth.api'

vi.mock('../api/auth.api', () => ({
  authApi: {
    registerCompany: vi.fn(),
  },
}))

describe('RegisterCompanyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all required and optional registration fields according to Stitch A02', () => {
    render(
      <MemoryRouter>
        <RegisterCompanyPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Đăng ký Tài khoản Doanh nghiệp Đối tác')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/hr@domain-company.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Nhập mật khẩu an toàn/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/VD: Công ty TNHH Phần mềm FPT/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/VD: 0101248141/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/https:\/\/domain-company.com/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Số nhà, tên đường/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/VD: Trần Thị Mai Lan/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/VD: 0982 123 456/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Gửi hồ sơ đăng ký/i })).toBeInTheDocument()
  })

  it('submits form with complete data and transitions to PENDING_APPROVAL status screen', async () => {
    vi.mocked(authApi.registerCompany).mockResolvedValueOnce({
      user_id: 10,
      company_id: 5,
      email: 'hr@vietnamtech.com',
      company_name: 'Vietnam Tech Corp',
      tax_code: '0109998888',
      status: 'PENDING_APPROVAL',
      verification_status: 'PENDING',
      message: 'Đăng ký thành công',
    })

    render(
      <MemoryRouter>
        <RegisterCompanyPage />
      </MemoryRouter>
    )

    await userEvent.type(screen.getByPlaceholderText(/hr@domain-company.com/i), 'hr@vietnamtech.com')
    await userEvent.type(screen.getByPlaceholderText(/Nhập mật khẩu an toàn/i), 'SecurePass@2025')
    await userEvent.type(screen.getByPlaceholderText(/VD: Công ty TNHH Phần mềm FPT/i), 'Vietnam Tech Corp')
    await userEvent.type(screen.getByPlaceholderText(/VD: 0101248141/i), '0109998888')
    await userEvent.type(screen.getByPlaceholderText(/https:\/\/domain-company.com/i), 'https://vietnamtech.com')
    await userEvent.type(screen.getByPlaceholderText(/Số nhà, tên đường/i), '123 Đường Cầu Giấy, Hà Nội')
    await userEvent.type(screen.getByPlaceholderText(/VD: Trần Thị Mai Lan/i), 'Nguyễn Văn Tuyển')
    await userEvent.type(screen.getByPlaceholderText(/VD: 0982 123 456/i), '0912345678')

    await userEvent.click(screen.getByRole('button', { name: /Gửi hồ sơ đăng ký/i }))

    await waitFor(() => {
      expect(authApi.registerCompany).toHaveBeenCalledWith({
        email: 'hr@vietnamtech.com',
        password: 'SecurePass@2025',
        company_name: 'Vietnam Tech Corp',
        tax_code: '0109998888',
        industry_id: null,
        website: 'https://vietnamtech.com',
        address: '123 Đường Cầu Giấy, Hà Nội',
        contact_name: 'Nguyễn Văn Tuyển',
        contact_phone: '0912345678',
      })
    })

    // Xác nhận hiển thị màn hình Chờ nhà trường phê duyệt (PENDING_APPROVAL)
    await waitFor(() => {
      expect(screen.getByText('Hồ sơ đang chờ Nhà trường phê duyệt')).toBeInTheDocument()
      expect(screen.getByText('PENDING_APPROVAL')).toBeInTheDocument()
      expect(screen.getByText(/Vietnam Tech Corp/i)).toBeInTheDocument()
      expect(screen.getByText(/Quay về trang Đăng nhập/i)).toBeInTheDocument()
    })
  })
})
