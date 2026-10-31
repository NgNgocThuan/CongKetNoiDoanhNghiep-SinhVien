import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import { ActionDialog, DataResult, Panel } from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import { Pagination } from '@/components/common/Pagination'
import { Button } from '@/components/ui/Button'
import { statusLabel } from '@/features/administration/status'
import { ApplyDialog } from '@/features/matching'
import type { StudentApplication, Internship } from './types'
import type { Page } from '@/types/api'

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
export function ApplicationsPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page')) || 1,
    status = params.get('status') || ''
  const query = useQuery({
    queryKey: ['applications', 'me', page, status],
    queryFn: () =>
      getData<Page<StudentApplication>>('/applications/me', {
        page,
        size: 12,
        status: status || undefined,
      }),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Đơn ứng tuyển"
        description="Theo dõi hành trình ứng tuyển của bạn."
      />
      <div className="ws-filters">
        <label>
          Trạng thái
          <select
            value={status}
            onChange={(e) =>
              setParams(e.target.value ? { status: e.target.value } : {})
            }
          >
            <option value="">Tất cả</option>
            {states.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <DataResult query={query}>
        {(data) => (
          <>
            <div className="ws-cards">
              {data.items.map((item) => (
                <Panel key={item.id} title={item.job.title}>
                  <p>{item.job.company.name}</p>
                  <p>{statusLabel(item.current_status)}</p>
                  <p className="muted">
                    Ngày nộp: {item.applied_at.slice(0, 10)}
                  </p>
                  <Link to={'/student/applications/' + item.id}>
                    Chi tiết & lịch sử →
                  </Link>
                </Panel>
              ))}
            </div>
            {!data.items.length && (
              <Panel title="Chưa có đơn ứng tuyển">
                <Link to="/student/jobs">Khám phá công việc</Link>
              </Panel>
            )}
            <Pagination
              page={page}
              pages={data.pages}
              total={data.total}
              onChange={(p) =>
                setParams({ ...(status ? { status } : {}), page: String(p) })
              }
            />
          </>
        )}
      </DataResult>
    </div>
  )
}
export function ApplicationDetailPage() {
  const { applicationId } = useParams(),
    [withdraw, setWithdraw] = useState(false)
  const query = useQuery({
    queryKey: ['applications', 'detail', applicationId],
    queryFn: () =>
      getData<StudentApplication>('/applications/' + applicationId),
  })
  return (
    <div className="workspace">
      <Link to="/student/applications">← Đơn ứng tuyển</Link>
      <DataResult query={query}>
        {(data) => (
          <>
            <PageHeader
              title={data.job.title}
              description={data.job.company.name}
            />
            <Panel title="Thông tin đơn">
              <p>
                Trạng thái: <strong>{statusLabel(data.current_status)}</strong>
              </p>
              <p className="ws-preline">
                {data.cover_letter || 'Không có thư giới thiệu.'}
              </p>
              {!['OFFER', 'HIRED', 'REJECTED', 'WITHDRAWN'].includes(
                data.current_status,
              ) && (
                <Button variant="danger" onClick={() => setWithdraw(true)}>
                  Rút đơn ứng tuyển
                </Button>
              )}
            </Panel>
            <Panel title="Lịch sử xử lý">
              <ol className="ws-timeline">
                {data.status_logs?.map((log) => (
                  <li key={log.id}>
                    <strong>{statusLabel(log.new_status)}</strong>
                    <p>{log.note}</p>
                    <small>{log.changed_at.replace('T', ' ')}</small>
                  </li>
                ))}
              </ol>
            </Panel>
            {withdraw && (
              <ActionDialog
                title="Rút đơn ứng tuyển"
                path={'/applications/' + data.id + '/withdraw'}
                invalidate={['applications']}
                onClose={() => setWithdraw(false)}
              />
            )}
          </>
        )}
      </DataResult>
    </div>
  )
}
interface Invitation {
  id: number
  job_id: number
  company_id: number
  status: string
  message: string | null
  created_at: string
}
export function InvitationsPage() {
  const [page, setPage] = useState(1),
    [apply, setApply] = useState<Invitation | null>(null),
    [decline, setDecline] = useState<Invitation | null>(null)
  const query = useQuery({
    queryKey: ['student-invitations', page],
    queryFn: () =>
      getData<Page<Invitation>>('/invitations/me', { page, size: 12 }),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Lời mời từ doanh nghiệp"
        description="Xem cơ hội mới và ứng tuyển bằng CV của bạn."
      />
      <DataResult query={query}>
        {(data) => (
          <>
            <div className="ws-cards">
              {data.items.map((item) => (
                <Panel key={item.id} title={'Lời mời #' + item.id}>
                  <p>{statusLabel(item.status)}</p>
                  <p className="ws-preline">
                    {item.message || 'Doanh nghiệp mời bạn ứng tuyển.'}
                  </p>
                  <div className="ws-actions">
                    <Link
                      to={
                        '/student/jobs/' +
                        item.job_id +
                        '?invitation_id=' +
                        item.id
                      }
                    >
                      Xem tin tuyển dụng #{item.job_id}
                    </Link>
                    <Link to={'/student/companies/' + item.company_id}>
                      Doanh nghiệp
                    </Link>
                    {item.status === 'PENDING' && (
                      <>
                        <Button size="sm" onClick={() => setApply(item)}>
                          Ứng tuyển theo lời mời
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => setDecline(item)}
                        >
                          Từ chối
                        </Button>
                      </>
                    )}
                  </div>
                </Panel>
              ))}
            </div>
            {!data.items.length && (
              <Panel title="Chưa có lời mời">
                <p>
                  Bật tìm việc và cập nhật kỹ năng để doanh nghiệp có thể tìm
                  thấy bạn.
                </p>
              </Panel>
            )}
            <Pagination
              page={page}
              pages={data.pages}
              total={data.total}
              onChange={setPage}
            />
          </>
        )}
      </DataResult>
      {apply && (
        <ApplyDialog
          jobId={apply.job_id}
          title={'Ứng tuyển theo lời mời #' + apply.id}
          invitationId={apply.id}
          onClose={() => setApply(null)}
        />
      )}
      {decline && (
        <ActionDialog
          title="Từ chối lời mời"
          path={'/invitations/' + decline.id + '/decline'}
          invalidate={['student-invitations']}
          onClose={() => setDecline(null)}
        />
      )}
    </div>
  )
}
export function InternshipsPage() {
  const query = useQuery({
    queryKey: ['student-internships'],
    queryFn: () => getData<Internship[]>('/students/me/internship'),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Thực tập của tôi"
        description="Đợt thực tập và giảng viên được nhà trường phân công."
      />
      <DataResult query={query}>
        {(data) =>
          data.length ? (
            data.map((item) => (
              <Panel key={item.id} title={item.term.name}>
                <p>
                  {item.term.semester} · {item.term.academic_year} ·{' '}
                  {statusLabel(item.term.status)}
                </p>
                <p>
                  {item.term.start_date} → {item.term.end_date}
                </p>
                <h3>Giảng viên hướng dẫn</h3>
                {item.lecturer ? (
                  <>
                    <p>{item.lecturer.full_name}</p>
                    <p>
                      {item.lecturer.email || 'Chưa có email'} ·{' '}
                      {item.lecturer.phone || 'Chưa có số điện thoại'}
                    </p>
                  </>
                ) : (
                  <p>Chưa phân công giảng viên.</p>
                )}
                <Link to="/student/jobs?flow=term">
                  Xem tin tuyển dụng theo đợt
                </Link>
              </Panel>
            ))
          ) : (
            <Panel title="Chưa có đợt thực tập">
              <p>Liên hệ nhà trường nếu bạn cần được bổ sung vào đợt.</p>
            </Panel>
          )
        }
      </DataResult>
    </div>
  )
}
