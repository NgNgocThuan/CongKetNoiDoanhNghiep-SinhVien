import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2 } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { matchingApi } from '../api'
import { ApiError } from '@/lib/api-error'
export function InviteDialog({ jobId, jobTitle, studentId, fullName, onClose, onSent }: { jobId: number; jobTitle: string; studentId: number; fullName: string; onClose: () => void; onSent: () => void }) {
  const [message, setMessage] = useState('')
  const client = useQueryClient()
  const mutation = useMutation({ mutationFn: matchingApi.invite, onSuccess: () => { onSent(); void client.invalidateQueries({ queryKey: ['invitations'] }) } })
  const duplicate = mutation.error instanceof ApiError && mutation.error.code === 'DUPLICATE_INVITATION'
  return <Dialog open onOpenChange={open => { if (!open && !mutation.isPending) onClose() }} title="Mời ứng tuyển" description={'Gửi lời mời đến ' + fullName}>
    {mutation.isSuccess ? <div className="state" role="status"><CheckCircle2 size={34} /><h3>Đã gửi lời mời</h3><p>Lời mời ứng tuyển đã được gửi đến {fullName}.</p><Button onClick={onClose}>Hoàn tất</Button></div> :
      <form className="match-form" onSubmit={event => { event.preventDefault(); if (!mutation.isPending) mutation.mutate({ job_id: jobId, student_id: studentId, ...(message.trim() ? { message: message.trim() } : {}) }) }}>
        <div className="match-invite-context"><span>Tin tuyển dụng</span><strong>{jobTitle}</strong><span>Ứng viên</span><strong>{fullName}</strong></div>
        <label>Lời nhắn <span className="muted">(không bắt buộc)</span><textarea rows={5} maxLength={500} value={message} onChange={event => setMessage(event.target.value)} disabled={mutation.isPending} placeholder="Giới thiệu cơ hội và gửi lời mời đến ứng viên…" /><span className="match-char-count">{message.length}/500 ký tự</span></label>
        {mutation.error && <p role="alert" className="match-inline-error">{mutation.error.message}</p>}
        <div className="match-form__actions"><Button variant="secondary" disabled={mutation.isPending} onClick={onClose}>Hủy</Button><Button type="submit" pending={mutation.isPending} disabled={duplicate}>Gửi lời mời</Button></div>
      </form>}
  </Dialog>
}
