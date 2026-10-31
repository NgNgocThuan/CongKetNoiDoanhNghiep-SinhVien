import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { CatalogSelect, DataResult, Panel } from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import { Button } from '@/components/ui/Button'
import { ApplyDialog, SaveJobButton } from '@/features/matching'
import { JobMetadata } from '@/features/matching/components/JobInformation'
import type { Job, JobDetail, SavedJob } from '@/features/matching/types'
import { ReportDialog } from '@/features/administration/pages'
import type { Page } from '@/types/api'

function JobCard({ job }: { job: Job }) {
  return (
    <article className="ws-card">
      <p>{job.company.name}</p>
      <h3>
        <Link to={'/student/jobs/' + job.id}>{job.title}</Link>
      </h3>
      <JobMetadata job={job} />
      <div className="ws-actions">
        <Link
          className="button button--secondary button--sm"
          to={'/student/jobs/' + job.id}
        >
          Xem chi tiết
        </Link>
        <SaveJobButton jobId={job.id} />
      </div>
    </article>
  )
}
export function JobsPage({ saved = false }: { saved?: boolean }) {
  const [params, setParams] = useSearchParams(),
    [draft, setDraft] = useState<Record<string, string>>(() =>
      Object.fromEntries(params),
    )
  const page = Number(params.get('page')) || 1
  const filters = { ...Object.fromEntries(params), page, size: 12 }
  const query = useQuery({
    queryKey: ['student-jobs', saved, filters],
    queryFn: async () => {
      if (!saved) return getData<Page<Job>>('/jobs', filters)
      const data = await getData<Page<SavedJob>>('/saved-jobs', filters)
      return { ...data, items: data.items.map((item) => item.job) }
    },
  })
  const change = (key: string, value: string) =>
    setDraft({ ...draft, [key]: value })
  return (
    <div className="workspace">
      <PageHeader
        title={saved ? 'Việc đã lưu' : 'Khám phá cơ hội nghề nghiệp'}
        description={
          saved
            ? 'Những cơ hội bạn muốn quay lại.'
            : 'Tìm công việc theo mục tiêu và năng lực của bạn.'
        }
      />
      {!saved && (
        <Panel title="Tìm công việc phù hợp">
          <form
            className="ws-filters"
            onSubmit={(e) => {
              e.preventDefault()
              setParams(
                Object.fromEntries(
                  Object.entries(draft).filter(([k, v]) => v && k !== 'page'),
                ),
              )
            }}
          >
            <label>
              Từ khóa
              <input
                value={draft.q || ''}
                onChange={(e) => change('q', e.target.value)}
                placeholder="Vị trí, công nghệ…"
              />
            </label>
            <label>
              Địa điểm
              <input
                value={draft.location || ''}
                onChange={(e) => change('location', e.target.value)}
              />
            </label>
            <CatalogSelect
              resource="job-types"
              name="job_type_id"
              label="Loại hình"
              value={draft.job_type_id || ''}
              onChange={(v) => change('job_type_id', v)}
            />
            <CatalogSelect
              resource="industries"
              name="industry_id"
              label="Lĩnh vực"
              value={draft.industry_id || ''}
              onChange={(v) => change('industry_id', v)}
            />
            <CatalogSelect
              resource="majors"
              name="major_id"
              label="Ngành"
              value={draft.major_id || ''}
              onChange={(v) => change('major_id', v)}
            />
            <label>
              Hình thức
              <select
                value={draft.work_mode || ''}
                onChange={(e) => change('work_mode', e.target.value)}
              >
                <option value="">Tất cả</option>
                <option value="ONSITE">Tại văn phòng</option>
                <option value="REMOTE">Từ xa</option>
                <option value="HYBRID">Kết hợp</option>
              </select>
            </label>
            <label>
              Luồng tuyển dụng
              <select
                value={draft.flow || ''}
                onChange={(e) => change('flow', e.target.value)}
              >
                <option value="">Tất cả</option>
                <option value="free">Tự do</option>
                <option value="term">Theo đợt</option>
              </select>
            </label>
            <Button type="submit">Tìm kiếm</Button>
          </form>
        </Panel>
      )}
      <DataResult query={query}>
        {(data) => (
          <>
            <p className="muted">{data.total} cơ hội</p>
            <div className="ws-cards">
              {data.items.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
            {!data.items.length && (
              <Panel title="Chưa tìm thấy công việc">
                <p>Thử thay đổi bộ lọc hoặc quay lại sau.</p>
              </Panel>
            )}
            <Pagination
              page={page}
              pages={data.pages}
              total={data.total}
              onChange={(p) => {
                const next = new URLSearchParams(params)
                next.set('page', String(p))
                setParams(next)
              }}
            />
          </>
        )}
      </DataResult>
    </div>
  )
}
export function JobDetailPage() {
  const { jobId } = useParams(),
    [params] = useSearchParams(),
    [apply, setApply] = useState(false),
    [report, setReport] = useState(false)
  const query = useQuery({
    queryKey: ['student-job-detail', jobId],
    queryFn: () => getData<JobDetail>('/jobs/' + jobId),
    refetchOnWindowFocus: false,
    staleTime: 300000,
  })
  return (
    <div className="workspace">
      <Link to="/student/jobs">← Tìm việc</Link>
      <DataResult query={query}>
        {(job) => (
          <>
            <PageHeader
              title={job.title}
              description={job.company.name}
              actions={
                <div className="ws-actions">
                  <SaveJobButton jobId={job.id} />
                  <Button onClick={() => setApply(true)}>Ứng tuyển</Button>
                </div>
              }
            />
            <Panel title="Thông tin tuyển dụng">
              <JobMetadata job={job} />
              <Link to={'/student/companies/' + job.company.id}>
                Xem hồ sơ doanh nghiệp
              </Link>
              <dl className="ws-detail">
                <div>
                  <dt>GPA tối thiểu</dt>
                  <dd>{job.min_gpa ?? 'Không yêu cầu'}</dd>
                </div>
                <div>
                  <dt>Kinh nghiệm tối thiểu</dt>
                  <dd>{job.min_experience_months ?? 0} tháng</dd>
                </div>
              </dl>
            </Panel>
            {[
              ['Mô tả công việc', job.description],
              ['Yêu cầu', job.requirements],
              ['Quyền lợi', job.benefits],
            ]
              .filter(([, value]) => value)
              .map(([title, value]) => (
                <Panel key={title} title={title!}>
                  <p className="ws-preline">{value}</p>
                </Panel>
              ))}
            <Panel title="Kỹ năng">
              <div className="ws-actions">
                {job.skills.map((skill) => (
                  <span className="badge" key={skill.skill_id}>
                    {skill.skill.name} ·{' '}
                    {skill.is_required ? 'Bắt buộc' : 'Ưu tiên'}
                  </span>
                ))}
              </div>
            </Panel>
            <Button variant="ghost" onClick={() => setReport(true)}>
              Báo cáo tin tuyển dụng
            </Button>
            {apply && (
              <ApplyDialog
                jobId={job.id}
                title={job.title}
                invitationId={Number(params.get('invitation_id')) || undefined}
                onClose={() => setApply(false)}
              />
            )}
            {report && (
              <ReportDialog
                targetType="JOB"
                targetId={job.id}
                onClose={() => setReport(false)}
              />
            )}
          </>
        )}
      </DataResult>
    </div>
  )
}
export function CompanyPublicPage() {
  const { companyId } = useParams(),
    [report, setReport] = useState(false)
  const query = useQuery({
    queryKey: ['public-company', companyId],
    queryFn: () =>
      getData<{
        id: number
        name: string
        description: string | null
        address: string | null
        website: string | null
        tech_stack: string | null
        benefits: string | null
      }>('/companies/' + companyId),
  })
  return (
    <div className="workspace">
      <DataResult query={query}>
        {(data) => (
          <>
            <PageHeader
              title={data.name}
              description={data.address || 'Hồ sơ doanh nghiệp'}
            />
            <Panel title="Giới thiệu">
              <p className="ws-preline">
                {data.description || 'Chưa cung cấp giới thiệu.'}
              </p>
              <p>{data.tech_stack}</p>
              <p className="ws-preline">{data.benefits}</p>
              {data.website && /^https?:\/\//i.test(data.website) && (
                <a href={data.website} target="_blank" rel="noreferrer">
                  Website doanh nghiệp
                </a>
              )}
            </Panel>
            <Button variant="ghost" onClick={() => setReport(true)}>
              Báo cáo doanh nghiệp
            </Button>
            {report && (
              <ReportDialog
                targetType="COMPANY"
                targetId={data.id}
                onClose={() => setReport(false)}
              />
            )}
          </>
        )}
      </DataResult>
    </div>
  )
}
