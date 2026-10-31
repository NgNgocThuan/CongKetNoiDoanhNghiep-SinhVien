import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type {
  EmailLogRead,
  EmailStatus,
  RetryEmailsResponse,
} from '../types/email-logs.types'

export const emailLogsApi = {
  list: async (params?: {
    page?: number
    size?: number
    status?: EmailStatus
    type?: string
  }): Promise<Page<EmailLogRead>> =>
    (
      await http.get<Page<EmailLogRead>>('/admin/users/email-logs', {
        params: {
          page: params?.page ?? 1,
          size: params?.size ?? 10,
          status: params?.status,
          type: params?.type?.trim() || undefined,
        },
      })
    ).data,

  retry: async (): Promise<RetryEmailsResponse> =>
    (await http.post<RetryEmailsResponse>('/admin/users/email-logs/retry')).data,
}
