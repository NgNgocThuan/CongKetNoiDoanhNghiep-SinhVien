import { describe, expect, it } from 'vitest'
import { hasReviewContent, isResultLocked, isTermEditable, nextStatus, TERM_STEPS } from './rules'

describe('nextStatus', () => {
  it('chỉ tiến đúng một bước theo luồng DRAFT→OPEN→ONGOING→CLOSED', () => {
    expect(nextStatus('DRAFT')).toBe('OPEN')
    expect(nextStatus('OPEN')).toBe('ONGOING')
    expect(nextStatus('ONGOING')).toBe('CLOSED')
  })

  it('đợt đã đóng không còn bước tiếp', () => {
    expect(nextStatus('CLOSED')).toBeNull()
  })

  it('luồng đủ bốn bước đúng thứ tự', () => {
    expect(TERM_STEPS).toEqual(['DRAFT', 'OPEN', 'ONGOING', 'CLOSED'])
  })
})

describe('isTermEditable', () => {
  it('đợt đã đóng thì khóa chỉnh sửa, các đợt khác thì mở', () => {
    expect(isTermEditable('CLOSED')).toBe(false)
    expect(isTermEditable('DRAFT')).toBe(true)
    expect(isTermEditable('OPEN')).toBe(true)
    expect(isTermEditable('ONGOING')).toBe(true)
  })
})

describe('isResultLocked', () => {
  it('chỉ kết quả đang chờ mới được sửa', () => {
    expect(isResultLocked({ result: 'PENDING' })).toBe(false)
    expect(isResultLocked({ result: 'PASSED' })).toBe(true)
    expect(isResultLocked({ result: 'FAILED' })).toBe(true)
  })
})

describe('hasReviewContent', () => {
  it('cần ít nhất nhận xét hoặc điểm', () => {
    expect(hasReviewContent('', null)).toBe(false)
    expect(hasReviewContent('   ', undefined)).toBe(false)
    expect(hasReviewContent('Tốt', null)).toBe(true)
    expect(hasReviewContent('', 0)).toBe(true) // điểm 0 vẫn là điểm hợp lệ
    expect(hasReviewContent(null, 8.5)).toBe(true)
  })
})
