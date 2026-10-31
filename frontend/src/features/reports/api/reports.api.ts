import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type { Report, ReportCreate, ReportHandle, ReportStatus, ReportTargetType } from '../types/reports.types'

export const reportsApi = {
  create: async (data: ReportCreate): Promise<Report> =>
    (await http.post<Report>('/reports', data)).data,

  list: async (params?: {
    page?: number
    size?: number
    status?: ReportStatus
    target_type?: ReportTargetType
  }): Promise<Page<Report>> =>
    (
      await http.get<Page<Report>>('/reports', {
        params: {
          page: params?.page ?? 1,
          size: params?.size ?? 10,
          status: params?.status,
          target_type: params?.target_type,
        },
      })
    ).data,

  get: async (id: number): Promise<Report> =>
    (await http.get<Report>(`/reports/${id}`)).data,

  handle: async (id: number, data: ReportHandle): Promise<Report> =>
    (await http.post<Report>(`/reports/${id}/handle`, data)).data,
}
