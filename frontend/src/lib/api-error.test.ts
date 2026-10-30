import { describe, expect, it } from 'vitest'
import { AxiosError, AxiosHeaders } from 'axios'
import { toApiError } from './api-error'

function error(status: number, data: unknown) {
  const config = { headers: new AxiosHeaders() }
  return new AxiosError('Failed', 'ERR_BAD_RESPONSE', config, undefined, { config, data, status, statusText: '', headers: {} })
}
describe('API error normalization', () => {
  it('keeps backend business codes and messages', () => {
    expect(toApiError(error(409, { error: { code: 'DUPLICATE_APPLICATION', message: 'Bạn đã ứng tuyển.' } })))
      .toMatchObject({ code: 'DUPLICATE_APPLICATION', status: 409, message: 'Bạn đã ứng tuyển.' })
  })
  it('maps FastAPI 422 locations to field errors', () => {
    expect(toApiError(error(422, { detail: [{ loc: ['body', 'email'], msg: 'Email không hợp lệ' }] })))
      .toMatchObject({ code: 'VALIDATION_ERROR', fields: { email: 'Email không hợp lệ' } })
  })
  it('does not display server traces or arbitrary response objects', () => {
    const normalized = toApiError(error(500, { traceback: 'secret=private' }))
    expect(normalized.message).not.toContain('secret')
  })
})
