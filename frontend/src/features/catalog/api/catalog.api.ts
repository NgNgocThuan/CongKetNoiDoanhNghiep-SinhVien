import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type { Faculty } from '../types/catalog.types'

export const catalogApi = {
  faculties: async (params: { page: number; size: number; q: string }, signal?: AbortSignal): Promise<Page<Faculty>> =>
    (await http.get<Page<Faculty>>('/catalog/faculties', { params, signal })).data,
}
