/** Admin: chi tiết một đợt thực tập: tiến trình trạng thái và các tab Tổng quan / Sinh viên / Tin / Kết quả. */
import { useState } from 'react'
import { App, Button, Popconfirm, Result, Skeleton, Steps, Tabs } from 'antd'
import { ArrowLeftOutlined, ArrowRightOutlined, SettingOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import PageHeader from '@/features/school-shared/components/PageHeader'
import QueryError from '@/features/school-shared/components/QueryError'
import { formatDate } from '@/features/school-shared/format'
import { getErrorMessage, getErrorStatus } from '@/features/school-shared/http'
import { useChangeTermStatus, useTerm } from './api'
import { TermStatusBadge } from './badges'
import { isTermEditable, nextStatus, TERM_STATUS_LABEL, TERM_STEPS } from './rules'
import TermFormModal from './TermFormModal'
import TermJobsTab from './TermJobsTab'
import TermOverviewTab from './TermOverviewTab'
import TermResultsTab from './TermResultsTab'
import TermStudentsTab from './TermStudentsTab'

const STEP_NOTE = {
  DRAFT: 'Đang soạn, chưa mở',
  OPEN: 'Sinh viên đăng ký tin của đợt',
  ONGOING: 'Sinh viên đang thực tập',
  CLOSED: 'Đã chốt kết quả',
} as const

export default function TermDetailPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const params = useParams()
  const termId = Number(params.termId)
  const [editing, setEditing] = useState(false)
  const query = useTerm(termId)
  const changeStatus = useChangeTermStatus(termId)

  if (!Number.isInteger(termId)) return <Result status="404" title="Không tìm thấy đợt thực tập" />
  if (query.isLoading) return <Skeleton active paragraph={{ rows: 8 }} />
  if (getErrorStatus(query.error) === 404) {
    return (
      <Result
        status="404"
        title="Không tìm thấy đợt thực tập"
        extra={<Button onClick={() => navigate('/admin/internships')}>Về danh sách</Button>}
      />
    )
  }
  if (query.isError || !query.data) return <QueryError error={query.error} onRetry={() => query.refetch()} />

  const term = query.data
  const next = nextStatus(term.status)

  const advance = async () => {
    if (!next) return
    try {
      await changeStatus.mutateAsync(next)
      message.success(`Đã chuyển đợt sang "${TERM_STATUS_LABEL[next]}"`)
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Phân hệ quản trị"
        title={term.name}
        subtitle={`Năm học ${term.academic_year} · ${term.semester} · ${formatDate(term.start_date)} - ${formatDate(term.end_date)}`}
        meta={<TermStatusBadge status={term.status} />}
        extra={
          <>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/admin/internships')}>
              Danh sách đợt
            </Button>
            {isTermEditable(term.status) && (
              <Button icon={<SettingOutlined />} onClick={() => setEditing(true)}>
                Cấu hình đợt
              </Button>
            )}
            {next && (
              <Popconfirm
                title={`Chuyển đợt sang "${TERM_STATUS_LABEL[next]}"?`}
                description={next === 'CLOSED' ? 'Đợt đã kết thúc sẽ không thể chỉnh sửa hay mở lại.' : 'Chỉ chuyển tiến từng bước, không quay lại.'}
                okText="Chuyển"
                cancelText="Hủy"
                onConfirm={advance}
              >
                <Button type="primary" icon={<ArrowRightOutlined />} loading={changeStatus.isPending}>
                  Chuyển sang {TERM_STATUS_LABEL[next]}
                </Button>
              </Popconfirm>
            )}
          </>
        }
      />

      <div className="sc-card" style={{ padding: 24, marginBottom: 24 }}>
        <Steps
          current={TERM_STEPS.indexOf(term.status)}
          responsive
          items={TERM_STEPS.map((s) => ({ title: TERM_STATUS_LABEL[s], content: STEP_NOTE[s] }))}
        />
      </div>

      <div className="sc-card" style={{ padding: 24 }}>
        <Tabs
          destroyOnHidden
          items={[
            { key: 'overview', label: 'Tổng quan', children: <TermOverviewTab term={term} /> },
            { key: 'students', label: `Sinh viên trong đợt (${term.student_count})`, children: <TermStudentsTab term={term} /> },
            { key: 'jobs', label: 'Tin tuyển dụng thuộc đợt', children: <TermJobsTab term={term} /> },
            { key: 'results', label: 'Kết quả & đánh giá', children: <TermResultsTab term={term} /> },
          ]}
        />
      </div>

      <TermFormModal open={editing} term={term} onClose={() => setEditing(false)} />
    </>
  )
}
