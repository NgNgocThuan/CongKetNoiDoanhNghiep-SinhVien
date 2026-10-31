import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import {
  ActionDialog,
  DataResult,
  Notice,
  Panel,
  RecordTable,
} from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import type { Field, Row } from '@/components/common/Workspace'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import type { Page } from '@/types/api'
import { statusLabel } from './status'

type Kind = 'users' | 'companies' | 'jobs' | 'reports' | 'email-logs'
const config: Record<
  Kind,
  {
    title: string
    path: string
    statusKey: string
    statuses: string[]
    columns: string[][]
    fields: string[][]
  }
> = {
  users: {
    title: 'Quản lý tài khoản',
    path: '/admin/users',
    statusKey: 'status',
    statuses: ['ACTIVE', 'LOCKED', 'PENDING_ACTIVATION', 'PENDING_APPROVAL'],
    columns: [
      ['email', 'Email'],
      ['role', 'Vai trò'],
      ['status', 'Trạng thái'],
    ],
    fields: [
      ['email', 'Email'],
      ['role', 'Vai trò'],
      ['status', 'Trạng thái'],
      ['locked_reason', 'Lý do khóa'],
      ['last_login_at', 'Đăng nhập gần nhất'],
    ],
  },
  companies: {
    title: 'Kiểm duyệt doanh nghiệp',
    path: '/admin/companies',
    statusKey: 'verification_status',
    statuses: ['PENDING', 'APPROVED', 'REJECTED'],
    columns: [
      ['name', 'Doanh nghiệp'],
      ['tax_code', 'Mã số thuế'],
      ['verification_status', 'Xác thực'],
    ],
    fields: [
      ['name', 'Doanh nghiệp'],
      ['tax_code', 'Mã số thuế'],
      ['address', 'Địa chỉ'],
      ['website', 'Website'],
      ['contact_name', 'Người liên hệ'],
      ['contact_phone', 'Điện thoại'],
      ['description', 'Giới thiệu'],
      ['tech_stack', 'Công nghệ'],
      ['benefits', 'Phúc lợi'],
      ['reject_reason', 'Lý do từ chối'],
    ],
  },
  jobs: {
    title: 'Kiểm duyệt tin tuyển dụng',
    path: '/admin/jobs',
    statusKey: 'status',
    statuses: [
      'PENDING_APPROVAL',
      'DRAFT',
      'APPROVED',
      'REJECTED',
      'CLOSED',
      'EXPIRED',
    ],
    columns: [
      ['title', 'Tiêu đề'],
      ['position', 'Vị trí'],
      ['status', 'Trạng thái'],
      ['deadline', 'Hạn nộp'],
    ],
    fields: [
      ['title', 'Tiêu đề'],
      ['position', 'Vị trí'],
      ['status', 'Trạng thái'],
      ['description', 'Mô tả'],
      ['requirements', 'Yêu cầu'],
      ['benefits', 'Quyền lợi'],
      ['deadline', 'Hạn nộp'],
      ['location', 'Địa điểm'],
      ['min_gpa', 'GPA tối thiểu'],
      ['reject_reason', 'Lý do từ chối'],
    ],
  },
  reports: {
    title: 'Báo cáo vi phạm',
    path: '/reports',
    statusKey: 'status',
    statuses: ['PENDING', 'RESOLVED', 'REJECTED'],
    columns: [
      ['target_type', 'Đối tượng'],
      ['target_id', 'Mã đối tượng'],
      ['reason', 'Nội dung'],
      ['status', 'Trạng thái'],
    ],
    fields: [
      ['reporter_id', 'Mã người báo cáo'],
      ['target_type', 'Loại đối tượng'],
      ['target_id', 'Mã đối tượng'],
      ['reason', 'Nội dung'],
      ['status', 'Trạng thái'],
      ['resolution_note', 'Kết quả xử lý'],
      ['handled_at', 'Thời điểm xử lý'],
    ],
  },
  'email-logs': {
    title: 'Nhật ký email',
    path: '/admin/users/email-logs',
    statusKey: 'status',
    statuses: ['PENDING', 'SENT', 'FAILED'],
    columns: [
      ['recipient_email', 'Người nhận'],
      ['subject', 'Tiêu đề'],
      ['status', 'Trạng thái'],
      ['retry_count', 'Số lần thử'],
    ],
    fields: [
      ['recipient_email', 'Người nhận'],
      ['type', 'Loại email'],
      ['subject', 'Tiêu đề'],
      ['status', 'Trạng thái'],
      ['error_message', 'Lỗi gửi'],
      ['retry_count', 'Số lần thử'],
      ['sent_at', 'Thời điểm gửi'],
      ['created_at', 'Thời điểm tạo'],
    ],
  },
}
type Action = {
  title: string
  path: string
  fields?: Field[]
  initial?: Row
  transform?: (values: Row) => Row
}
function actionsFor(kind: Kind, row: Row): Action[] {
  const path = config[kind].path + '/' + row.id
  if (kind === 'users')
    return row.status === 'LOCKED'
      ? [{ title: 'Mở khóa tài khoản', path: path + '/unlock' }]
      : [
          {
            title: 'Khóa tài khoản',
            path: path + '/lock',
            fields: [
              {
                name: 'reason',
                label: 'Lý do khóa',
                type: 'textarea',
                required: true,
                maxLength: 500,
              },
            ],
          },
        ]
  if (
    (kind === 'companies' && row.verification_status === 'PENDING') ||
    (kind === 'jobs' && row.status === 'PENDING_APPROVAL')
  )
    return [
      { title: 'Phê duyệt', path: path + '/approve' },
      {
        title: 'Từ chối',
        path: path + '/reject',
        fields: [
          {
            name: 'reject_reason',
            label: 'Lý do từ chối',
            type: 'textarea',
            required: true,
            maxLength: 500,
          },
        ],
      },
    ]
  if (kind === 'jobs' && row.status === 'APPROVED')
    return [
      {
        title: 'Đóng tin',
        path: path + '/close',
        fields: [
          {
            name: 'reason',
            label: 'Lý do đóng',
            type: 'textarea',
            maxLength: 500,
          },
        ],
      },
    ]
  if (kind === 'reports' && row.status === 'PENDING')
    return [
      {
        title: 'Xử lý báo cáo',
        path: path + '/handle',
        fields: [
          {
            name: 'status',
            label: 'Kết quả',
            type: 'select',
            required: true,
            options: [
              { value: 'RESOLVED', label: 'Đã xử lý' },
              { value: 'REJECTED', label: 'Bác bỏ báo cáo' },
            ],
          },
          {
            name: 'resolution_note',
            label: 'Ghi chú xử lý',
            type: 'textarea',
            maxLength: 500,
          },
          {
            name: 'lock_target_user',
            label: 'Khóa tài khoản đối tượng khi xác nhận vi phạm',
            type: 'checkbox',
          },
          ...(row.target_type === 'JOB'
            ? [
                {
                  name: 'close_target_job',
                  label: 'Đóng tin vi phạm',
                  type: 'checkbox' as const,
                },
              ]
            : []),
        ],
        transform: (values) => ({
          ...values,
          lock_target_user:
            values.status === 'RESOLVED' && Boolean(values.lock_target_user),
          close_target_job:
            values.status === 'RESOLVED' && Boolean(values.close_target_job),
        }),
      },
    ]
  return []
}
function Detail({
  kind,
  row,
  onClose,
  onAction,
}: {
  kind: Kind
  row: Row
  onClose: () => void
  onAction: (a: Action) => void
}) {
  const query = useQuery({
    queryKey: ['administration', kind, row.id],
    queryFn: () =>
      kind === 'email-logs'
        ? Promise.resolve(row)
        : getData<Row>(config[kind].path + '/' + row.id),
  })
  return (
    <Dialog
      open
      title={config[kind].title + ' — #' + row.id}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <DataResult query={query}>
        {(data) => (
          <>
            <dl className="ws-detail">
              {config[kind].fields.map(([key, label]) => (
                <div key={key}>
                  <dt>{label}</dt>
                  <dd>{statusLabel(data[key])}</dd>
                </div>
              ))}
            </dl>
            {kind === 'companies' && (
              <>
                <h3>Giấy tờ xác thực</h3>
                <RecordTable
                  rows={(data.documents || []) as Row[]}
                  columns={[
                    { key: 'doc_type', label: 'Loại giấy tờ' },
                    { key: 'file_url', label: 'Tham chiếu tệp' },
                    { key: 'uploaded_at', label: 'Ngày tải' },
                  ]}
                />
                <p className="muted">
                  Backend hiện trả tham chiếu tệp, chưa có API tải giấy tờ được
                  bảo vệ.
                </p>
              </>
            )}
            <div className="ws-actions">
              {actionsFor(kind, data).map((a) => (
                <Button key={a.path} onClick={() => onAction(a)}>
                  {a.title}
                </Button>
              ))}
            </div>
          </>
        )}
      </DataResult>
    </Dialog>
  )
}
export function AdministrationPage({ kind }: { kind: Kind }) {
  const cfg = config[kind]
  const [params, setParams] = useSearchParams(),
    [detail, setDetail] = useState<Row | null>(null),
    [action, setAction] = useState<Action | null>(null),
    [result, setResult] = useState('')
  const page = Number(params.get('page')) || 1
  const status =
    params.get('status') ?? (kind === 'jobs' ? 'PENDING_APPROVAL' : '')
  const filters = {
    page,
    size: 20,
    [cfg.statusKey]: status || undefined,
    q: params.get('q') || undefined,
    role: params.get('role') || undefined,
    type: params.get('type') || undefined,
    target_type: params.get('target_type') || undefined,
  }
  const query = useQuery({
    queryKey: ['administration', kind, filters],
    queryFn: () => getData<Page<Row>>(cfg.path, filters),
  })
  const change = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    next.set(key, value)
    next.delete('page')
    setParams(next)
  }
  return (
    <div className="workspace">
      <PageHeader
        title={cfg.title}
        description="Dữ liệu và thao tác theo quyền quản trị nhà trường."
        actions={
          kind === 'users' ? (
            <Button
              onClick={() =>
                setAction({
                  title: 'Tạo quản trị viên',
                  path: '/admin/users/admins',
                  fields: [
                    {
                      name: 'full_name',
                      label: 'Họ và tên',
                      required: true,
                      maxLength: 255,
                    },
                    {
                      name: 'email',
                      label: 'Email',
                      type: 'email',
                      required: true,
                    },
                    {
                      name: 'password',
                      label: 'Mật khẩu (ít nhất 8 ký tự)',
                      type: 'password',
                      required: true,
                      minLength: 8,
                      maxLength: 128,
                    },
                  ],
                })
              }
            >
              Tạo quản trị viên
            </Button>
          ) : kind === 'email-logs' ? (
            <Button
              onClick={() =>
                setAction({
                  title: 'Xếp hàng gửi lại tất cả email lỗi',
                  path: '/admin/users/email-logs/retry',
                })
              }
            >
              Gửi lại email lỗi
            </Button>
          ) : undefined
        }
      />
      <Panel title="Bộ lọc">
        <div className="ws-filters">
          {['users', 'companies', 'jobs'].includes(kind) && (
            <label>
              Tìm kiếm
              <input
                value={params.get('q') || ''}
                onChange={(e) => change('q', e.target.value)}
                placeholder="Nhập từ khóa…"
              />
            </label>
          )}
          <label>
            Trạng thái
            <select
              value={status}
              onChange={(e) => change('status', e.target.value)}
            >
              {kind !== 'jobs' && <option value="">Tất cả</option>}
              {cfg.statuses.map((s) => (
                <option key={s} value={s}>
                  {statusLabel(s)}
                </option>
              ))}
            </select>
          </label>
          {kind === 'users' && (
            <label>
              Vai trò
              <select
                value={params.get('role') || ''}
                onChange={(e) => change('role', e.target.value)}
              >
                <option value="">Tất cả</option>
                {['ADMIN', 'STUDENT', 'COMPANY'].map((s) => (
                  <option key={s} value={s}>
                    {statusLabel(s)}
                  </option>
                ))}
              </select>
            </label>
          )}
          {kind === 'reports' && (
            <label>
              Đối tượng
              <select
                value={params.get('target_type') || ''}
                onChange={(e) => change('target_type', e.target.value)}
              >
                <option value="">Tất cả</option>
                {['JOB', 'COMPANY', 'STUDENT'].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          )}
          {kind === 'email-logs' && (
            <label>
              Loại email
              <input
                value={params.get('type') || ''}
                onChange={(e) => change('type', e.target.value)}
              />
            </label>
          )}
        </div>
      </Panel>
      <Notice success={result} />
      <Panel title="Danh sách">
        <DataResult query={query}>
          {(data) => (
            <>
              <RecordTable
                rows={data.items}
                columns={cfg.columns.map(([key, label]) => ({
                  key,
                  label,
                  render: (row: Row) => statusLabel(row[key]),
                }))}
                actions={(row) => (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setDetail(row)}
                  >
                    Chi tiết
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
      {detail && !action && (
        <Detail
          key={String(detail.id)}
          kind={kind}
          row={detail}
          onClose={() => setDetail(null)}
          onAction={setAction}
        />
      )}
      {action && (
        <ActionDialog
          {...action}
          invalidate={['administration']}
          onClose={() => {
            setAction(null)
            setDetail(null)
          }}
          onSuccess={() =>
            setResult('Đã hoàn tất thao tác. Danh sách đã được cập nhật.')
          }
        />
      )}
    </div>
  )
}
export function ReportDialog({
  targetType,
  targetId,
  onClose,
}: {
  targetType: 'JOB' | 'COMPANY'
  targetId: number
  onClose: () => void
}) {
  return (
    <ActionDialog
      title="Báo cáo vi phạm"
      path="/reports"
      fields={[
        {
          name: 'reason',
          label: 'Nội dung phản ánh',
          type: 'textarea',
          required: true,
          maxLength: 500,
        },
      ]}
      transform={(values) => ({
        ...values,
        target_type: targetType,
        target_id: targetId,
      })}
      invalidate={['reports']}
      onClose={onClose}
    />
  )
}
