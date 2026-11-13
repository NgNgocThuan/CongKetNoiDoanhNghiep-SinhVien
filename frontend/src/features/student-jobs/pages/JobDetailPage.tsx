import { dateText } from '../format'
import { UserAvatar } from '@/components/common/UserAvatar'
import { ReportDialog } from '@/features/administration/pages'
import { useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ApplyDialog } from '@/features/student-applications'
import { jobsApi } from '../api'
import { SaveJobButton } from '../components/SaveJobButton'
import { salaryText } from '../format'
import { StudentPage, QueryState } from '../components/StudentUI'
import { ArrowLeft, BriefcaseBusiness, Building2, CalendarDays, MapPin, Users } from 'lucide-react'
export default function JobDetailPage() {
  const { id } = useParams(),
    jobId = Number(id),
    [params] = useSearchParams(),
    navigate = useNavigate()
  const [apply, setApply] = useState(false),
    [report, setReport] = useState(false)
  const query = useQuery({
    queryKey: ['student-job', jobId],
    queryFn: ({ signal }) => jobsApi.detail(jobId, signal),
    staleTime: 300000,
    refetchOnWindowFocus: false,
  })
  const job = query.data
  const closed =
    job &&
    (job.status !== 'APPROVED' ||
      job.deadline < new Date().toISOString().slice(0, 10))
  return (
    <StudentPage
      title="Chi tiết cơ hội"
      hideHeading
    >
      <Link className="student-back-link" to="/student/jobs"><ArrowLeft size={16} /> Trở về tìm việc</Link>
      <QueryState query={query} />
      {job && (
        <>
          <article className="student-job-hero">
            <div className="student-job-hero__identity">
              <span className="student-job-hero__logo">
                {job.company.user_id ? <UserAvatar userId={job.company.user_id} name={job.company.name} size={60} /> : job.company.logo_url ? <img src={job.company.logo_url} alt="" /> : <Building2 size={30} />}
              </span>
              <div>
                <div className="student-tags">
                  <span className="student-tag teal">{job.work_mode === 'REMOTE' ? 'Từ xa' : job.work_mode === 'HYBRID' ? 'Kết hợp' : 'Trực tiếp'}</span>
                  {job.is_mou_partner && <span className="student-tag">Đối tác MOU</span>}
                </div>
                <h1>{job.title}</h1>
                <Link to={'/student/companies/' + job.company.id}>{job.company.name}</Link>
              </div>
            </div>
            <div className="student-job-overview">
              <span><MapPin size={16} /> {job.location || 'Chưa công bố địa điểm'}</span>
              <span><BriefcaseBusiness size={16} /> {job.job_type.name}</span>
              <span><Users size={16} /> {job.quantity} vị trí</span>
              <span><CalendarDays size={16} /> Hạn nộp {dateText(job.deadline)}</span>
            </div>
            <div className="student-job-hero__actions">
              <Button disabled={!!closed} onClick={() => setApply(true)}>
                {closed ? 'Không còn nhận hồ sơ' : 'Ứng tuyển ngay'}
              </Button>
              <SaveJobButton jobId={job.id} />
            </div>
          </article>
          <nav className="student-detail-nav" aria-label="Nội dung công việc">
            <a href="#job-description">Mô tả</a>
            <a href="#job-requirements">Yêu cầu</a>
            <a href="#job-benefits">Quyền lợi</a>
            <a href="#job-details">Chi tiết công việc</a>
            <a href="#job-company">Doanh nghiệp</a>
          </nav>
          <div className="student-split student-job-detail-layout">
          <article className="student-panel student-stack student-job-content">
            {[
              { id: 'job-description', title: 'Mô tả công việc', content: job.description },
              { id: 'job-requirements', title: 'Yêu cầu ứng viên', content: job.requirements },
              { id: 'job-benefits', title: 'Quyền lợi', content: job.benefits },
            ].map((section) => (
              <section id={section.id} key={section.id}>
                <h2>{section.title}</h2>
                <p className="student-rich">{section.content || 'Chưa cập nhật'}</p>
              </section>
            ))}
            <section id="job-details">
              <h2>Kỹ năng</h2>
              <div className="student-tags">
                {job.skills?.map((item) => (
                  <span className="student-tag" key={item.skill_id}>
                    {item.skill.name} ·{' '}
                    {item.is_required ? 'Bắt buộc' : 'Ưu tiên'}
                  </span>
                ))}
              </div>
            </section>
            <section>
              <h2>Ngành học</h2>
              <p>
                {job.majors?.map((item) => item.major.name).join(', ') ||
                  'Mọi ngành'}
              </p>
            </section>
          </article>
          <aside className="student-stack">
            <div className="student-panel student-apply-panel">
              <span className="student-label">Mức thu nhập</span>
              <p className="student-salary">{salaryText(job)}</p>
              <dl className="student-apply-facts">
                <div><dt>Hình thức</dt><dd>{job.job_type.name}</dd></div>
                <div><dt>Số lượng</dt><dd>{job.quantity} vị trí</dd></div>
                <div><dt>Hạn nộp</dt><dd>{dateText(job.deadline)}</dd></div>
                {job.min_gpa != null && <div><dt>GPA tối thiểu</dt><dd>{job.min_gpa}/4</dd></div>}
                {job.min_experience_months != null && <div><dt>Kinh nghiệm</dt><dd>{job.min_experience_months} tháng</dd></div>}
              </dl>
              <div className="student-stack">
                <Button disabled={!!closed} onClick={() => setApply(true)}>
                  {closed ? 'Không còn nhận hồ sơ' : 'Ứng tuyển ngay'}
                </Button>
                <SaveJobButton jobId={job.id} />
              </div>
            </div>
            <div className="student-panel" id="job-company">
              <h3>{job.company.name}</h3>
              <p className="muted">Xem thông tin, lĩnh vực hoạt động và các cơ hội khác từ doanh nghiệp.</p>
              <Link to={'/student/companies/' + job.company.id}>
                Xem hồ sơ doanh nghiệp ↗
              </Link>
            </div>
          </aside>
          </div>
        </>
      )}
      {job && (
        <ApplyDialog
          open={apply}
          jobId={job.id}
          invitationId={Number(params.get('invitation_id')) || undefined}
          onClose={() => setApply(false)}
          onSuccess={(app) => navigate('/student/applications/' + app.id)}
        />
      )}
      <Button variant="ghost" onClick={() => setReport(true)}>
        Báo cáo tin tuyển dụng
      </Button>
      {report && job && (
        <ReportDialog
          targetType="JOB"
          targetId={job.id}
          onClose={() => setReport(false)}
        />
      )}
    </StudentPage>
  )
}
