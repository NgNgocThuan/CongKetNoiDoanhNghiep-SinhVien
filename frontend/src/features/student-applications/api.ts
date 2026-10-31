import { http } from '@/lib/http'
import type { Page } from '@/types/api'
import type { Application, ApplicationDetail } from './types'
export const applicationsApi = {
 list: async (page: number, status: string, signal?: AbortSignal) => (await http.get<Page<Application>>('/applications/me', {params:{page, size:12, status:status || undefined}, signal})).data,
 detail: async (id: number, signal?: AbortSignal) => (await http.get<ApplicationDetail>('/applications/' + id,{signal})).data,
 apply: async (data: {job_id: number; cv_id: number; cover_letter?: string; invitation_id?: number}) => (await http.post<ApplicationDetail>('/applications', data)).data,
 withdraw: async (id: number) => (await http.post<ApplicationDetail>('/applications/' + id + '/withdraw')).data,
}

