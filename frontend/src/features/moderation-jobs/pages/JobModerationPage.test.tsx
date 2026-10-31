import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import JobModerationPage from './JobModerationPage'
import { jobsApi } from '../api/jobs.api'
import type { AdminJobDetailRead, AdminJobRead } from '../types/jobs.types'

vi.mock('../api/jobs.api', () => ({
  jobsApi: {
    list: vi.fn(),
    get: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    close: vi.fn(),
  },
}))

const sampleJobs: AdminJobRead[] = [
  {
    id: 10,
    company_id: 2,
    title: 'Thực tập sinh Backend Python FastAPI',
    position: 'Backend Developer Intern',
    job_type_id: 1,
    quantity: 5,
    salary_min: 5000000,
    salary_max: 8000000,
    is_salary_negotiable: false,
    location: 'Hà Nội',
    work_mode: 'HYBRID',
    min_gpa: 3.0,
    deadline: '2026-11-30',
    status: 'PENDING_APPROVAL',
    view_count: 0,
    created_at: '2026-10-30T08:00:00Z',
    updated_at: '2026-10-30T08:00:00Z',
  },
]

const sampleDetail: AdminJobDetailRead = {
  ...sampleJobs[0],
  description: 'Tham gia phát triển API microservices',
  requirements: 'Nắm vững Python và cơ sở dữ liệu quan hệ',
  benefits: 'Phụ cấp hấp dẫn, hỗ trợ dấu thực tập',
  parsed_json: {
    skills: 'Python, FastAPI, SQL',
  },
}

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('JobModerationPage (D05)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(jobsApi.list).mockResolvedValue({
      items: sampleJobs,
      total: 1,
      page: 1,
      size: 10,
      pages: 1,
    })
    vi.mocked(jobsApi.get).mockResolvedValue(sampleDetail)
  })

  it('renders job moderation table and job details', async () => {
    renderWithClient(<JobModerationPage />)

    expect(await screen.findByText('Kiểm duyệt Tin tuyển dụng Thực tập')).toBeInTheDocument()
    expect(await screen.findByText('Thực tập sinh Backend Python FastAPI')).toBeInTheDocument()
    expect(screen.getByText('5 - 8 tr VNĐ')).toBeInTheDocument()
  })

  it('approves job from slide-over drawer', async () => {
    const user = userEvent.setup()
    vi.mocked(jobsApi.approve).mockResolvedValueOnce({
      ...sampleDetail,
      status: 'APPROVED',
      approved_by: 1,
      approved_at: '2026-10-30T09:00:00Z',
    })

    renderWithClient(<JobModerationPage />)

    const checkBtn = await screen.findByRole('button', { name: /Kiểm duyệt/i })
    await user.click(checkBtn)

    expect(await screen.findByText('Tham gia phát triển API microservices')).toBeInTheDocument()
    const approveBtn = screen.getByRole('button', { name: /Phê duyệt tin/i })
    await user.click(approveBtn)

    await waitFor(() => {
      expect(jobsApi.approve).toHaveBeenCalledWith(10)
    })
  })

  it('rejects job with mandatory reason', async () => {
    const user = userEvent.setup()
    vi.mocked(jobsApi.reject).mockResolvedValueOnce({
      ...sampleDetail,
      status: 'REJECTED',
      reject_reason: 'Nội dung thiếu yêu cầu chuyên môn',
    })

    renderWithClient(<JobModerationPage />)

    const checkBtn = await screen.findByRole('button', { name: /Kiểm duyệt/i })
    await user.click(checkBtn)

    const rejectBtn = await screen.findByRole('button', { name: /Từ chối tin/i })
    await user.click(rejectBtn)

    const reasonInput = screen.getByPlaceholderText(/Nêu rõ lý do/i)
    await user.type(reasonInput, 'Nội dung thiếu yêu cầu chuyên môn')

    const confirmRejectBtn = screen.getByRole('button', { name: /Xác nhận Từ chối/i })
    await user.click(confirmRejectBtn)

    await waitFor(() => {
      expect(jobsApi.reject).toHaveBeenCalledWith(10, {
        reject_reason: 'Nội dung thiếu yêu cầu chuyên môn',
      })
    })
  })
})
