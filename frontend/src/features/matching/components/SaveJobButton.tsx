import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { matchingApi } from '../api'
import { matchingKeys } from '../hooks'
export function SaveJobButton({ jobId }: { jobId: number }) {
  const client = useQueryClient()
  const query = useQuery({ queryKey: matchingKeys.saved, queryFn: ({ signal }) => matchingApi.savedIds(signal), staleTime: 60_000 })
  const saved = query.data?.includes(jobId) ?? false
  const mutation = useMutation({
    mutationKey: ['saved-jobs', jobId],
    mutationFn: async () => { if (saved) await matchingApi.unsave(jobId); else await matchingApi.save(jobId) },
    onSuccess: () => {
      client.setQueryData<number[]>(matchingKeys.saved, previous => saved ? previous?.filter(id => id !== jobId) ?? [] : [...new Set([...(previous ?? []), jobId])])
      void client.invalidateQueries({ queryKey: ['saved-jobs'] })
      void client.invalidateQueries({ queryKey: ['student-jobs', true] })
    },
  })
  return <div className="match-save"><Button variant="secondary" size="sm" pending={query.isPending || mutation.isPending} disabled={query.isError} aria-label={saved ? 'Bỏ lưu việc làm' : 'Lưu việc làm'} aria-pressed={saved} onClick={() => mutation.mutate()}><Bookmark size={17} fill={saved ? 'currentColor' : 'none'} /><span>{saved ? 'Đã lưu' : 'Lưu tin'}</span></Button>
    {query.isError && <button className="match-text-button" onClick={() => void query.refetch()}>Tải lại trạng thái lưu</button>}
    {mutation.error && <span role="alert" className="match-inline-error">{mutation.error.message}</span>}
  </div>
}
