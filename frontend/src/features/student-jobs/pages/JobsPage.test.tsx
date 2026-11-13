import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import JobsPage from './JobsPage'

vi.mock('../api', () => ({ jobsApi: {
  search: vi.fn(async () => ({ items: [], page: 1, size: 12, pages: 1, total: 0 })),
  catalog: vi.fn(async () => ({ items: [{ id: 3, name: 'Công nghệ thông tin' }], total: 1, pages: 1 })),
} }))
vi.mock('../components/JobCard', () => ({ JobCard: () => null }))

function Location() { return <output aria-label="Địa chỉ tìm kiếm">{useLocation().search}</output> }
function mount(initial = '/student/jobs') {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <MemoryRouter initialEntries={[initial]}><JobsPage /><Location /></MemoryRouter>
  </QueryClientProvider>)
}

describe('job search sidebar', () => {
  it('submits keyword and externally associated sidebar filters together', async () => {
    mount('/student/jobs?page=3')
    await waitFor(() => expect(screen.getByLabelText('Lĩnh vực')).not.toBeDisabled())
    fireEvent.change(screen.getByLabelText('Từ khóa'), { target: { value: 'Python' } })
    fireEvent.change(screen.getByLabelText('Địa điểm'), { target: { value: 'Hà Nội' } })
    fireEvent.change(screen.getByLabelText('Hình thức làm việc'), { target: { value: 'HYBRID' } })
    fireEvent.change(screen.getByLabelText('Lĩnh vực'), { target: { value: '3' } })
    fireEvent.submit(document.getElementById('student-job-search')!)
    await waitFor(() => {
      const params = new URLSearchParams(screen.getByLabelText('Địa chỉ tìm kiếm').textContent!)
      expect(params.get('q')).toBe('Python')
      expect(params.get('location')).toBe('Hà Nội')
      expect(params.get('work_mode')).toBe('HYBRID')
      expect(params.get('industry_id')).toBe('3')
      expect(params.has('page')).toBe(false)
    })
  })
  it('opens filters explicitly and clears filters while preserving search text', async () => {
    mount('/student/jobs?q=Python&location=Hanoi&work_mode=REMOTE&page=2')
    const toggle = screen.getByRole('button', { name: /Bộ lọc/ })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa bộ lọc' }))
    await waitFor(() => {
      const params = new URLSearchParams(screen.getByLabelText('Địa chỉ tìm kiếm').textContent!)
      expect(params.get('q')).toBe('Python')
      expect(params.get('location')).toBe('Hanoi')
      expect(params.has('work_mode')).toBe(false)
      expect(params.has('page')).toBe(false)
    })
  })
})
