import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RecommendedJobsPage from './RecommendedJobsPage'

vi.mock('../hooks', () => ({
  usePublicCompany: () => ({ data: { name: 'Example Company' }, isError: false }),
  useRecommendedJobs: () => ({
    isPending: false, isError: false, isFetching: false,
    data: { total: 2, pages: 1, items: [{
      job_id: 42, title: 'React Developer', company_id: 1,
      match: { score: 80, skill_score: 80, experience_score: 0, semantic_score: 0, matched_skills: ['React'], missing_skills: [], explanation: 'Khớp kỹ năng', computed_at: '2026-11-13T01:00:00Z' },
    }, {
      job_id: 43, title: 'Python Developer', company_id: 1,
      match: { score: 60, skill_score: 60, experience_score: 0, semantic_score: 0, matched_skills: ['Python'], missing_skills: ['SQL'], explanation: 'Khớp Python', computed_at: '2026-11-13T01:00:00Z' },
    }] },
  }),
}))
vi.mock('../components/ApplyDialog', () => ({ ApplyDialog: () => <div>Đang ứng tuyển</div> }))
vi.mock('../components/SaveJobButton', () => ({ SaveJobButton: () => <button>Lưu tin</button> }))

function mount() {
  return render(<MemoryRouter initialEntries={['/student/recommended']}><Routes>
    <Route path="/student/recommended" element={<RecommendedJobsPage />} />
    <Route path="/student/jobs/42" element={<div>Trang chi tiết đúng công việc</div>} />
  </Routes></MemoryRouter>)
}

describe('recommended job interactions', () => {
  beforeEach(() => {
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })))
  })
  it('opens the correct job from its linked title', () => {
    mount()
    fireEvent.click(screen.getByRole('link', { name: 'React Developer' }))
    expect(screen.getByText('Trang chi tiết đúng công việc')).toBeInTheDocument()
  })
  it('opens the correct job from the view button', () => {
    mount()
    fireEvent.click(screen.getAllByRole('button', { name: 'Xem tin' })[0])
    expect(screen.getByText('Trang chi tiết đúng công việc')).toBeInTheDocument()
  })
  it('keeps apply independent of card navigation', () => {
    mount()
    fireEvent.click(screen.getAllByRole('button', { name: /^Ứng tuyển$/ })[0])
    expect(screen.getByText('Đang ứng tuyển')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'React Developer' })).toBeInTheDocument()
  })
  it('starts unselected and updates analysis when switching cards', () => {
    mount()
    const aside = document.querySelector('aside')!
    expect(within(aside).getByText(/Chọn một thẻ việc/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('article', { name: 'Gợi ý Python Developer' }))
    expect(within(aside).getByRole('heading', { name: 'Python Developer' })).toBeInTheDocument()
    expect(within(aside).getByText('SQL')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('article', { name: 'Gợi ý React Developer' }))
    expect(within(aside).getByRole('heading', { name: 'React Developer' })).toBeInTheDocument()
    expect(within(aside).queryByText('SQL')).not.toBeInTheDocument()
  })
  it('updates analysis from the explanation button without navigating', () => {
    mount()
    const card = screen.getByRole('article', { name: 'Gợi ý Python Developer' })
    fireEvent.click(within(card).getByRole('button', { name: 'Vì sao được gợi ý?' }))
    expect(within(document.querySelector('aside')!).getByRole('heading', { name: 'Python Developer' })).toBeInTheDocument()
    expect(within(card).getByRole('button', { pressed: true })).toBeInTheDocument()
  })
})
