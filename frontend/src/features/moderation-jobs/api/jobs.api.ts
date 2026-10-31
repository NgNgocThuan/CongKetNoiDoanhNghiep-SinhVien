import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type {
  AdminJobDetailRead,
  AdminJobRead,
  JobCloseRequest,
  JobRejectRequest,
  JobStatus,
} from '../types/jobs.types'

export const jobsApi = {
  list: async (params?: {
    page?: number
    size?: number
    status?: JobStatus
    company_id?: number
    term_id?: number
    q?: string
  }): Promise<Page<AdminJobRead>> =>
    (
      await http.get<Page<AdminJobRead>>('/admin/jobs', {
        params: {
          page: params?.page ?? 1,
          size: params?.size ?? 10,
          status: params?.status,
          company_id: params?.company_id,
          term_id: params?.term_id,
          q: params?.q?.trim() || undefined,
        },
      })
    ).data,

  get: async (id: number): Promise<AdminJobDetailRead> =>
    (await http.get<AdminJobDetailRead>(`/admin/jobs/${id}`)).data,

  approve: async (id: number): Promise<AdminJobDetailRead> =>
    (await http.post<AdminJobDetailRead>(`/admin/jobs/${id}/approve`)).data,

  reject: async (id: number, data: JobRejectRequest): Promise<AdminJobDetailRead> =>
    (await http.post<AdminJobDetailRead>(`/admin/jobs/${id}/reject`, data)).data,

  close: async (id: number, data: JobCloseRequest): Promise<AdminJobDetailRead> =>
    (await http.post<AdminJobDetailRead>(`/admin/jobs/${id}/close`, data)).data,
}
