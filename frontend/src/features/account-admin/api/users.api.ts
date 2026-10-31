import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type {
  AdminCreate,
  LockUserRequest,
  UserRead,
  UserRole,
  UserStatus,
} from '../types/users.types'

export const usersApi = {
  list: async (params?: {
    page?: number
    size?: number
    role?: UserRole
    status?: UserStatus
    q?: string
  }): Promise<Page<UserRead>> =>
    (
      await http.get<Page<UserRead>>('/admin/users', {
        params: {
          page: params?.page ?? 1,
          size: params?.size ?? 10,
          role: params?.role,
          status: params?.status,
          q: params?.q?.trim() || undefined,
        },
      })
    ).data,

  get: async (id: number): Promise<UserRead> =>
    (await http.get<UserRead>(`/admin/users/${id}`)).data,

  lock: async (id: number, data: LockUserRequest): Promise<UserRead> =>
    (await http.post<UserRead>(`/admin/users/${id}/lock`, data)).data,

  unlock: async (id: number): Promise<UserRead> =>
    (await http.post<UserRead>(`/admin/users/${id}/unlock`)).data,

  createAdmin: async (data: AdminCreate): Promise<UserRead> =>
    (await http.post<UserRead>('/admin/users/admins', data)).data,
}
