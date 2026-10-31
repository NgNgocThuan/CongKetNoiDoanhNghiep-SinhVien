import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CompanyModerationPage from './CompanyModerationPage'
import { companiesApi } from '../api/companies.api'
import type { AdminCompanyDetailRead, AdminCompanyRead } from '../types/companies.types'

vi.mock('../api/companies.api', () => ({
  companiesApi: {
    list: vi.fn(),
    get: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
  },
}))

const sampleCompanies: AdminCompanyRead[] = [
  {
    id: 1,
    user_id: 10,
    name: 'Công ty Cổ phần Công nghệ ABC',
    tax_code: '0101248141',
    company_size: '51-200',
    address: '123 Đường Cầu Giấy, Hà Nội',
    website: 'https://abc.tech',
    contact_name: 'Nguyễn Văn Q',
    contact_phone: '0987654321',
    verification_status: 'PENDING',
    created_at: '2026-10-30T08:00:00Z',
    updated_at: '2026-10-30T08:00:00Z',
  },
]

const sampleDetail: AdminCompanyDetailRead = {
  ...sampleCompanies[0],
  description: 'Công ty phát triển phần mềm doanh nghiệp',
  documents: [
    {
      id: 5,
      doc_type: 'BUSINESS_LICENSE',
      file_url: 'https://cdn.example.com/dkkd.pdf',
      uploaded_at: '2026-10-30T08:05:00Z',
    },
  ],
}

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('CompanyModerationPage (D04)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(companiesApi.list).mockResolvedValue({
      items: sampleCompanies,
      total: 1,
      page: 1,
      size: 10,
      pages: 1,
    })
    vi.mocked(companiesApi.get).mockResolvedValue(sampleDetail)
  })

  it('renders company list and pending stat', async () => {
    renderWithClient(<CompanyModerationPage />)

    expect(await screen.findByText('Kiểm duyệt Hồ sơ Doanh nghiệp')).toBeInTheDocument()
    expect(await screen.findByText('Công ty Cổ phần Công nghệ ABC')).toBeInTheDocument()
    expect(screen.getByText('MST: 0101248141')).toBeInTheDocument()
  })

  it('opens drawer and approves company', async () => {
    const user = userEvent.setup()
    vi.mocked(companiesApi.approve).mockResolvedValueOnce({
      ...sampleDetail,
      verification_status: 'APPROVED',
      verified_by: 1,
      verified_at: '2026-10-30T09:00:00Z',
    })

    renderWithClient(<CompanyModerationPage />)

    const checkBtn = await screen.findByRole('button', { name: /Xét duyệt/i })
    await user.click(checkBtn)

    expect(await screen.findByText('Giấy phép ĐKKD')).toBeInTheDocument()
    const approveBtn = screen.getByRole('button', { name: /Phê duyệt Doanh nghiệp/i })
    await user.click(approveBtn)

    await waitFor(() => {
      expect(companiesApi.approve).toHaveBeenCalledWith(1)
    })
  })

  it('submits rejection with required reason', async () => {
    const user = userEvent.setup()
    vi.mocked(companiesApi.reject).mockResolvedValueOnce({
      ...sampleDetail,
      verification_status: 'REJECTED',
      reject_reason: 'Mã số thuế không tồn tại',
      verified_at: '2026-10-30T09:00:00Z',
    })

    renderWithClient(<CompanyModerationPage />)

    const checkBtn = await screen.findByRole('button', { name: /Xét duyệt/i })
    await user.click(checkBtn)

    const rejectBtn = await screen.findByRole('button', { name: /Từ chối hồ sơ/i })
    await user.click(rejectBtn)

    const reasonInput = screen.getByPlaceholderText(/Nêu rõ lý do/i)
    await user.type(reasonInput, 'Mã số thuế không tồn tại')

    const confirmRejectBtn = screen.getByRole('button', { name: /Xác nhận Từ chối/i })
    await user.click(confirmRejectBtn)

    await waitFor(() => {
      expect(companiesApi.reject).toHaveBeenCalledWith(1, {
        reject_reason: 'Mã số thuế không tồn tại',
      })
    })
  })
})
