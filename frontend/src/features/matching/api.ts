import { http } from '@/lib/http'
import type { CandidateRecommendation, CVChoice, Job, JobDetail, JobRecommendation, Page, SavedJob } from './types'
export const matchingApi = {
  jobs: async (page: number, signal?: AbortSignal) => (await http.get<Page<JobRecommendation>>('/matching/jobs/recommended', { params: { page, size: 6 }, signal, timeout: 120_000 })).data,
  candidates: async (jobId: number, page: number, signal?: AbortSignal) => (await http.get<Page<CandidateRecommendation>>('/matching/jobs/' + jobId + '/candidates', { params: { page, size: 6 }, signal, timeout: 120_000 })).data,
  companyJobs: async (page: number, signal?: AbortSignal) => (await http.get<Page<Job>>('/jobs/me', { params: { page, size: 20 }, signal })).data,
  job: async (id: number, signal?: AbortSignal) => (await http.get<JobDetail>('/jobs/' + id, { signal })).data,
  company: async (id: number, signal?: AbortSignal) => (await http.get<{ id: number; name: string; logo_url: string | null }>('/companies/' + id, { signal })).data,
  major: async (id: number, signal?: AbortSignal) => (await http.get<{ id: number; name: string }>('/catalog/majors/' + id, { signal })).data,
  cvs: async (signal?: AbortSignal) => (await http.get<CVChoice[]>('/cvs/me', { signal })).data,
  savedIds: async (signal?: AbortSignal) => {
    const ids: number[] = []
    let page = 1
    while (true) {
      const { data } = await http.get<Page<SavedJob>>('/saved-jobs', { params: { page, size: 100 }, signal })
      ids.push(...data.items.map(item => item.job.id))
      if (page >= data.pages || !data.items.length) return ids
      page++
    }
  },
  save: async (jobId: number) => { await http.post('/saved-jobs/' + jobId) },
  unsave: async (jobId: number) => { await http.delete('/saved-jobs/' + jobId) },
  apply: async (data: { job_id: number; cv_id: number; cover_letter?: string }) => (await http.post<{ id: number }>('/applications', data)).data,
  invite: async (data: { job_id: number; student_id: number; message?: string }) => (await http.post<{ id: number }>('/invitations', data)).data,
}
