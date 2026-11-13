import { dateText } from '../format'
import { salaryText } from '../format'
import { Link } from 'react-router-dom'
import { MapPin, Clock, Building2, ArrowUpRight, Award, BriefcaseBusiness } from 'lucide-react'
import type { Job } from '../types'
import { SaveJobButton } from './SaveJobButton'
import {} from './StudentUI'
export function JobCard({ job, saved }: { job: Job; saved?: boolean }) {
  const isFeatured = Boolean(job.is_featured && job.is_mou_partner)
  return (
    <article
      className={'student-job-card' + (isFeatured ? ' is-featured' : '')}
    >
      {isFeatured && (
        <div className="student-featured-badge">
          <Award size={12} /> Đối tác MOU · Ưu tiên
        </div>
      )}
      <div className="student-card-top">
        <span className="student-logo">
          {job.company.logo_url ? (
            <img src={job.company.logo_url} alt="" />
          ) : (
            <Building2 size={24} />
          )}
        </span>
        <div>
          <Link to={'/student/companies/' + job.company.id}>
            {job.company.name}
          </Link>
          <p className="muted"><BriefcaseBusiness size={12} /> {job.job_type.name}</p>
        </div>
        <SaveJobButton jobId={job.id} saved={saved} />
      </div>
      <h2>
        <Link to={'/student/jobs/' + job.id}>{job.title}</Link>
      </h2>
      <div className="student-card-compensation">
        <span>Thu nhập</span>
        <p className="student-salary">{salaryText(job)}</p>
      </div>
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
          Ứng tuyển trực tiếp
        </span>
        {job.status !== 'APPROVED' && (
          <span className="student-tag">Không còn nhận hồ sơ</span>
        )}
      </div>
      <Link className="student-card-link" to={'/student/jobs/' + job.id}>
        <span>Xem chi tiết công việc</span> <ArrowUpRight size={16} />
      </Link>
    </article>
  )
}
