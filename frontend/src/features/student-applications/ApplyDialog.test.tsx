import { vi, describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ApplyDialog } from './components/ApplyDialog'
import { http } from '@/lib/http'
import { ApiError } from '@/lib/api-error'
vi.mock('@/lib/http', () => ({ http: { get: vi.fn(), post: vi.fn() } }))
const get = vi.mocked(http.get),
  post = vi.mocked(http.post)
function mount(onSuccess = vi.fn()) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
          },
        })
      }
    >
      <MemoryRouter>
        <ApplyDialog open jobId={11} invitationId={22} onClose={vi.fn()} onSuccess={onSuccess} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
beforeEach(() => {
  cleanup()
  vi.resetAllMocks()
  get.mockImplementation(async (url) => ({
    data:
      url === '/cvs/me'
        ? [
            { id: 1, title: 'CV phụ', is_default: false },
            { id: 2, title: 'CV mặc định', is_default: true },
          ]
        : { id: 11, title: 'Backend Intern', company: { name: 'Acme' } },
  }))
})
describe('ApplyDialog', () => {
  it('selects default CV and preserves invitation when submitting', async () => {
    const onSuccess = vi.fn()
    post.mockResolvedValue({ data: { id: 44 } })
    mount(onSuccess)
    await screen.findByRole('option', { name: 'CV mặc định · Mặc định' })
    expect(screen.getByRole('combobox')).toHaveValue('2')
    await userEvent.type(screen.getByRole('textbox'), 'Em quan tâm vị trí Backend.')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi đơn ứng tuyển' }))
    await waitFor(() =>
      expect(post).toHaveBeenCalledWith('/applications', {
        job_id: 11,
        cv_id: 2,
        invitation_id: 22,
        cover_letter: 'Em quan tâm vị trí Backend.',
      }),
    )
    expect(onSuccess).toHaveBeenCalledWith({ id: 44 })
  })
  it('shows business conflict and keeps the modal available', async () => {
    post.mockRejectedValue(new ApiError('Bạn đã ứng tuyển tin này', 409, 'DUPLICATE_APPLICATION'))
    mount()
    await screen.findByRole('combobox')
    await userEvent.click(screen.getByRole('button', { name: 'Gửi đơn ứng tuyển' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Bạn đã ứng tuyển tin này')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })
  it('offers CV creation instead of sending an invalid application', async () => {
    get.mockImplementation(async (url) => ({
      data: url === '/cvs/me' ? [] : { title: 'Backend Intern', company: { name: 'Acme' } },
    }))
    mount()
    expect(await screen.findByRole('link', { name: 'Tạo hoặc tải CV lên' })).toHaveAttribute(
      'href',
      '/student/cvs',
    )
    expect(screen.queryByRole('button', { name: 'Gửi đơn ứng tuyển' })).not.toBeInTheDocument()
  })
})
