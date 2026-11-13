import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { http } from '@/lib/http'
import { CVAnalysis } from './CVAnalysis'
import type { CV } from '../types'

vi.mock('@/lib/http', () => ({ http: { post: vi.fn(async () => ({ data: { added_skills: ['React'] } })) } }))

describe('student approves extracted CV skills', () => {
  it('requires explicit selection and only sends approved skills', async () => {
    const cv: CV = { id: 5, title: 'CV Frontend', type: 'UPLOADED', file_url: 'cv.pdf', content_json: null, parsed_json: { skills: ['React', 'SQL'] }, is_default: true, parsed_at: '2026-11-13', created_at: '2026-11-13', updated_at: '2026-11-13' }
    render(<QueryClientProvider client={new QueryClient()}><CVAnalysis cv={cv} /></QueryClientProvider>)
    const button = screen.getByRole('button', { name: /Xác nhận & thêm vào hồ sơ/ })
    expect(button).toBeDisabled()
    expect(http.post).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('checkbox', { name: 'React' }))
    expect(screen.getByRole('checkbox', { name: 'SQL' })).not.toBeChecked()
    fireEvent.click(button)
    await waitFor(() => expect(http.post).toHaveBeenCalledWith('/cvs/5/confirm-skills', { skills: ['React'] }))
    expect(await screen.findByText('Đã lưu kỹ năng vào hồ sơ và đồng bộ CV online.')).toBeInTheDocument()
  })
})
