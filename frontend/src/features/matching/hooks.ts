import { useQuery } from '@tanstack/react-query'
import { matchingApi } from './api'
export const matchingKeys = {
  jobs: (page: number) => ['matching', 'jobs', page] as const,
  candidates: (jobId: number | null, page: number) => ['matching', 'candidates', jobId, page] as const,
  saved: ['saved-jobs', 'ids'] as const,
}
export const useRecommendedJobs = (page: number) => useQuery({ queryKey: matchingKeys.jobs(page), queryFn: ({ signal }) => matchingApi.jobs(page, signal), staleTime: 60_000 })
export const useCandidates = (jobId: number | null, page: number, enabled: boolean) => useQuery({
  queryKey: matchingKeys.candidates(jobId, page), queryFn: ({ signal }) => matchingApi.candidates(jobId!, page, signal),
  enabled: jobId !== null && enabled, staleTime: 60_000,
})
export const useJob = (id: number | null) => useQuery({
  queryKey: ['jobs', 'detail', id], queryFn: ({ signal }) => matchingApi.job(id!, signal), enabled: id !== null, staleTime: 60_000,
})
export const useMajor = (id: number) => useQuery({ queryKey: ['catalog', 'major', id], queryFn: ({ signal }) => matchingApi.major(id, signal), staleTime: 300_000 })
export const usePublicCompany = (id: number) => useQuery({ queryKey: ['companies', 'public', id], queryFn: ({ signal }) => matchingApi.company(id, signal), staleTime: 300_000 })
