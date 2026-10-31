import { dateText } from '@/features/student-jobs/format'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GraduationCap } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/common/States'
import { Pagination } from '@/components/common/Pagination'
import { StudentPage, QueryState, Status } from '@/features/student-jobs/components/StudentUI'
import { internshipsApi } from '../api'
import type { Assignment } from '../api'
export default function InternshipsPage() {
  const query = useQuery({
    queryKey: ['student-internships'],
    queryFn: ({ signal }) => internshipsApi.list(signal),
  })
  return (
    <StudentPage
      title="Thực tập của tôi"
      description="Thông tin đợt thực tập và giảng viên đồng hành cùng bạn."
    >
      <QueryState query={query} />
      {query.data?.length === 0 && (
        <EmptyState
          title="Chưa được phân công đợt thực tập"
          description="Nhà trường sẽ cập nhật thông tin khi bạn được thêm vào một đợt."
        />
      )}
      {query.data?.map((item) => (
        <AssignmentCard key={item.id} item={item} />
      ))}
    </StudentPage>
  )
}
function AssignmentCard({ item }: { item: Assignment }) {
  const [show, setShow] = useState(false),
    [page, setPage] = useState(1)
  const jobs = useQuery({
    queryKey: ['student-term-jobs', item.term.id, page],
    queryFn: ({ signal }) => internshipsApi.jobs(item.term.id, page, signal),
    enabled: show,
  })
  return (
    <article className="student-panel student-stack">
      <div className="student-section-title">
        <span className="student-logo">
          <GraduationCap />
        </span>
        <Status value={item.term.status} />
      </div>
      <h2>{item.term.name}</h2>
      <div className="student-definition">
        <div>
          <dt>Học kỳ / Năm học</dt>
          <dd>
            {item.term.semester} · {item.term.academic_year}
          </dd>
        </div>
        <div>
          <dt>Thời gian</dt>
          <dd>
            {dateText(item.term.start_date)} – {dateText(item.term.end_date)}
          </dd>
        </div>
      </div>
      <section className="student-notice">
        <h3>Giảng viên hướng dẫn</h3>
        {item.lecturer ? (
          <>
            <strong>{item.lecturer.full_name}</strong>
            <div className="student-link-list">
              {item.lecturer.email && (
                <a href={'mailto:' + item.lecturer.email}>{item.lecturer.email}</a>
              )}
              {item.lecturer.phone && <span>{item.lecturer.phone}</span>}
            </div>
          </>
        ) : (
          <p>Nhà trường chưa phân công giảng viên.</p>
        )}
      </section>
      <Button variant="secondary" onClick={() => setShow(!show)}>
        {show ? 'Ẩn tin tuyển dụng' : 'Xem tin thuộc đợt'}
      </Button>
      {show && (
        <>
          <QueryState query={jobs} />
          {jobs.data && (
            <>
              {jobs.data.items.map((job) => (
                <div className="student-record" key={job.id}>
                  <Link to={'/student/jobs/' + job.id}>{job.title}</Link>
                  <span>Hạn {dateText(job.deadline)}</span>
                </div>
              ))}
              {!jobs.data.items.length && <EmptyState title="Chưa có tin tuyển dụng thuộc đợt" />}
              <Pagination {...jobs.data} onChange={setPage} />
            </>
          )}
        </>
      )}
    </article>
  )
}
