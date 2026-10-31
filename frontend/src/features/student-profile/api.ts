import { http } from '@/lib/http'
import type { FullProfile } from './types'
export const profileApi = {
  get: async (signal?: AbortSignal) =>
    (await http.get<FullProfile>('/students/me', { signal })).data,
  update: async (data: Record<string, unknown>) => {
    await http.put('/students/me/profile', data)
  },
  save: async (group: string, data: Record<string, unknown>, id?: number) => {
    if (id) await http.put('/students/me/' + group + '/' + id, data)
    else await http.post('/students/me/' + group, data)
  },
  remove: async (group: string, id: number) => {
    await http.delete('/students/me/' + group + '/' + id)
  },
}
