import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type {
  AdminCompanyDetailRead,
  AdminCompanyRead,
  CompanyRejectRequest,
  VerificationStatus,
} from '../types/companies.types'

export const companiesApi = {
  list: async (params?: {
    page?: number
    size?: number
    verification_status?: VerificationStatus
    q?: string
  }): Promise<Page<AdminCompanyRead>> =>
    (
      await http.get<Page<AdminCompanyRead>>('/admin/companies', {
        params: {
          page: params?.page ?? 1,
          size: params?.size ?? 10,
          verification_status: params?.verification_status,
          q: params?.q?.trim() || undefined,
        },
      })
    ).data,

  get: async (id: number): Promise<AdminCompanyDetailRead> =>
    (await http.get<AdminCompanyDetailRead>(`/admin/companies/${id}`)).data,

  approve: async (id: number): Promise<AdminCompanyDetailRead> =>
    (await http.post<AdminCompanyDetailRead>(`/admin/companies/${id}/approve`)).data,

  reject: async (id: number, data: CompanyRejectRequest): Promise<AdminCompanyDetailRead> =>
    (await http.post<AdminCompanyDetailRead>(`/admin/companies/${id}/reject`, data)).data,
}
