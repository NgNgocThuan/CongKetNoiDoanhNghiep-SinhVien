import { useState } from 'react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { http } from '@/lib/http'
import { Feedback } from './StudentUI'
import { useStudentAction } from '../useStudentAction'

/** Student-side adapter until Quang's shared ReportDialog is merged into main. */
export function ReportJobDialog({ jobId, title }: { jobId: number; title: string }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button variant="ghost" onClick={() => setOpen(true)}>
        Báo cáo tin
      </Button>
      <Dialog open={open} onOpenChange={setOpen} title="Báo cáo tin tuyển dụng" description={title}>
        {open && <ReportForm jobId={jobId} />}
      </Dialog>
    </>
  )
}
function ReportForm({ jobId }: { jobId: number }) {
  const [reason, setReason] = useState('')
  const action = useStudentAction(['student-reports'])
  return (
    <form
      className="student-form"
      onSubmit={async (e) => {
        e.preventDefault()
        if (!reason.trim()) return
        await action.run(
          () =>
            http.post('/reports', { target_type: 'JOB', target_id: jobId, reason: reason.trim() }),
          'Đã gửi báo cáo đến nhà trường.',
        )
      }}
    >
      <label>
        Lý do báo cáo
        <textarea
          required
          maxLength={500}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Mô tả nội dung cần nhà trường xem xét…"
        />
      </label>
      <Feedback {...action} />
      <Button type="submit" pending={action.pending} disabled={!!action.success}>
        Gửi báo cáo
      </Button>
    </form>
  )
}
