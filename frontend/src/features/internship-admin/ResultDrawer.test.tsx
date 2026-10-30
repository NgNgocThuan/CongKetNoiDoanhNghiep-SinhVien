import { App } from 'antd'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ResultDrawer from './ResultDrawer'
import type { InternshipResult } from './types'

const mocks = vi.hoisted(() => ({ save: vi.fn().mockResolvedValue({}), confirm: vi.fn().mockResolvedValue({}) }))
vi.mock('./api', () => ({
  useSaveLecturerReview: () => ({ mutateAsync: mocks.save, isPending: false }),
  useConfirmResult: () => ({ mutateAsync: mocks.confirm, isPending: false }),
}))
function result(id: number): InternshipResult {
  return { id, term_id: 1, term_student_id: id, student_id: id, student_code: 'SV' + id,
    student_name: 'Sinh viên ' + id, lecturer_id: null, lecturer_name: null, company_id: null,
    company_name: null, application_id: null, company_evaluation: null, company_score: null,
    evaluated_at: null, lecturer_comment: 'Nhận xét của sinh viên ' + id,
    lecturer_score: id === 1 ? '8.00' : '5.00', result: 'PENDING', confirmed_by: null, confirmed_at: null }
}
describe('ResultDrawer isolates each student review', () => {
  beforeEach(() => { vi.clearAllMocks() })
  it.each([false, true])('does not submit student A values for student B (close between: %s)', async closeBetween => {
    const onClose = vi.fn()
    const ui = (value: InternshipResult | null) => <App><ResultDrawer result={value} onClose={onClose} /></App>
    const view = render(ui(result(1)))
    await expect(screen.findByRole('textbox', { name: 'Nhận xét' })).resolves.toHaveValue('Nhận xét của sinh viên 1')
    if (closeBetween) view.rerender(ui(null))
    view.rerender(ui(result(2)))
    expect(await screen.findByRole('textbox', { name: 'Nhận xét' })).toHaveValue('Nhận xét của sinh viên 2')
    expect(screen.getByRole('spinbutton', { name: 'Điểm (thang 10)' })).toHaveValue('5.0')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu nhận xét' }))
    await waitFor(() => expect(mocks.save).toHaveBeenCalledWith({ resultId: 2, comment: 'Nhận xét của sinh viên 2', score: 5 }))
  })
})
