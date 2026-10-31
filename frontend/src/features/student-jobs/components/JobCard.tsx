import { dateText } from '../format'
import { salaryText } from '../format'
import { Link } from 'react-router-dom'
import { MapPin, Clock, Building2, ArrowUpRight } from 'lucide-react'
import type { Job } from '../types'
import { SaveJobButton } from './SaveJobButton'
import {} from './StudentUI'
export function JobCard({ job, saved }: { job: Job; saved?: boolean }) {
  return (
    <article className="student-job-card">
      <div className="student-card-top">
        <span className="student-logo">
          <Building2 size={24} />
        </span>
        <div>
          <Link to={'/student/companies/' + job.company.id}>{job.company.name}</Link>
          <p className="muted">{job.job_type.name}</p>
        </div>
        <SaveJobButton jobId={job.id} saved={saved} />
      </div>
      <h2>
        <Link to={'/student/jobs/' + job.id}>{job.title}</Link>
      </h2>
      <p className="student-salary">{salaryText(job)}</p>
      <div className="student-meta">
        <span>
          <MapPin size={15} />
          {job.location || 'Chưa công bố địa điểm'}
        </span>
        <span>
          <Clock size={15} />
          Hạn {dateText(job.deadline)}
        </span>
      </div>
      <div className="student-tags">
        <span className="student-tag">
          {
            (
              {
                REMOTE: 'Từ xa',
                HYBRID: 'Kết hợp',
                ONSITE: 'Trực tiếp',
              } as Record<string, string>
            )[job.work_mode]
          }
        </span>
        <span className="student-tag teal">
          {job.term_id ? 'Theo đợt thực tập' : 'Ứng tuyển tự do'}
        </span>
        {job.status !== 'APPROVED' && <span className="student-tag">Không còn nhận hồ sơ</span>}
      </div>
      <Link className="student-card-link" to={'/student/jobs/' + job.id}>
        Xem chi tiết <ArrowUpRight size={16} />
      </Link>
    </article>
  )
}
