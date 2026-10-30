import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2 } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { ErrorState, LoadingState } from '@/components/common/States'
import { matchingApi } from '../api'
import { ApiError } from '@/lib/api-error'
export function ApplyDialog({ jobId, title, onClose }: { jobId: number; title: string; onClose: () => void }) {
  const [selectedCV, setSelectedCV] = useState<number | null>(null), [letter, setLetter] = useState('')
  const client = useQueryClient()
  const cvs = useQuery({ queryKey: ['cvs', 'me'], queryFn: ({ signal }) => matchingApi.cvs(signal) })
  const mutation = useMutation({ mutationFn: matchingApi.apply, onSuccess: () => { void client.invalidateQueries({ queryKey: ['applications'] }) } })
  const cvId = selectedCV ?? cvs.data?.find(cv => cv.is_default)?.id ?? cvs.data?.[0]?.id
  const duplicate = mutation.error instanceof ApiError && mutation.error.code === 'DUPLICATE_APPLICATION'
  return <Dialog open onOpenChange={open => { if (!open && !mutation.isPending) onClose() }} title="Ứng tuyển" description={title}>
    {mutation.isSuccess ? <div className="state" role="status"><CheckCircle2 size={34} /><h3>Đã gửi đơn ứng tuyển</h3><p>Doanh nghiệp sẽ nhận được hồ sơ bạn đã chọn.</p><Button onClick={onClose}>Hoàn tất</Button></div> :
      cvs.isPending ? <LoadingState label="Đang tải CV của bạn…" /> : cvs.isError ? <ErrorState message={cvs.error.message} onRetry={() => void cvs.refetch()} /> : !cvs.data.length ? <div className="state"><h3>Bạn chưa có CV</h3><p>Cần chuẩn bị CV trước khi ứng tuyển.</p><Link className="button button--primary button--md" to="/student/cvs">Đến CV của tôi</Link></div> :
        <form className="match-form" onSubmit={event => { event.preventDefault(); if (cvId && !mutation.isPending) mutation.mutate({ job_id: jobId, cv_id: cvId, ...(letter.trim() ? { cover_letter: letter.trim() } : {}) }) }}>
          <label>CV ứng tuyển<select required value={cvId ?? ''} onChange={event => setSelectedCV(Number(event.target.value))} disabled={mutation.isPending}>{cvs.data.map(cv => <option key={cv.id} value={cv.id}>{cv.title}{cv.is_default ? ' — Mặc định' : ''}</option>)}</select></label>
          <label>Thư giới thiệu <span className="muted">(không bắt buộc)</span><textarea value={letter} maxLength={10000} rows={5} onChange={event => setLetter(event.target.value)} disabled={mutation.isPending} placeholder="Giới thiệu ngắn về bạn và lý do ứng tuyển…" /></label>
          {mutation.error && <p className="match-inline-error" role="alert">{mutation.error.message}</p>}
          <div className="match-form__actions"><Button variant="secondary" onClick={onClose} disabled={mutation.isPending}>Hủy</Button><Button type="submit" pending={mutation.isPending} disabled={!cvId || duplicate}>Gửi đơn ứng tuyển</Button></div>
        </form>}
  </Dialog>
}
