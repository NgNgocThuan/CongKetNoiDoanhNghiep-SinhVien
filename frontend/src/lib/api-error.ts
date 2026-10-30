import axios from 'axios'

export class ApiError extends Error {
  readonly status: number | null
  readonly code: string
  readonly fields: Record<string, string>
  constructor(message: string, status: number | null = null, code = 'UNKNOWN', fields: Record<string, string> = {}) {
    super(message); this.name = 'ApiError'; this.status = status; this.code = code; this.fields = fields
  }
}
function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (axios.isCancel(error)) return new ApiError('Yêu cầu đã được hủy.', null, 'REQUEST_CANCELLED')
  if (!axios.isAxiosError(error)) return new ApiError('Đã có lỗi xảy ra. Vui lòng thử lại.')
  const status = error.response?.status ?? null
  const body: unknown = error.response?.data
  if (record(body) && record(body.error) && typeof body.error.message === 'string') {
    return new ApiError(body.error.message, status, typeof body.error.code === 'string' ? body.error.code : 'API_ERROR')
  }
  if (record(body) && Array.isArray(body.detail)) {
    const fields: Record<string, string> = {}
    for (const issue of body.detail) {
      if (record(issue) && Array.isArray(issue.loc) && typeof issue.msg === 'string') {
        fields[issue.loc.filter(part => part !== 'body' && part !== 'query').join('.')] = issue.msg
      }
    }
    return new ApiError('Vui lòng kiểm tra lại thông tin đã nhập.', status, 'VALIDATION_ERROR', fields)
  }
  if (record(body) && typeof body.detail === 'string') return new ApiError(body.detail, status, 'HTTP_ERROR')
  if (!status) return new ApiError('Không thể kết nối máy chủ. Vui lòng kiểm tra kết nối và thử lại.', null, 'NETWORK_ERROR')
  return new ApiError(status >= 500 ? 'Máy chủ đang gặp sự cố. Vui lòng thử lại sau.' : 'Không thể hoàn tất yêu cầu.', status, 'HTTP_ERROR')
}
