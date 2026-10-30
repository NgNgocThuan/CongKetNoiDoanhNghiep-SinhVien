import { describe, expect, it } from 'vitest'
import { computedAtLabel, positiveId, salaryLabel, scoreLabel } from './format'
describe('matching API value boundaries', () => {
  it('keeps zero salary and decimal matching scores distinct from absent data', () => {
    expect(salaryLabel({ salary_min: 0, salary_max: null, is_salary_negotiable: false })).toBe('Từ 0 đ')
    expect(scoreLabel('0.00')).toBe('0%')
    expect(scoreLabel(null)).toBe('—')
    expect(scoreLabel('86.50')).toBe('86,5%')
  })
  it('rejects invalid route IDs before making an API call', () => {
    for (const value of ['-1', '1.5', '1e2', 'Infinity', '9007199254740992', '', null]) expect(positiveId(value)).toBeNull()
    expect(positiveId('12')).toBe(12)
  })
  it('interprets backend naive timestamps as UTC without shifting explicit offsets twice', () => {
    expect(computedAtLabel('2026-10-30T08:00:00')).toBe(computedAtLabel('2026-10-30T08:00:00Z'))
    expect(computedAtLabel('2026-10-30T15:00:00+07:00')).toBe(computedAtLabel('2026-10-30T08:00:00Z'))
    expect(computedAtLabel('invalid')).toBe('Chưa có thông tin')
  })
})
