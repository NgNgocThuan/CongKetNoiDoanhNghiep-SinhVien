import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ReportsPage from './ReportsPage'
import { reportsApi } from '../api/reports.api'
import type { Report } from '../types/reports.types'

vi.mock('../api/reports.api', () => ({
  reportsApi: {
    list: vi.fn(),
    get: vi.fn(),
    handle: vi.fn(),
  },
}))

const sampleReports: Report[] = [
  {
    id: 101,
    reporter_id: 12,
    target_type: 'JOB',
    target_id: 55,
    reason: 'Tin tuyển dụng bắt đóng tiền đồng phục 1 triệu đồng',
    status: 'PENDING',
    created_at: '2026-10-30T09:00:00Z',
  },
]

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('ReportsPage (D09)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(reportsApi.list).mockResolvedValue({
      items: sampleReports,
      total: 1,
      page: 1,
      size: 10,
      pages: 1,
    })
  })

  it('renders report list and stat cards', async () => {
    renderWithClient(<ReportsPage />)

    expect(await screen.findByText('Quản trị Báo cáo Vi phạm')).toBeInTheDocument()
    expect(await screen.findByText('Tin tuyển dụng bắt đóng tiền đồng phục 1 triệu đồng')).toBeInTheDocument()
    expect(screen.getByText('Tin tuyển dụng #55')).toBeInTheDocument()
  })

  it('opens drawer and submits RESOLVED verdict with cascade action', async () => {
    const user = userEvent.setup()
    vi.mocked(reportsApi.handle).mockResolvedValueOnce({
      ...sampleReports[0],
      status: 'RESOLVED',
      handled_by: 1,
      handled_at: '2026-10-30T10:00:00Z',
      resolution_note: 'Đã xác minh và đóng tin vi phạm',
    })

    renderWithClient(<ReportsPage />)

    const actionBtn = await screen.findByRole('button', { name: /Xét xử lý/i })
    await user.click(actionBtn)

    expect(await screen.findByText('Chi tiết Phản ánh & Phán quyết')).toBeInTheDocument()
    expect(screen.getByText('Xác nhận vi phạm (RESOLVED)')).toBeInTheDocument()

    // Note input
    const noteArea = screen.getByPlaceholderText(/Ghi rõ căn cứ xử lý/i)
    await user.type(noteArea, 'Đã xác minh và đóng tin vi phạm')

    const submitBtn = screen.getByRole('button', { name: /Xác nhận & Lưu phán quyết/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(reportsApi.handle).toHaveBeenCalledWith(101, {
        status: 'RESOLVED',
        resolution_note: 'Đã xác minh và đóng tin vi phạm',
        lock_target_user: false,
        close_target_job: true,
      })
    })
  })
})
