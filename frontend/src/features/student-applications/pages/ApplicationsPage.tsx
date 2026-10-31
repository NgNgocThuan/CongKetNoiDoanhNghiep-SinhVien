import { dateText } from '@/features/student-jobs/format'
import { statusLabels } from '@/features/student-jobs/format'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState } from '@/components/common/States'
import { StudentPage, QueryState, Status } from '@/features/student-jobs/components/StudentUI'
import { applicationsApi } from '../api'
export default function ApplicationsPage() {
  const [params, setParams] = useSearchParams(),
    page = Math.max(1, Number(params.get('page')) || 1),
    status = params.get('status') || ''
  const query = useQuery({
    queryKey: ['student-applications', page, status],
    queryFn: ({ signal }) => applicationsApi.list(page, status, signal),
  })
  return (
    <StudentPage
      title="Đơn ứng tuyển của tôi"
      description="Theo dõi tiến trình và phản hồi từ doanh nghiệp trong từng cơ hội."
    >
      <label className="student-form">
        Trạng thái
        <select
          value={status}
          onChange={(e) => setParams(e.target.value ? { status: e.target.value } : {})}
        >
          <option value="">Tất cả trạng thái</option>
          {[
            'APPLIED',
            'SCREENING',
            'SHORTLISTED',
            'INTERVIEW',
            'OFFER',
            'HIRED',
            'REJECTED',
            'WITHDRAWN',
          ].map((s) => (
            <option key={s} value={s}>
              {statusLabels[s]}
            </option>
          ))}
        </select>
      </label>
      <QueryState query={query} />
      {query.data && (
        <>
          <div className="student-stack">
            {query.data.items.map((app) => (
              <article key={app.id} className="student-panel">
                <div className="student-section-title">
                  <h2>
                    <Link to={'/student/applications/' + app.id}>{app.job.title}</Link>
                  </h2>
                  <Status value={app.current_status} />
                </div>
                <p className="muted">{app.job.company.name}</p>
                <div className="student-meta">
                  <span>Nộp ngày {dateText(app.applied_at)}</span>
                  <Link to={'/student/applications/' + app.id}>Xem tiến trình →</Link>
                </div>
              </article>
            ))}
          </div>
          {!query.data.items.length && (
            <EmptyState
              title="Chưa có đơn ứng tuyển"
              description="Hãy tìm một cơ hội phù hợp và gửi CV của bạn."
            />
          )}
          <Pagination
            {...query.data}
            onChange={(p) => {
              const next = new URLSearchParams(params)
              next.set('page', String(p))
              setParams(next)
            }}
          />
        </>
      )}
    </StudentPage>
  )
}
