import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import UserAdminPage from './UserAdminPage'
import { usersApi } from '../api/users.api'
import type { UserRead } from '../types/users.types'

vi.mock('../api/users.api', () => ({
  usersApi: {
    list: vi.fn(),
    get: vi.fn(),
    lock: vi.fn(),
    unlock: vi.fn(),
    createAdmin: vi.fn(),
  },
}))

const sampleUsers: UserRead[] = [
  {
    id: 1,
    email: 'admin@university.edu.vn',
    role: 'ADMIN',
    status: 'ACTIVE',
    created_at: '2026-10-30T07:00:00Z',
    updated_at: '2026-10-30T07:00:00Z',
    admin: {
      id: 1,
      full_name: 'Nguyễn Văn Admin',
      position: 'Trưởng phòng Đào tạo',
    },
  },
  {
    id: 2,
    email: 'bad.user@company.com',
    role: 'COMPANY',
    status: 'LOCKED',
    locked_reason: 'Gian lận tuyển dụng',
    created_at: '2026-10-30T08:00:00Z',
    updated_at: '2026-10-30T08:00:00Z',
  },
]

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('UserAdminPage (D08)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.list).mockResolvedValue({
      items: sampleUsers,
      total: 2,
      page: 1,
      size: 10,
      pages: 1,
    })
  })

  it('renders user accounts with roles and statuses', async () => {
    renderWithClient(<UserAdminPage />)

    expect(await screen.findByText('Quản lý Tài khoản Hệ thống')).toBeInTheDocument()
    expect(await screen.findByText('Nguyễn Văn Admin')).toBeInTheDocument()
    expect(screen.getByText('bad.user@company.com')).toBeInTheDocument()
    expect(screen.getByText('Gian lận tuyển dụng')).toBeInTheDocument()
  })

  it('opens create admin modal and submits new admin form', async () => {
    const user = userEvent.setup()
    vi.mocked(usersApi.createAdmin).mockResolvedValueOnce({
      id: 3,
      email: 'new.admin@school.edu.vn',
      role: 'ADMIN',
      status: 'ACTIVE',
      created_at: '2026-10-30T10:00:00Z',
      updated_at: '2026-10-30T10:00:00Z',
      admin: {
        id: 2,
        full_name: 'Trần Thị Admin',
      },
    })

    renderWithClient(<UserAdminPage />)

    const createBtn = await screen.findByRole('button', { name: /Tạo tài khoản Admin mới/i })
    await user.click(createBtn)

    expect(await screen.findByRole('heading', { name: 'Tạo tài khoản Quản trị viên mới' })).toBeInTheDocument()

    const emailInput = screen.getByPlaceholderText('admin.cntt@university.edu.vn')
    const passInput = screen.getByPlaceholderText('Tối thiểu 8 ký tự an toàn')
    const nameInput = screen.getByPlaceholderText('Nguyễn Văn A')

    await user.type(emailInput, 'new.admin@school.edu.vn')
    await user.type(passInput, 'Password123#')
    await user.type(nameInput, 'Trần Thị Admin')

    const submitBtn = screen.getByRole('button', { name: /^Tạo tài khoản$/ })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(usersApi.createAdmin).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'new.admin@school.edu.vn',
          password: 'Password123#',
          full_name: 'Trần Thị Admin',
        })
      )
    })
  })

  it('opens lock modal and submits lock reason', async () => {
    const user = userEvent.setup()
    vi.mocked(usersApi.lock).mockResolvedValueOnce({
      ...sampleUsers[0],
      status: 'LOCKED',
      locked_reason: 'Vi phạm chính sách bảo mật',
    })

    renderWithClient(<UserAdminPage />)

    const lockBtn = await screen.findByRole('button', { name: /^Khóa tài khoản$/ })
    await user.click(lockBtn)

    expect(await screen.findByRole('heading', { name: 'Xác nhận Khóa tài khoản' })).toBeInTheDocument()

    const reasonInput = screen.getByPlaceholderText(/Ghi rõ hành vi vi phạm/i)
    await user.type(reasonInput, 'Vi phạm chính sách bảo mật')

    const confirmBtn = screen.getByRole('button', { name: /Xác nhận Khóa tài khoản/i })
    await user.click(confirmBtn)

    await waitFor(() => {
      expect(usersApi.lock).toHaveBeenCalledWith(1, {
        reason: 'Vi phạm chính sách bảo mật',
      })
    })
  })

  it('unlocks a locked user directly', async () => {
    const user = userEvent.setup()
    vi.mocked(usersApi.unlock).mockResolvedValueOnce({
      ...sampleUsers[1],
      status: 'ACTIVE',
      locked_reason: null,
    })

    renderWithClient(<UserAdminPage />)

    const unlockBtn = await screen.findByRole('button', { name: /Mở khóa/i })
    await user.click(unlockBtn)

    await waitFor(() => {
      expect(usersApi.unlock).toHaveBeenCalledWith(2)
    })
  })
})
