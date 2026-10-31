import { describe, expect, it } from 'vitest'
import { formSchema } from './workspace-form'

describe('business forms', () => {
  it('rejects blank reasons and out-of-range scores while accepting zero', () => {
    const schema = formSchema([
      { name: 'reason', label: 'Lý do', required: true },
      { name: 'score', label: 'Điểm', type: 'number', min: 0, max: 10 },
    ])
    expect(schema.safeParse({ reason: '   ', score: '0' }).success).toBe(false)
    expect(schema.safeParse({ reason: 'Nhận xét', score: '11' }).success).toBe(
      false,
    )
    expect(schema.safeParse({ reason: 'Nhận xét', score: '0' }).success).toBe(
      true,
    )
  })
  it('enforces the backend minimum password length before creating an administrator', () => {
    const schema = formSchema([
      {
        name: 'password',
        label: 'Mật khẩu',
        type: 'password',
        required: true,
        minLength: 8,
      },
    ])
    expect(schema.safeParse({ password: '1234567' }).success).toBe(false)
    expect(schema.safeParse({ password: 'Abcd1234' }).success).toBe(true)
  })
})
