export interface Page<T> { items: T[]; total: number; page: number; size: number; pages: number }
export interface PageParams { page?: number; size?: number }
export interface MessageResponse { message: string }
