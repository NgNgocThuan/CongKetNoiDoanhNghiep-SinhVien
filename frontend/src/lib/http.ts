/**
 * HTTP client chung. Gắn access token, chuẩn hóa lỗi backend.
 * TẠM: Quang (xác thực) sẽ thay phần refresh token; các feature chỉ cần import `http` và `getErrorMessage`.
 */
import axios, { AxiosError } from 'axios'
import { clearToken, getToken } from '@/lib/token'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

export const http = axios.create({ baseURL: API_BASE_URL })

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** Sự kiện phát ra khi phiên hết hạn / token không hợp lệ để AuthProvider đưa về trang đăng nhập. */
export const SESSION_EXPIRED_EVENT = 'session-expired'

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearToken()
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    }
    return Promise.reject(error)
  },
)

interface BusinessError {
  error?: { code?: string; message?: string }
}
interface ValidationError {
  detail?: string | { loc?: (string | number)[]; msg?: string }[]
}

/** Đổi lỗi bất kỳ thành thông báo tiếng Việt: lỗi nghiệp vụ {error:{message}}, lỗi 422 {detail:[...]}, lỗi mạng. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return 'Không kết nối được máy chủ. Vui lòng kiểm tra mạng hoặc thử lại sau.'
    const data = error.response.data as BusinessError & ValidationError
    if (data?.error?.message) return data.error.message
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      return data.detail
        .map((d) => {
          const field = d.loc?.filter((p) => p !== 'body').join('.')
          return field ? `${field}: ${d.msg}` : (d.msg ?? '')
        })
        .join('; ')
    }
    if (typeof data?.detail === 'string') return data.detail
    if (error.response.status === 403) return 'Bạn không có quyền thực hiện thao tác này.'
    if (error.response.status === 404) return 'Không tìm thấy dữ liệu.'
    return `Có lỗi xảy ra (mã ${error.response.status}).`
  }
  return error instanceof Error ? error.message : 'Có lỗi không xác định.'
}

export function getErrorStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined
}
