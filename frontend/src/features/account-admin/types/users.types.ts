export type UserRole = 'STUDENT' | 'COMPANY' | 'ADMIN'
export type UserStatus =
  | 'PENDING_ACTIVATION'
  | 'PENDING_APPROVAL'
  | 'ACTIVE'
  | 'LOCKED'

export interface AdminProfileRead {
  id: number
  full_name: string
  faculty_id?: number | null
  position?: string | null
  phone?: string | null
}

export interface UserRead {
  id: number
  email: string
  role: UserRole
  status: UserStatus
  locked_reason?: string | null
  last_login_at?: string | null
  created_at: string
  updated_at: string
  admin?: AdminProfileRead | null
}

export interface AdminCreate {
  email: string
  password: string
  full_name: string
  faculty_id?: number | null
  position?: string | null
  phone?: string | null
}

export interface LockUserRequest {
  reason: string
}
