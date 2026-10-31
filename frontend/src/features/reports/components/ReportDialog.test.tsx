import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReportDialog } from './ReportDialog'
import { reportsApi } from '../api/reports.api'

vi.mock('../api/reports.api', () => ({
  reportsApi: {
    create: vi.fn(),
  },
}))

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('ReportDialog (A08)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders trigger button and opens modal when clicked', async () => {
    const user = userEvent.setup()
    renderWithClient(
      <ReportDialog
        targetType="JOB"
        targetId={10}
        targetTitle="Thực tập sinh Frontend"
        trigger={<button>Báo cáo tin</button>}
      />
    )

    expect(screen.getByRole('button', { name: 'Báo cáo tin' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Báo cáo tin' }))

    expect(screen.getByText('Báo cáo nội dung hoặc hành vi vi phạm')).toBeInTheDocument()
    expect(screen.getByText('TIN TUYỂN DỤNG')).toBeInTheDocument()
    expect(screen.getByText('Thực tập sinh Frontend')).toBeInTheDocument()
  })

  it('submits report with selected category and details', async () => {
    const user = userEvent.setup()
    vi.mocked(reportsApi.create).mockResolvedValueOnce({
      id: 1,
      reporter_id: 2,
      target_type: 'JOB',
      target_id: 10,
      reason: '[Thu phí thực tập / Đặt cọc giữ chỗ sai quy định] Đòi cọc 500k',
      status: 'PENDING',
      created_at: '2026-10-30T10:00:00Z',
    })

    renderWithClient(
      <ReportDialog
        open={true}
        targetType="JOB"
        targetId={10}
        targetTitle="Thực tập sinh Frontend"
      />
    )

    const textarea = screen.getByPlaceholderText(/Nêu rõ tình huống/i)
    await user.type(textarea, 'Đòi cọc 500k')

    const submitBtn = screen.getByRole('button', { name: /Gửi báo cáo vi phạm/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(reportsApi.create).toHaveBeenCalledWith({
        target_type: 'JOB',
        target_id: 10,
        reason: '[Thu phí thực tập / Đặt cọc giữ chỗ sai quy định] Đòi cọc 500k',
      })
    })

    expect(await screen.findByText('Gửi báo cáo thành công!')).toBeInTheDocument()
  })
})
