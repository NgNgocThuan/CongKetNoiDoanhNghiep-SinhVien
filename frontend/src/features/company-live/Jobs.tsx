import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import {
  ActionDialog,
  CatalogSelect,
  DataResult,
  FieldsForm,
  Notice,
  Panel,
  RecordTable,
} from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import type { Field, Row } from '@/components/common/Workspace'
import { Pagination } from '@/components/common/Pagination'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { LoadingState, ErrorState } from '@/components/common/States'
import { http } from '@/lib/http'
import { statusLabel } from '@/features/administration/status'
import type { Page } from '@/types/api'

const numberFields = [
  'job_type_id',
  'industry_id',
  'term_id',
  'quantity',
  'salary_min',
  'salary_max',
  'min_gpa',
  'min_experience_months',
]
function JobEditorForm({
  data = {},
  onClose,
}: {
  data?: Row
  onClose: () => void
}) {
  const client = useQueryClient(),
    [skillId, setSkillId] = useState(''),
    [required, setRequired] = useState(true),
    [majorId, setMajorId] = useState('')
  const [skills, setSkills] = useState<
    { skill_id: number; is_required: boolean; name: string }[]
  >(() =>
    (
      (data.skills || []) as {
        skill_id: number
        is_required: boolean
        skill: { name: string }
      }[]
    ).map((s) => ({ ...s, name: s.skill.name })),
  )
  const [majors, setMajors] = useState<number[]>(() =>
    ((data.majors || []) as { major_id: number }[]).map((m) => m.major_id),
  )
  const types = useQuery({
    queryKey: ['job-editor-types'],
    queryFn: () =>
      getData<Page<{ id: number; name: string }>>('/catalog/job-types', {
        size: 100,
      }),
  })
  const industries = useQuery({
    queryKey: ['company-industries'],
    queryFn: () =>
      getData<Page<{ id: number; name: string }>>('/catalog/industries', {
        size: 100,
      }),
  })
  const fields: Field[] = [
    { name: 'title', label: 'Tiêu đề', required: true, maxLength: 255 },
    { name: 'position', label: 'Vị trí', required: true, maxLength: 255 },
    {
      name: 'job_type_id',
      label: 'Loại hình',
      type: 'select',
      required: true,
      options: types.data?.items.map((i) => ({ value: i.id, label: i.name })),
    },
    {
      name: 'industry_id',
      label: 'Lĩnh vực',
      type: 'select',
      options: industries.data?.items.map((i) => ({
        value: i.id,
        label: i.name,
      })),
    },
    {
      name: 'term_id',
      label: 'Mã đợt thực tập (để trống = tuyển tự do)',
      type: 'number',
      min: 1,
    },
    {
      name: 'quantity',
      label: 'Số lượng',
      type: 'number',
      required: true,
      min: 1,
      max: 10000,
    },
    { name: 'deadline', label: 'Hạn nộp', type: 'date', required: true },
    {
      name: 'work_mode',
      label: 'Hình thức',
      type: 'select',
      required: true,
      options: [
        { value: 'ONSITE', label: 'Tại văn phòng' },
        { value: 'REMOTE', label: 'Từ xa' },
        { value: 'HYBRID', label: 'Kết hợp' },
      ],
    },
    { name: 'location', label: 'Địa điểm', maxLength: 255 },
    {
      name: 'salary_min',
      label: 'Lương tối thiểu (VNĐ)',
      type: 'number',
      min: 0,
      max: 2000000000,
    },
    {
      name: 'salary_max',
      label: 'Lương tối đa (VNĐ)',
      type: 'number',
      min: 0,
      max: 2000000000,
    },
    {
      name: 'is_salary_negotiable',
      label: 'Lương thỏa thuận',
      type: 'checkbox',
    },
    {
      name: 'min_gpa',
      label: 'GPA tối thiểu (0–4)',
      type: 'number',
      min: 0,
      max: 4,
      step: '0.01',
    },
    {
      name: 'min_experience_months',
      label: 'Kinh nghiệm tối thiểu (tháng)',
      type: 'number',
      min: 0,
      max: 600,
    },
    {
      name: 'description',
      label: 'Mô tả công việc',
      type: 'textarea',
      required: true,
    },
    { name: 'requirements', label: 'Yêu cầu', type: 'textarea' },
    { name: 'benefits', label: 'Quyền lợi', type: 'textarea' },
  ]
  const mutation = useMutation({
    mutationFn: async (values: Row) => {
      const payload = Object.fromEntries(
        fields.map((f) => [
          f.name,
          f.type === 'checkbox'
            ? Boolean(values[f.name])
            : values[f.name] === '' ||
                values[f.name] === undefined ||
                values[f.name] === null
              ? null
              : numberFields.includes(f.name)
                ? Number(values[f.name])
                : values[f.name],
        ]),
      )
      if (
        payload.salary_min !== null &&
        payload.salary_max !== null &&
        Number(payload.salary_min) > Number(payload.salary_max)
      )
        throw new Error('Lương tối đa phải lớn hơn hoặc bằng lương tối thiểu.')
      const body = {
        ...payload,
        skills: skills.map(({ skill_id, is_required }) => ({
          skill_id,
          is_required,
        })),
        major_ids: majors,
      }
      return data.id
        ? http.put('/jobs/' + data.id, body)
        : http.post('/jobs', body)
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['company-jobs'] })
      await client.invalidateQueries({ queryKey: ['company-job-edit'] })
      onClose()
    },
  })
  const initial = {
    ...Object.fromEntries(fields.map((f) => [f.name, data[f.name] ?? ''])),
    quantity: data.quantity ?? 1,
    work_mode: data.work_mode ?? 'ONSITE',
    job_type_id: (data.job_type as Row)?.id ?? '',
    industry_id: (data.industry as Row)?.id ?? '',
  }
  if (types.isPending || industries.isPending) return <LoadingState />
  if (types.isError || industries.isError)
    return (
      <ErrorState
        message={(types.error || industries.error)?.message}
        onRetry={() => {
          void types.refetch()
          void industries.refetch()
        }}
      />
    )
  return (
    <>
      <Notice error={types.error || industries.error} />
      {data.status === 'APPROVED' && (
        <p className="muted">
          Chỉnh sửa tin đã duyệt sẽ đưa tin về chờ kiểm duyệt.
        </p>
      )}
      <FieldsForm
        fields={fields}
        initial={initial}
        submit={(v) => mutation.mutate(v)}
        pending={mutation.isPending}
        error={mutation.error}
        label={data.id ? 'Lưu thay đổi' : 'Lưu nháp'}
      />
      <hr />
      <h3>Kỹ năng yêu cầu</h3>
      <div className="ws-filters">
        <CatalogSelect
          resource="skills"
          name="skill_id"
          label="Kỹ năng"
          value={skillId}
          onChange={setSkillId}
        />
        <label>
          Yêu cầu
          <select
            value={String(required)}
            onChange={(e) => setRequired(e.target.value === 'true')}
          >
            <option value="true">Bắt buộc</option>
            <option value="false">Ưu tiên</option>
          </select>
        </label>
        <Button
          variant="secondary"
          disabled={
            !skillId || skills.some((s) => s.skill_id === Number(skillId))
          }
          onClick={() =>
            setSkills([
              ...skills,
              {
                skill_id: Number(skillId),
                is_required: required,
                name: 'Kỹ năng #' + skillId,
              },
            ])
          }
        >
          Thêm kỹ năng
        </Button>
      </div>
      <div className="ws-actions">
        {skills.map((s) => (
          <Button
            size="sm"
            variant="secondary"
            key={s.skill_id}
            onClick={() =>
              setSkills(skills.filter((x) => x.skill_id !== s.skill_id))
            }
          >
            {s.name} · {s.is_required ? 'Bắt buộc' : 'Ưu tiên'} ×
          </Button>
        ))}
      </div>
      <h3>Giới hạn ngành học</h3>
      <p className="muted">Không chọn ngành = mọi ngành được ứng tuyển.</p>
      <div className="ws-filters">
        <CatalogSelect
          resource="majors"
          name="major_id"
          label="Ngành"
          value={majorId}
          onChange={setMajorId}
        />
        <Button
          variant="secondary"
          disabled={!majorId || majors.includes(Number(majorId))}
          onClick={() => setMajors([...majors, Number(majorId)])}
        >
          Thêm ngành
        </Button>
      </div>
      <div className="ws-actions">
        {majors.map((id) => (
          <Button
            key={id}
            size="sm"
            variant="secondary"
            onClick={() => setMajors(majors.filter((m) => m !== id))}
          >
            Ngành #{id} ×
          </Button>
        ))}
      </div>
      <p className="muted">Bấm lưu ở phía trên sau khi chọn kỹ năng/ngành.</p>
    </>
  )
}
function JobEditor({
  id,
  onClose,
}: {
  id: number | 'new'
  onClose: () => void
}) {
  const query = useQuery({
    queryKey: ['company-job-edit', id],
    queryFn: () =>
      id === 'new' ? Promise.resolve({} as Row) : getData<Row>('/jobs/' + id),
  })
  return (
    <Dialog
      open
      wide
      title={id === 'new' ? 'Tạo tin tuyển dụng' : 'Chỉnh sửa tin tuyển dụng'}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DataResult query={query}>
        {(data) => <JobEditorForm data={data} onClose={onClose} />}
      </DataResult>
    </Dialog>
  )
}
export default function CompanyJobsPage() {
  const [page, setPage] = useState(1),
    [status, setStatus] = useState(''),
    [edit, setEdit] = useState<number | 'new' | null>(null),
    [action, setAction] = useState<{ id: number; action: string } | null>(null)
  const query = useQuery({
    queryKey: ['company-jobs', page, status],
    queryFn: () =>
      getData<Page<Row>>('/jobs/me', {
        page,
        size: 12,
        status: status || undefined,
      }),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Tin tuyển dụng"
        description="Quản lý cơ hội và theo dõi hiệu quả tuyển dụng."
        actions={
          <Button onClick={() => setEdit('new')}>Tạo tin tuyển dụng</Button>
        }
      />
      <div className="ws-filters">
        <label>
          Trạng thái
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setPage(1)
            }}
          >
            <option value="">Tất cả</option>
            {[
              'DRAFT',
              'PENDING_APPROVAL',
              'APPROVED',
              'REJECTED',
              'CLOSED',
              'EXPIRED',
            ].map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <Panel title="Tin của doanh nghiệp">
        <DataResult query={query}>
          {(data) => (
            <>
              <RecordTable
                rows={data.items}
                columns={[
                  {
                    key: 'title',
                    label: 'Vị trí',
                    render: (r) => (
                      <>
                        <strong>{String(r.title)}</strong>
                        {r.reject_reason && (
                          <p className="ws-error">{String(r.reject_reason)}</p>
                        )}
                      </>
                    ),
                  },
                  {
                    key: 'status',
                    label: 'Trạng thái',
                    render: (r) => statusLabel(r.status),
                  },
                  { key: 'deadline', label: 'Hạn nộp' },
                  { key: 'application_count', label: 'Đơn' },
                  { key: 'view_count', label: 'Lượt xem' },
                ]}
                actions={(r) => (
                  <>
                    {!['CLOSED', 'EXPIRED'].includes(String(r.status)) && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setEdit(Number(r.id))}
                      >
                        Chỉnh sửa
                      </Button>
                    )}
                    <Link to={'/company/jobs/' + r.id + '/stats'}>
                      Thống kê
                    </Link>
                    <Link to={'/company/applications?job_id=' + r.id}>
                      Ứng viên
                    </Link>
                    <Link to={'/company/candidates?job_id=' + r.id}>Gợi ý</Link>
                    {['DRAFT', 'REJECTED'].includes(String(r.status)) && (
                      <Button
                        size="sm"
                        onClick={() =>
                          setAction({ id: Number(r.id), action: 'submit' })
                        }
                      >
                        Gửi duyệt
                      </Button>
                    )}
                    {!['CLOSED', 'EXPIRED'].includes(String(r.status)) && (
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() =>
                          setAction({ id: Number(r.id), action: 'close' })
                        }
                      >
                        Đóng tin
                      </Button>
                    )}
                  </>
                )}
              />
              <Pagination
                page={page}
                pages={data.pages}
                total={data.total}
                onChange={setPage}
              />
            </>
          )}
        </DataResult>
      </Panel>
      {edit !== null && <JobEditor id={edit} onClose={() => setEdit(null)} />}
      {action && (
        <ActionDialog
          title={
            action.action === 'submit'
              ? 'Gửi tin kiểm duyệt'
              : 'Đóng tin tuyển dụng'
          }
          path={'/jobs/' + action.id + '/' + action.action}
          invalidate={['company-jobs']}
          onClose={() => setAction(null)}
        />
      )}
    </div>
  )
}
export function JobStatsPage() {
  const { jobId } = useParams(),
    [days, setDays] = useState(30)
  const query = useQuery({
    queryKey: ['company-job-stats', jobId, days],
    queryFn: () =>
      getData<{
        total_views: number
        total_applications: number
        views_by_day: { day: string; views: number }[]
        applications_by_status: Record<string, number>
      }>('/jobs/' + jobId + '/stats', { days }),
  })
  return (
    <div className="workspace">
      <PageHeader
        title={'Thống kê tin #' + jobId}
        description="Lượt xem và tình trạng các đơn ứng tuyển."
      />
      <Link to="/company/jobs">← Tin tuyển dụng</Link>
      <label>
        Số ngày{' '}
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value="7">7 ngày</option>
          <option value="30">30 ngày</option>
          <option value="90">90 ngày</option>
        </select>
      </label>
      <DataResult query={query}>
        {(data) => (
          <>
            <div className="ws-cards">
              <Panel title="Lượt xem">
                <strong className="ws-number">{data.total_views}</strong>
              </Panel>
              <Panel title="Đơn ứng tuyển">
                <strong className="ws-number">{data.total_applications}</strong>
              </Panel>
            </div>
            <Panel title="Đơn theo trạng thái">
              <RecordTable
                rows={Object.entries(data.applications_by_status).map(
                  ([status, count]) => ({ status, count }),
                )}
                columns={[
                  {
                    key: 'status',
                    label: 'Trạng thái',
                    render: (r) => statusLabel(r.status),
                  },
                  { key: 'count', label: 'Số đơn' },
                ]}
              />
            </Panel>
            <Panel title="Lượt xem theo ngày">
              <RecordTable
                rows={data.views_by_day}
                columns={[
                  { key: 'day', label: 'Ngày' },
                  { key: 'views', label: 'Lượt xem' },
                ]}
              />
            </Panel>
          </>
        )}
      </DataResult>
    </div>
  )
}
