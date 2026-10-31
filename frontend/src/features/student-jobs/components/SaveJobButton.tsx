import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Bookmark } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { jobsApi } from '../api'
export function SaveJobButton({jobId, saved = false}: {jobId: number; saved?: boolean}) {
 const client = useQueryClient()
 const mutation = useMutation({mutationFn: async () => { if (saved) await jobsApi.unsave(jobId); else await jobsApi.save(jobId) }, onSuccess: () => client.invalidateQueries({queryKey:['saved-jobs']})})
 return <div><Button variant="secondary" aria-label={saved ? 'Bỏ lưu việc làm' : 'Lưu việc làm'} pending={mutation.isPending} onClick={() => mutation.mutate()}><Bookmark size={16} fill={saved ? 'currentColor' : 'none'} />{saved ? 'Bỏ lưu' : 'Lưu tin'}</Button>{mutation.error && <p role="alert" className="field__error">{mutation.error.message}</p>}{mutation.isSuccess && !saved && <span role="status" className="student-tag">Đã lưu</span>}</div>
}

