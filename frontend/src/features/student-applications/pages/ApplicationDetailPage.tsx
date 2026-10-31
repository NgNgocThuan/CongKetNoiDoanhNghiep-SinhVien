import { dateText } from '@/features/student-jobs/format'
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { StudentPage, QueryState, Status } from '@/features/student-jobs/components/StudentUI'
import { applicationsApi } from '../api'
import { canWithdraw } from '../types'
export default function ApplicationDetailPage() {
  const { id } = useParams(),
    appId = Number(id),
    client = useQueryClient(),
    [confirm, setConfirm] = useState(false)
  const query = useQuery({
    queryKey: ['student-applications', 'detail', appId],
    queryFn: ({ signal }) => applicationsApi.detail(appId, signal),
  })
  const app = query.data
  return (
    <StudentPage title="Tiến trình ứng tuyển" description={app?.job.title}>
      <Link to="/student/applications">← Đơn ứng tuyển của tôi</Link>
      <QueryState query={query} />
      {app && (
        <div className="student-split">
          <article className="student-panel">
            <h2>{app.job.title}</h2>
            <p>{app.job.company.name}</p>
            <Status value={app.current_status} />
            <h3 style={{ marginTop: 24 }}>Lịch sử trạng thái</h3>
            <ol className="student-timeline">
              {app.status_logs.map((log) => (
                <li key={log.id}>
                  <Status value={log.new_status} />
                  <time>{dateText(log.changed_at)}</time>
                  {log.note && <p className="student-rich">{log.note}</p>}
                </li>
              ))}
            </ol>
          </article>
          <aside className="student-panel student-stack">
            <h2>Hồ sơ đã gửi</h2>
            <p>
              <strong>{app.cv.title}</strong>
            </p>
            <p className="muted">
              CV được lưu tại thời điểm nộp đơn; thay đổi CV sau đó không thay đổi hồ sơ đã gửi.
            </p>
            <h3>Thư giới thiệu</h3>
            <p className="student-rich">{app.cover_letter || 'Không có thư giới thiệu.'}</p>
            <Link to={'/student/jobs/' + app.job_id}>Xem tin tuyển dụng</Link>
            {canWithdraw(app.current_status) && (
              <Button variant="danger" onClick={() => setConfirm(true)}>
                Rút đơn ứng tuyển
              </Button>
            )}
          </aside>
        </div>
      )}
      {app && (
        <ConfirmDialog
          open={confirm}
          onOpenChange={setConfirm}
          title="Rút đơn ứng tuyển?"
          description="Bạn không thể nộp lại đơn cho cùng tin tuyển dụng sau khi rút. Doanh nghiệp sẽ được thông báo."
          confirmLabel="Xác nhận rút đơn"
          danger
          onConfirm={async () => {
            await applicationsApi.withdraw(appId)
            await client.invalidateQueries({
              queryKey: ['student-applications'],
            })
          }}
        />
      )}
    </StudentPage>
  )
}
