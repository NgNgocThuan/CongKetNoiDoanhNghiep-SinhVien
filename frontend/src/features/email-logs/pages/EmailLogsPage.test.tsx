import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import EmailLogsPage from './EmailLogsPage'
import { emailLogsApi } from '../api/email-logs.api'
import type { EmailLogRead } from '../types/email-logs.types'

vi.mock('../api/email-logs.api', () => ({
  emailLogsApi: {
    list: vi.fn(),
    retry: vi.fn(),
  },
}))

const sampleEmailLogs: EmailLogRead[] = [
  {
    id: 1,
    recipient_email: 'student1@school.edu.vn',
    type: 'ACCOUNT_ACTIVATION',
    subject: 'Kích hoạt tài khoản sinh viên',
    status: 'SENT',
    retry_count: 0,
    sent_at: '2026-10-30T08:00:00Z',
    created_at: '2026-10-30T07:59:00Z',
  },
  {
    id: 2,
    recipient_email: 'company@hr.com',
    type: 'COMPANY_APPROVED',
    subject: 'Thông báo kết quả kiểm duyệt hồ sơ',
    status: 'FAILED',
    error_message: 'SMTP Connection timeout (421)',
    retry_count: 2,
    sent_at: null,
    created_at: '2026-10-30T08:30:00Z',
  },
  {
    id: 3,
    recipient_email: 'pending@school.edu.vn',
    type: 'PASSWORD_RESET',
    subject: 'Yêu cầu đặt lại mật khẩu',
    status: 'PENDING',
    retry_count: 0,
    sent_at: null,
    created_at: '2026-10-30T08:45:00Z',
  },
]

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('EmailLogsPage (D10)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(emailLogsApi.list).mockResolvedValue({
      items: sampleEmailLogs,
      total: 3,
      page: 1,
      size: 10,
      pages: 1,
    })
  })

  it('renders email logs table, badges including PENDING and error message', async () => {
    renderWithClient(<EmailLogsPage />)

    expect(await screen.findByText('Nhật ký Gửi Email Hệ thống')).toBeInTheDocument()
    expect(await screen.findByText('student1@school.edu.vn')).toBeInTheDocument()
    expect(screen.getByText('company@hr.com')).toBeInTheDocument()
    expect(screen.getByText('pending@school.edu.vn')).toBeInTheDocument()
    expect(screen.getByText(/SMTP Connection timeout/i)).toBeInTheDocument()
    expect(screen.getByText('Đã gửi (SENT)')).toBeInTheDocument()
    expect(screen.getByText('Thất bại (FAILED)')).toBeInTheDocument()
    expect(screen.getByText('Đang chờ gửi (PENDING)')).toBeInTheDocument()
  })

  it('triggers bulk retry queue when clicking action button', async () => {
    const user = userEvent.setup()
    vi.mocked(emailLogsApi.retry).mockResolvedValueOnce({
      retried_count: 1,
      message: 'Đã đưa 1 email lỗi vào hàng đợi gửi lại',
    })

    renderWithClient(<EmailLogsPage />)

    const retryBtn = await screen.findByRole('button', {
      name: /Xếp hàng gửi lại/i,
    })
    await user.click(retryBtn)

    await waitFor(() => {
      expect(emailLogsApi.retry).toHaveBeenCalledTimes(1)
    })

    expect(await screen.findByText('Đã đưa 1 email lỗi vào hàng đợi gửi lại')).toBeInTheDocument()
  })
})
