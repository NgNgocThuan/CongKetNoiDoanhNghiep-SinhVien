import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { cvsApi } from '@/features/student-cvs/api'
import type { Job } from '@/features/student-jobs/types'
import {
  Feedback,
  QueryState,
} from '@/features/student-jobs/components/StudentUI'
import { applicationsApi } from '../api'
import type { ApplicationDetail } from '../types'
const schema = z.object({
  cv_id: z.string().min(1, 'Vui lòng chọn CV.'),
  cover_letter: z.string().max(10000, 'Thư giới thiệu tối đa 10.000 ký tự.'),
})
export interface ApplyDialogProps {
  open: boolean
  jobId: number
  invitationId?: number
  onClose: () => void
  onSuccess?: (application: ApplicationDetail) => void
}
export function ApplyDialog(props: ApplyDialogProps) {
  return (
    <Dialog
      open={props.open}
      onOpenChange={(open) => {
        if (!open) props.onClose()
      }}
      title="Nộp đơn ứng tuyển"
      description="Chọn CV và giới thiệu ngắn về bạn. Hồ sơ sẽ được lưu tại thời điểm nộp đơn."
    >
      {props.open && (
        <ApplyForm key={props.jobId + ':' + props.invitationId} {...props} />
      )}
    </Dialog>
  )
}
function ApplyForm({
  jobId,
  invitationId,
  onClose,
  onSuccess,
}: ApplyDialogProps) {
  const cvs = useQuery({
    queryKey: ['student-cvs'],
    queryFn: ({ signal }) => cvsApi.list(signal),
  })
  const client = useQueryClient()
  const job = client.getQueryData<Job>(['student-job', jobId])
  const action = useStudentAction([
    'student-applications',
    'student-invitations',
  ])
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    values: {
      cv_id: String(
        cvs.data?.find((cv) => cv.is_default)?.id || cvs.data?.[0]?.id || '',
      ),
      cover_letter: '',
    },
  })
  if (cvs.isPending || cvs.error) return <QueryState query={cvs} />
  if (!cvs.data?.length)
    return (
      <div className="student-stack">
        <p>Bạn chưa có CV online để ứng tuyển.</p>
        <Link to="/student/cvs" onClick={onClose}>
          Tạo CV online từ thông tin nhà trường
        </Link>
      </div>
    )
  return (
    <form
      className="student-form"
      onSubmit={form.handleSubmit(async (data) => {
        await action.run(async () => {
          const created = await applicationsApi.apply({
            job_id: jobId,
            cv_id: Number(data.cv_id),
            cover_letter: data.cover_letter || undefined,
            ...(invitationId ? { invitation_id: invitationId } : {}),
          })
          onSuccess?.(created)
          onClose()
        }, 'Đã nộp đơn ứng tuyển.')
      })}
    >
      <p>
        <strong>{job?.title || 'Vị trí tuyển dụng #' + jobId}</strong>
        <br />
        {job?.company.name}
      </p>
      <label>
        CV ứng tuyển
        <select {...form.register('cv_id')}>
          {cvs.data.map((cv) => (
            <option key={cv.id} value={cv.id}>
              {cv.title}
              {cv.is_default ? ' · Mặc định' : ''}
            </option>
          ))}
        </select>
      </label>
      <span className="field__error">
        {form.formState.errors.cv_id?.message}
      </span>
      <label>
        Thư giới thiệu (tùy chọn)
        <textarea
          rows={5}
          maxLength={10000}
          {...form.register('cover_letter')}
          placeholder="Giới thiệu kỹ năng và lý do bạn quan tâm vị trí này…"
        />
      </label>
      <span className="field__error">
        {form.formState.errors.cover_letter?.message}
      </span>
      {invitationId && (
        <p className="student-notice">
          Bạn đang ứng tuyển theo lời mời từ doanh nghiệp.
        </p>
      )}
      <Feedback {...action} />
      <div className="dialog__actions">
        <Button variant="secondary" disabled={action.pending} onClick={onClose}>
          Hủy
        </Button>
        <Button type="submit" pending={action.pending}>
          Gửi đơn ứng tuyển
        </Button>
      </div>
    </form>
  )
}
