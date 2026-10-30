/** Kiểu phân trang chung của mọi API danh sách (khớp schema Page[T] của backend). */
export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface PageQuery {
  page?: number
  size?: number
}

export type Role = 'STUDENT' | 'COMPANY' | 'ADMIN'
