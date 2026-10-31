import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bookmark } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { jobsApi } from '../api'
export function SaveJobButton({ jobId, saved }: { jobId: number; saved?: boolean }) {
  const client = useQueryClient()
  const savedIds = useQuery({
    queryKey: ['saved-jobs', 'student-ids'],
    queryFn: ({ signal }) => jobsApi.savedIds(signal),
    enabled: saved === undefined,
  })
  const isSaved = saved ?? savedIds.data?.has(jobId) ?? false
  const mutation = useMutation({
    mutationFn: async () => {
      if (isSaved) await jobsApi.unsave(jobId)
      else await jobsApi.save(jobId)
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ['saved-jobs'] }),
  })
  return (
    <div>
      <Button
        variant="secondary"
        aria-label={isSaved ? 'Bỏ lưu việc làm' : 'Lưu việc làm'}
        disabled={saved === undefined && savedIds.isPending}
        pending={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        <Bookmark size={16} fill={isSaved ? 'currentColor' : 'none'} />
        {isSaved ? 'Bỏ lưu' : 'Lưu tin'}
      </Button>
      {mutation.error && (
        <p role="alert" className="field__error">
          {mutation.error.message}
        </p>
      )}
      {mutation.isSuccess && !isSaved && (
        <span role="status" className="student-tag">
          Đã lưu
        </span>
      )}
    </div>
  )
}
