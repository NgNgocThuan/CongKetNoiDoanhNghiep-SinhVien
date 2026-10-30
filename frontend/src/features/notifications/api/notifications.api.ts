import { http } from '@/lib/http'
import type { Page } from '@/types/api'
export interface Notification { id: number; title: string; content: string | null; is_read: boolean; created_at: string; ref_type: string | null; ref_id: number | null }
export const notificationsApi = {
  count: async () => (await http.get<{ unread_count: number }>('/notifications/unread-count')).data,
  list: async (page: number, signal?: AbortSignal) => (await http.get<Page<Notification>>('/notifications', { params: { page, size: 10 }, signal })).data,
  read: (id: number) => http.post('/notifications/' + id + '/read'),
  readAll: () => http.post('/notifications/read-all'),
}
