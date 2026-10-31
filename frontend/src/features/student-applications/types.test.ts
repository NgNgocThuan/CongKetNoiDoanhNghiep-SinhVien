import { describe, it, expect } from 'vitest'
import { canWithdraw } from './types'
describe('withdraw availability', () => {
  it.each(['OFFER', 'HIRED', 'REJECTED', 'WITHDRAWN'] as const)(
    'blocks terminal state %s',
    (status) => expect(canWithdraw(status)).toBe(false),
  )
  it.each(['APPLIED', 'SCREENING', 'SHORTLISTED', 'INTERVIEW'] as const)(
    'allows active state %s',
    (status) => expect(canWithdraw(status)).toBe(true),
  )
})
