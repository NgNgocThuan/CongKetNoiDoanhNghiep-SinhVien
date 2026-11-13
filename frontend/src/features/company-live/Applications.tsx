import { useState } from 'react'
import { UserAvatar } from '@/components/common/UserAvatar'
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import {
  CatalogSelect,
  DataResult,
  FieldsForm,
  Notice,
  Panel,
  RecordTable,
} from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import type { Row } from '@/components/common/Workspace'
import { Pagination } from '@/components/common/Pagination'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { http } from '@/lib/http'
import { downloadFile } from '@/utils/download'
import { statusLabel } from '@/features/administration/status'
import { toast } from '@/lib/toast'
import { errorText } from '@/features/freelancer/messages'
import type { Page } from '@/types/api'

interface Application {
  id: number
  job_id: number
  current_status: string
  contact_email: string | null
  contact_phone: string | null
  cover_letter: string | null
  interview_time?: string | null
  interview_location?: string | null
  cv_download_url: string
  student: {
    user_id: number
    full_name: string
    gpa: number | null
    skills: string[]
    experience_months: number
  }
  status_logs: {
    id: number
    new_status: string
    note: string | null
    changed_at: string
  }[]
}
const transitions: Record<string, string[]> = {
  APPLIED: ['SCREENING', 'REJECTED'],
  SCREENING: ['SHORTLISTED', 'REJECTED'],
  SHORTLISTED: ['INTERVIEW', 'REJECTED'],
  INTERVIEW: ['OFFER', 'REJECTED'],
  OFFER: ['HIRED', 'REJECTED'],
}
const states = [
  'APPLIED',
  'SCREENING',
  'SHORTLISTED',
  'INTERVIEW',
  'OFFER',
  'HIRED',
  'REJECTED',
  'WITHDRAWN',
]
function ApplicationDrawer({
  id,
  onClose,
}: {
  id: number
  onClose: () => void
}) {
  const client = useQueryClient(),
    [next, setNext] = useState('')
  const query = useQuery({
    queryKey: ['company-applications', 'detail', id],
    queryFn: () => getData<Application>('/company/applications/' + id),
  })
  const update = useMutation({
    mutationFn: async (values: Row) => {
      const payload = {
        status: next,
        note: values.note || null,
        interview_time: values.interview_time ? new Date(String(values.interview_time)).toISOString() : undefined,
        interview_location: values.interview_location || undefined,
        interview_notes: values.note || undefined,
      }
      return (await http.patch('/company/applications/' + id + '/status', payload)).data
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['company-applications'] })
      toast.success('Đã cập nhật trạng thái ứng viên!')
      setNext('')
    },
    onError: (err: unknown) => {
      toast.error(errorText(err), 'Thất bại')
    },
  })
  const download = useMutation({
    mutationFn: (path: string) => downloadFile(path, 'cv-don-' + id),
  })
  return (
    <Dialog
      open
      wide
      title={'Chi tiết đơn #' + id}
      onOpenChange={(open) => {
        if (!open && !update.isPending) onClose()
      }}
    >
      <DataResult query={query}>
        {(data) => (
          <>
            <UserAvatar userId={data.student.user_id} name={data.student.full_name} size={56} />
            <h3>{data.student.full_name}</h3>
            <dl className="ws-detail">
              <div>
                <dt>GPA</dt>
                <dd>{data.student.gpa ?? 'Không chia sẻ'}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{data.contact_email || 'Không chia sẻ'}</dd>
              </div>
              <div>
                <dt>Điện thoại</dt>
                <dd>{data.contact_phone || 'Không chia sẻ'}</dd>
              </div>
              <div>
                <dt>Kinh nghiệm</dt>
                <dd>{data.student.experience_months} tháng</dd>
              </div>
            </dl>
            <p>Kỹ năng: {data.student.skills.join(', ') || 'Chưa cung cấp'}</p>
            <p className="ws-preline">{data.cover_letter}</p>
            <Button
              variant="secondary"
              pending={download.isPending}
              onClick={() => download.mutate(data.cv_download_url)}
            >
              Tải CV đã nộp
            </Button>
            <Notice error={download.error} />
            <h3>Trạng thái: {statusLabel(data.current_status)}</h3>
            {data.interview_time && <p>Lịch phỏng vấn: {new Date(data.interview_time.endsWith('Z') ? data.interview_time : data.interview_time + 'Z').toLocaleString('vi-VN')} · {data.interview_location}</p>}
            <div className="ws-actions">
              {(transitions[data.current_status] || []).map((status) => (
                <Button
                  key={status}
                  variant={next === status ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setNext(status)}
                >
                  {statusLabel(status)}
                </Button>
              ))}
            </div>
            {next && (
              <>
                <p>
                  Xác nhận chuyển sang <strong>{statusLabel(next)}</strong>.
                </p>
                <FieldsForm
                  key={next}
                  fields={
                    next === 'INTERVIEW'
                      ? [
                          {
                            name: 'interview_time',
                            label: 'Thời gian phỏng vấn (Ngày giờ) *',
                            type: 'datetime-local',
                            required: true,
                          },
                          {
                            name: 'interview_location',
                            label: 'Địa điểm / Link phòng họp online (Google Meet, Teams, phòng họp) *',
                            type: 'text',
                            required: true,
                            maxLength: 255,
                          },
                          {
                            name: 'note',
                            label: 'Ghi chú / Dặn dò ứng viên (nội dung phỏng vấn, hồ sơ mang theo)',
                            type: 'textarea',
                            maxLength: 500,
                          },
                        ]
                      : [
                          {
                            name: 'note',
                            label: next === 'OFFER' ? 'Nội dung đề nghị tiếp nhận / thông báo trúng tuyển' : 'Ghi chú',
                            type: 'textarea',
                            maxLength: 500,
                          },
                        ]
                  }
                  submit={(v) => update.mutate(v)}
                  pending={update.isPending}
                  error={update.error instanceof Error ? update.error : null}
                  label="Xác nhận chuyển trạng thái"
                />
              </>
            )}
            <h3>Lịch sử xử lý</h3>
            <ol className="ws-timeline">
              {data.status_logs.map((log) => (
                <li key={log.id}>
                  <strong>{statusLabel(log.new_status)}</strong>
                  <p>{log.note}</p>
                  <small>{log.changed_at.replace('T', ' ')}</small>
                </li>
              ))}
            </ol>
          </>
        )}
      </DataResult>
    </Dialog>
  )
}
function KanbanColumn({
  status,
  filters,
  onOpen,
}: {
  status: string
  filters: Record<string, string>
  onOpen: (id: number) => void
}) {
  const query = useInfiniteQuery({
    queryKey: ['company-applications', 'kanban', filters, status],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      getData<Page<Application>>('/company/applications', {
        ...filters,
        status,
        page: pageParam,
        size: 10,
      }),
    getNextPageParam: (last) =>
      last.page < last.pages ? last.page + 1 : undefined,
  })
  return (
    <section className="ws-kanban-column">
      <h3>
        {statusLabel(status)}{' '}
        <small>({query.data?.pages[0].total ?? '…'})</small>
      </h3>
      <DataResult query={query}>
        {(data) => (
          <>
            {data.pages
              .flatMap((p) => p.items)
              .map((item) => (
                <article key={item.id} className="ws-card">
                  <UserAvatar userId={item.student.user_id} name={item.student.full_name} />
                  <strong>{item.student.full_name}</strong>
                  <p>GPA: {item.student.gpa ?? 'Không chia sẻ'}</p>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => onOpen(item.id)}
                  >
                    Xem & xử lý
                  </Button>
                </article>
              ))}
            {!data.pages[0].total && <p className="muted">Chưa có đơn</p>}
            {query.hasNextPage && (
              <Button
                size="sm"
                variant="secondary"
                pending={query.isFetchingNextPage}
                onClick={() => void query.fetchNextPage()}
              >
                Tải thêm
              </Button>
            )}
          </>
        )}
      </DataResult>
    </section>
  )
}
export default function CompanyApplicationsPage() {
  const [params, setParams] = useSearchParams(),
    [jobPage, setJobPage] = useState(1),
    [view, setView] = useState<'table' | 'kanban'>('table'),
    [open, setOpen] = useState<number | null>(null)
  const page = Number(params.get('page')) || 1,
    jobId = params.get('job_id') || ''
  const filters = Object.fromEntries(
    [...params].filter(([key, value]) => key !== 'page' && value),
  )
  const jobs = useQuery({
    queryKey: ['company-jobs', 'picker', jobPage],
    queryFn: () =>
      getData<Page<{ id: number; title: string }>>('/jobs/me', {
        page: jobPage,
        size: 20,
      }),
  })
  const query = useQuery({
    queryKey: ['company-applications', 'list', filters, page],
    queryFn: () =>
      getData<Page<Application>>('/company/applications', {
        ...filters,
        page,
        size: 15,
      }),
    enabled: !!jobId && view === 'table',
  })
  const change = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    next.delete('page')
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
  }
  return (
    <div className="workspace">
      <PageHeader
        title="Quản lý ứng viên"
        description="Theo dõi hồ sơ theo từng vị trí tuyển dụng."
      />
      <Panel title="Tin tuyển dụng & bộ lọc">
        <div className="ws-filters">
          <label>
            Tin tuyển dụng
            <select
              value={jobId}
              onChange={(e) => change('job_id', e.target.value)}
            >
              <option value="">Chọn tin</option>
              {jobId &&
                !jobs.data?.items.some((j) => String(j.id) === jobId) && (
                  <option value={jobId}>Tin #{jobId}</option>
                )}
              {jobs.data?.items.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Trạng thái
            <select
              value={params.get('status') || ''}
              onChange={(e) => change('status', e.target.value)}
            >
              <option value="">Tất cả</option>
              {states.map((s) => (
                <option key={s} value={s}>
                  {statusLabel(s)}
                </option>
              ))}
            </select>
          </label>
          <CatalogSelect
            resource="majors"
            name="major_id"
            label="Ngành"
            value={params.get('major_id') || ''}
            onChange={(v) => change('major_id', v)}
          />
          <CatalogSelect
            resource="skills"
            name="skill_id"
            label="Kỹ năng"
            value={params.get('skill_id') || ''}
            onChange={(v) => change('skill_id', v)}
          />
          <label>
            GPA tối thiểu
            <input
              type="number"
              min="0"
              max="4"
              step="0.1"
              value={params.get('min_gpa') || ''}
              onChange={(e) => change('min_gpa', e.target.value)}
            />
          </label>
          <label>
            Kinh nghiệm (tháng)
            <input
              type="number"
              min="0"
              value={params.get('min_experience_months') || ''}
              onChange={(e) => change('min_experience_months', e.target.value)}
            />
          </label>
        </div>
        <Notice error={jobs.error} />
        {jobs.data && (
          <Pagination
            page={jobPage}
            pages={jobs.data.pages}
            total={jobs.data.total}
            onChange={setJobPage}
          />
        )}
      </Panel>
      <div className="ws-actions">
        <Button
          variant={view === 'table' ? 'primary' : 'secondary'}
          onClick={() => setView('table')}
        >
          Danh sách
        </Button>
        <Button
          variant={view === 'kanban' ? 'primary' : 'secondary'}
          onClick={() => setView('kanban')}
        >
          Kanban
        </Button>
      </div>
      {!jobId ? (
        <Panel title="Chọn tin tuyển dụng">
          <p>Các đơn được quản lý theo từng vị trí.</p>
        </Panel>
      ) : view === 'kanban' ? (
        <div className="ws-kanban">
          {(params.get('status') ? [params.get('status')!] : states).map(
            (status) => (
              <KanbanColumn
                key={status + JSON.stringify(filters)}
                status={status}
                filters={filters}
                onOpen={setOpen}
              />
            ),
          )}
        </div>
      ) : (
        <Panel title="Danh sách ứng viên">
          <DataResult query={query}>
            {(data) => (
              <>
                <RecordTable
                  rows={data.items}
                  columns={[
                    {
                      key: 'student',
                      label: 'Sinh viên',
                      render: (r) => <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}><UserAvatar userId={r.student.user_id} name={r.student.full_name} />{r.student.full_name}</span>,
                    },
                    {
                      key: 'gpa',
                      label: 'GPA',
                      render: (r) => r.student.gpa ?? 'Không chia sẻ',
                    },
                    {
                      key: 'contact_email',
                      label: 'Email',
                      render: (r) => String(r.contact_email || 'Không chia sẻ'),
                    },
                    {
                      key: 'current_status',
                      label: 'Trạng thái',
                      render: (r) => statusLabel(r.current_status),
                    },
                  ]}
                  actions={(r) => (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setOpen(Number(r.id))}
                    >
                      Chi tiết & xử lý
                    </Button>
                  )}
                />
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
        </Panel>
      )}
      {open && (
        <ApplicationDrawer key={open} id={open} onClose={() => setOpen(null)} />
      )}
    </div>
  )
}
