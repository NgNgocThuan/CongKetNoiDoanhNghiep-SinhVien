import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios'
import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime, formatScore } from './format'
import { getErrorMessage, getErrorStatus } from './http'
import { getRoleFromToken } from './token'

function axiosError(status: number, data: unknown): AxiosError {
  const response = { status, data, statusText: '', headers: {}, config: { headers: new AxiosHeaders() } } as AxiosResponse
  return new AxiosError('lỗi', String(status), undefined, undefined, response)
}

describe('getErrorMessage', () => {
  it('lấy thông báo lỗi nghiệp vụ {error:{message}} của backend', () => {
    expect(getErrorMessage(axiosError(409, { error: { code: 'CONFLICT', message: 'Mã khoa đã tồn tại' } }))).toBe(
      'Mã khoa đã tồn tại',
    )
  })

  it('ghép lỗi validate 422 theo từng trường', () => {
    const err = axiosError(422, { detail: [{ loc: ['body', 'gpa'], msg: 'phải nhỏ hơn hoặc bằng 4' }] })
    expect(getErrorMessage(err)).toBe('gpa: phải nhỏ hơn hoặc bằng 4')
  })

  it('lỗi 403/404 không có nội dung thì có thông báo mặc định', () => {
    expect(getErrorMessage(axiosError(403, {}))).toMatch(/không có quyền/i)
    expect(getErrorMessage(axiosError(404, {}))).toMatch(/không tìm thấy/i)
  })

  it('lỗi mạng (không có phản hồi) báo không kết nối được máy chủ', () => {
    expect(getErrorMessage(new AxiosError('Network Error'))).toMatch(/không kết nối/i)
  })

  it('lỗi thường thì trả về nội dung của nó', () => {
    expect(getErrorMessage(new Error('hỏng'))).toBe('hỏng')
  })
})

describe('getErrorStatus', () => {
  it('trả mã HTTP, hoặc undefined nếu không phải lỗi HTTP', () => {
    expect(getErrorStatus(axiosError(404, {}))).toBe(404)
    expect(getErrorStatus(new Error('x'))).toBeUndefined()
  })
})

describe('format', () => {
  it('ngày hiển thị dd/MM/yyyy, rỗng thì là dấu gạch', () => {
    expect(formatDate('2025-09-01')).toBe('01/09/2025')
    expect(formatDate(null)).toBe('—')
    expect(formatDate(undefined)).toBe('—')
    expect(formatDateTime('2025-09-01T08:05:00')).toBe('01/09/2025 08:05')
  })

  it('điểm null giữ dấu gạch, không đổi thành 0', () => {
    expect(formatScore(null)).toBe('—')
    expect(formatScore('8.50')).toBe('8.5')
    expect(formatScore('9.00')).toBe('9')
    expect(formatScore('0.00')).toBe('0')
    expect(formatScore(7.25)).toBe('7.25')
  })
})

describe('getRoleFromToken', () => {
  const make = (payload: object) => `x.${btoa(JSON.stringify(payload))}.y`

  it('đọc role từ payload JWT', () => {
    expect(getRoleFromToken(make({ role: 'ADMIN' }))).toBe('ADMIN')
  })

  it('token rỗng hoặc hỏng thì không có role', () => {
    expect(getRoleFromToken(null)).toBeNull()
    expect(getRoleFromToken('khong-phai-jwt')).toBeNull()
  })
})
