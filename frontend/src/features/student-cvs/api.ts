import { http } from '@/lib/http'
import type { CV } from './types'
export const cvsApi = {
  upload: async (title: string, file: File) => {
    const body = new FormData()
    body.append('title', title)
    body.append('file', file)
    return (await http.post<CV>('/cvs/upload', body)).data
  },
  list: async (signal?: AbortSignal) =>
    (await http.get<CV[]>('/cvs/me', { signal })).data,
  create: async (data: {
    title: string
    content_json: Record<string, unknown>
  }) => (await http.post<CV>('/cvs/online', data)).data,
  update: async (
    id: number,
    data: { title: string; content_json?: Record<string, unknown> },
  ) => (await http.put<CV>('/cvs/' + id, data)).data,
  remove: async (id: number) => {
    await http.delete('/cvs/' + id)
  },
  default: async (id: number) =>
    (await http.post<CV>('/cvs/' + id + '/set-default')).data,
}
