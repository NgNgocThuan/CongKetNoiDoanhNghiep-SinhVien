import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NotificationBell } from './NotificationBell'
import { notificationsApi } from '../api/notifications.api'
import { ApiError } from '@/lib/api-error'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const mockUser = {
  id: 1,
  email: 'student@school.edu.vn',
  role: 'STUDENT' as const,
  status: 'ACTIVE',
}

vi.mock('@/features/auth', () => ({
  useAuth: () => ({ user: mockUser }),
  roleHome: {
    STUDENT: '/student',
    COMPANY: '/company',
    ADMIN: '/admin',
  },
}))

vi.mock('../api/notifications.api', () => ({
  notificationsApi: {
    count: vi.fn(),
    list: vi.fn(),
    read: vi.fn(),
    readAll: vi.fn(),
  },
}))

const sampleNotifications = [
  {
    id: 101,
    title: 'Đơn ứng tuyển được chấp nhận',
    content: 'Doanh nghiệp FPT Software đã duyệt đơn ứng tuyển của bạn.',
    is_read: false,
    created_at: '2026-10-30T10:00:00Z',
    ref_type: 'APPLICATION',
    ref_id: 12,
  },
  {
    id: 102,
    title: 'Tin tuyển dụng mới',
    content: 'Viettel tuyển thực tập sinh React.',
    is_read: true,
    created_at: '2026-10-29T10:00:00Z',
    ref_type: 'JOB',
    ref_id: 5,
  },
]

function renderWithClient() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <NotificationBell />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('NotificationBell & Flyout Drawer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(notificationsApi.count).mockResolvedValue({ unread_count: 1 })
    vi.mocked(notificationsApi.list).mockResolvedValue({
      items: sampleNotifications,
      total: 2,
      page: 1,
      size: 10,
      pages: 1,
    })
    vi.mocked(notificationsApi.read).mockResolvedValue({} as never)
    vi.mocked(notificationsApi.readAll).mockResolvedValue({ updated_count: 1, message: 'OK' } as never)
  })

  it('renders bell with unread badge count', async () => {
    renderWithClient()

    expect(await screen.findByText('1')).toBeInTheDocument()
  })

  it('opens flyout drawer on click and marks all as read when button clicked', async () => {
    renderWithClient()

    const bellBtn = screen.getByRole('button', { name: /Thông báo/i })
    await userEvent.click(bellBtn)

    expect(await screen.findByText('Thông báo mới nhận')).toBeInTheDocument()
    expect(screen.getByText('Đơn ứng tuyển được chấp nhận')).toBeInTheDocument()
    expect(screen.getByText('Đánh dấu tất cả đã đọc')).toBeInTheDocument()

    await userEvent.click(screen.getByText('Đánh dấu tất cả đã đọc'))
    await waitFor(() => {
      expect(notificationsApi.readAll).toHaveBeenCalledTimes(1)
    })
  })

  it('marks single notification as read and navigates to target when clicked', async () => {
    renderWithClient()

    const bellBtn = screen.getByRole('button', { name: /Thông báo/i })
    await userEvent.click(bellBtn)

    const unreadItem = await screen.findByText('Đơn ứng tuyển được chấp nhận')
    await userEvent.click(unreadItem)

    await waitFor(() => {
      expect(notificationsApi.read).toHaveBeenCalledWith(101)
      expect(mockNavigate).toHaveBeenCalledWith('/student/applications')
    })
  })

  it('displays error state and retry button when loading notifications fails', async () => {
    vi.mocked(notificationsApi.list).mockRejectedValueOnce(
      new ApiError('Tài khoản không có quyền truy cập', 403, 'FORBIDDEN')
    )

    renderWithClient()

    const bellBtn = screen.getByRole('button', { name: /Thông báo/i })
    await userEvent.click(bellBtn)

    expect(await screen.findByText(/Tài khoản không có quyền truy cập/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Thử lại/i })).toBeInTheDocument()
    expect(screen.queryByText(/Bạn đã cập nhật mọi thông tin!/i)).not.toBeInTheDocument()

    // Bấm Thử lại thành công
    vi.mocked(notificationsApi.list).mockResolvedValueOnce({
      items: sampleNotifications,
      total: 2,
      page: 1,
      size: 10,
      pages: 1,
    })
    await userEvent.click(screen.getByRole('button', { name: /Thử lại/i }))

    expect(await screen.findByText('Đơn ứng tuyển được chấp nhận')).toBeInTheDocument()
  })
})
