import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type { Job, JobFilters, SavedJob, PublicCompany, Brief } from './types'
export const jobsApi = {
 search: async (params: JobFilters, signal?: AbortSignal) => (await http.get<Page<Job>>('/jobs', { params, signal })).data,
 detail: async (id: number, signal?: AbortSignal) => (await http.get<Job>('/jobs/' + id, { signal })).data,
 company: async (id: number, signal?: AbortSignal) => (await http.get<PublicCompany>('/companies/' + id, { signal })).data,
 saved: async (page: number, signal?: AbortSignal) => (await http.get<Page<SavedJob>>('/saved-jobs', { params: {page, size: 12}, signal })).data,
 save: async (id: number) => (await http.post<SavedJob>('/saved-jobs/' + id)).data,
 unsave: async (id: number) => { await http.delete('/saved-jobs/' + id) },
 catalog: async (name: string, q = '', page = 1) => (await http.get<Page<Brief>>('/catalog/' + name, { params: {q, page, size: 100} })).data,
}

