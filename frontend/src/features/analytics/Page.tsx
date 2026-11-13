import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  ArrowUpRight,
  BarChart3,
  BriefcaseBusiness,
  Building2,
  CircleDollarSign,
  Clock3,
  FolderCheck,
  FolderKanban,
  Gavel,
  GraduationCap,
  Landmark,
  Users,
  UserCheck,
  WalletCards,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import {
  CatalogSelect,
  DataResult,
  Notice,
  Panel,
  RecordTable,
} from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import type { Row } from '@/components/common/Workspace'
import { Pagination } from '@/components/common/Pagination'
import { Button } from '@/components/ui/Button'
import { http } from '@/lib/http'
import { downloadFile } from '@/utils/download'
import type { Page } from '@/types/api'
import './analytics.css'

type FreelancerOverview = {
  platform_fee_revenue: number
  disbursed_amount: number
  total_projects: number
  pending_review_projects: number
  recruiting_projects: number
  in_progress_projects: number
  completed_projects: number
  open_disputes: number
  pending_payouts: number
}

const formatVnd = (value: number) =>
  new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(value)

const sections = {
  breakdown: {
    title: 'Phân bố sinh viên',
    columns: [
      ['group', 'Nhóm'],
      ['count', 'Sinh viên'],
    ],
  },
  'top-skills': {
    title: 'Kỹ năng được yêu cầu',
    columns: [
      ['name', 'Kỹ năng'],
      ['required_jobs', 'Tin yêu cầu'],
    ],
  },
  'skill-gap': {
    title: 'Khoảng thiếu kỹ năng',
    columns: [
      ['name', 'Kỹ năng'],
      ['required_jobs', 'Tin yêu cầu'],
      ['students_with_skill', 'Sinh viên có kỹ năng'],
      ['students_missing_skill', 'Sinh viên còn thiếu'],
    ],
  },
  'match-rate': {
    title: 'Mức phù hợp theo ngành',
    columns: [
      ['major_name', 'Ngành'],
      ['students', 'Sinh viên'],
      ['matched_students', 'Sinh viên đáp ứng'],
      ['match_rate', 'Tỷ lệ (%)'],
      ['average_score', 'Điểm trung bình'],
    ],
  },
  trends: {
    title: 'Xu hướng theo ngày',
    columns: [
      ['period', 'Ngày'],
      ['jobs', 'Tin tuyển dụng'],
      ['applications', 'Đơn ứng tuyển'],
    ],
  },
}
function GroupName({ group, groupBy }: { group: unknown; groupBy: string }) {
  const id = Number(group)
  const resource =
    groupBy === 'faculty' ? '/catalog/faculties/' : '/catalog/majors/'
  const query = useQuery({
    queryKey: ['analytics-group', resource, id],
    queryFn: () => getData<{ name: string }>(resource + id),
    enabled: groupBy !== 'cohort' && id > 0,
  })
  return (
    <>
      {groupBy === 'cohort'
        ? String(group)
        : query.data?.name ||
          (id > 0 ? 'Mã #' + id : String(group || 'Chưa xác định'))}
    </>
  )
}
function DataChart({
  section,
  rows,
}: {
  section: keyof typeof sections
  rows: Row[]
}) {
  const valueKey =
    section === 'top-skills'
      ? 'required_jobs'
      : section === 'match-rate'
        ? 'match_rate'
        : section === 'trends'
          ? 'applications'
          : ''
  if (!valueKey || !rows.length) return null
  const maximum =
    section === 'match-rate'
      ? 100
      : Math.max(1, ...rows.map((row) => Number(row[valueKey])))
  return (
    <div className="ws-chart" aria-label="Biểu đồ dữ liệu trên trang hiện tại">
      {rows.map((row, index) => {
        const value = Number(row[valueKey])
        return (
          <div className="ws-chart-row" key={index}>
            <div className="ws-chart-label">
              <span>{String(row.name || row.major_name || row.period)}</span>
              <strong>
                {value}
                {section === 'match-rate' ? '%' : ''}
              </strong>
            </div>
            <div className="ws-bar" aria-hidden="true">
              <span
                style={{ width: Math.min(100, (100 * value) / maximum) + '%' }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
function AnalyticsTable({
  section,
  filters,
}: {
  section: keyof typeof sections
  filters: Record<string, string>
}) {
  const [page, setPage] = useState(1)
  const cfg = sections[section]
  const query = useQuery({
    queryKey: ['analytics', section, filters, page],
    queryFn: () =>
      getData<Page<Row>>('/admin/dashboard/' + section, {
        ...filters,
        page,
        size: 10,
      }),
  })
  return (
    <Panel title={cfg.title}>
      <DataResult query={query}>
        {(data) => (
          <>
            <DataChart section={section} rows={data.items} />
            <RecordTable
              rows={data.items}
              columns={cfg.columns.map(([key, label]) => ({
                key,
                label,
                render: (row: Row) =>
                  key === 'group' ? (
                    <GroupName group={row[key]} groupBy={filters.group_by} />
                  ) : key === 'match_rate' || key === 'average_score' ? (
                    Number(row[key]).toFixed(1)
                  ) : (
                    String(row[key] ?? '—')
                  ),
              }))}
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
  )
}
export default function AnalyticsPage() {
  const [filters, setFilters] = useState<Record<string, string>>({
      group_by: 'major',
    }),
    [draft, setDraft] = useState(filters),
    [exportType, setExportType] = useState('dashboard.pdf'),
    [filterError, setFilterError] = useState('')
  const overview = useQuery({
    queryKey: ['analytics', 'overview', filters],
    queryFn: () =>
      getData<Record<string, number>>('/admin/dashboard/overview', filters),
  })
  const freelancerOverview = useQuery({
    queryKey: ['analytics', 'freelancer-overview', filters],
    queryFn: () =>
      getData<FreelancerOverview>(
        '/admin/dashboard/freelancer-overview',
        filters,
      ),
  })
  const recompute = useMutation({
    mutationFn: () => http.post('/matching/recompute'),
  })
  const download = useMutation({
    mutationFn: () =>
      downloadFile(
        '/api/v1/admin/exports/' +
          exportType +
          '?' +
          new URLSearchParams(filters),
        exportType,
      ),
  })
  const update = (key: string, value: string) =>
    setDraft({ ...draft, [key]: value })
  const cards = [
    { key: 'students', label: 'Sinh viên', icon: GraduationCap },
    { key: 'companies', label: 'Doanh nghiệp', icon: Building2 },
    { key: 'jobs', label: 'Tin tuyển dụng', icon: BriefcaseBusiness },
    { key: 'applications', label: 'Đơn ứng tuyển', icon: Users },
    { key: 'interviews', label: 'Đang phỏng vấn', icon: BarChart3 },
    { key: 'hired', label: 'Đã tuyển', icon: UserCheck },
  ]
  const freelancerOperations = [
    {
      key: 'pending_review_projects',
      label: 'Chờ duyệt',
      description: 'Dự án cần admin kiểm tra',
      icon: Clock3,
      href: '/admin/freelancer/admin/projects',
      tone: 'warning',
    },
    {
      key: 'recruiting_projects',
      label: 'Đang tuyển sinh viên',
      description: 'Dự án đã duyệt và đang mở',
      icon: Users,
      href: '/admin/freelancer/admin/projects',
      tone: 'info',
    },
    {
      key: 'in_progress_projects',
      label: 'Đang thực hiện',
      description: 'Dự án đang triển khai',
      icon: FolderKanban,
      href: '/admin/freelancer/admin/projects',
      tone: 'neutral',
    },
    {
      key: 'completed_projects',
      label: 'Đã hoàn thành',
      description: 'Dự án hoàn thành hoặc đã đóng',
      icon: FolderCheck,
      href: '/admin/freelancer/admin/projects',
      tone: 'success',
    },
    {
      key: 'open_disputes',
      label: 'Tranh chấp đang mở',
      description: 'Hồ sơ cần theo dõi, xử lý',
      icon: Gavel,
      href: '/admin/freelancer/admin/disputes',
      tone: 'danger',
    },
    {
      key: 'pending_payouts',
      label: 'Lệnh chi đang xử lý',
      description: 'Chờ ngân hàng, đang xử lý hoặc cần xác minh',
      icon: WalletCards,
      href: '/admin/freelancer/admin/transfers',
      tone: 'warning',
    },
  ] as const
  return (
    <div className="workspace">
      <PageHeader
        title="Phân tích & báo cáo"
        description="Theo dõi dữ liệu tuyển dụng và nguồn nhân lực của nhà trường."
      />
      <Panel title="Phạm vi thống kê">
        <form
          className="ws-filters"
          onSubmit={(e) => {
            e.preventDefault()
            if (
              draft.date_from &&
              draft.date_to &&
              draft.date_from > draft.date_to
            ) {
              setFilterError('Ngày bắt đầu phải trước ngày kết thúc.')
              return
            }
            setFilterError('')
            setFilters(
              Object.fromEntries(Object.entries(draft).filter(([, v]) => v)),
            )
          }}
        >
          <label>
            Từ ngày
            <input
              type="date"
              value={draft.date_from || ''}
              onChange={(e) => update('date_from', e.target.value)}
            />
          </label>
          <label>
            Đến ngày
            <input
              type="date"
              value={draft.date_to || ''}
              onChange={(e) => update('date_to', e.target.value)}
            />
          </label>
          <CatalogSelect
            resource="faculties"
            label="Khoa"
            name="faculty_id"
            value={draft.faculty_id || ''}
            onChange={(v) => update('faculty_id', v)}
          />
          <CatalogSelect
            resource="majors"
            label="Ngành"
            name="major_id"
            value={draft.major_id || ''}
            onChange={(v) => update('major_id', v)}
          />
          <label>
            Khóa học
            <input
              value={draft.cohort || ''}
              onChange={(e) => update('cohort', e.target.value)}
            />
          </label>
          <label>
            Phân nhóm
            <select
              value={draft.group_by}
              onChange={(e) => update('group_by', e.target.value)}
            >
              {[
                ['major', 'Ngành'],
                ['faculty', 'Khoa'],
                ['cohort', 'Khóa'],
              ].map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <Button type="submit">Áp dụng bộ lọc</Button>
        </form>
        {filterError && (
          <p role="alert" className="ws-error">
            {filterError}
          </p>
        )}
        <p className="muted">
          Khoảng ngày được backend áp dụng theo từng chỉ số. Tỷ lệ phù hợp dùng
          kết quả matching đã lưu, chỉ mang tính tham khảo.
        </p>
      </Panel>
      <section className="analytics-freelancer" aria-labelledby="freelancer-title">
        <div className="analytics-section-heading">
          <div>
            <p className="analytics-eyebrow">VẬN HÀNH FREELANCER</p>
            <h2 id="freelancer-title">Tài chính và công việc cần quan tâm</h2>
            <p>
              Doanh thu và tiền đã chi theo khoảng ngày đã chọn. Các hàng đợi
              phản ánh trạng thái hiện tại của hệ thống.
            </p>
          </div>
          <span className="analytics-project-total">
            <FolderKanban size={17} />
            <strong>
              {freelancerOverview.data?.total_projects.toLocaleString('vi-VN') ?? '—'}
            </strong>
            dự án
          </span>
        </div>
        <DataResult query={freelancerOverview}>
          {(data) => (
            <>
              <div className="analytics-finance-grid">
                <article className="analytics-finance-card analytics-finance-card--revenue">
                  <div className="analytics-finance-icon">
                    <CircleDollarSign size={25} />
                  </div>
                  <div>
                    <p>Doanh thu phí nền tảng</p>
                    <strong>{formatVnd(data.platform_fee_revenue)}</strong>
                    <span>
                      Phí 5% đã ghi nhận từ các lần giải ngân thành công
                    </span>
                  </div>
                </article>
                <article className="analytics-finance-card analytics-finance-card--payout">
                  <div className="analytics-finance-icon">
                    <Landmark size={25} />
                  </div>
                  <div>
                    <p>Đã giải ngân cho sinh viên</p>
                    <strong>{formatVnd(data.disbursed_amount)}</strong>
                    <span>Tổng tiền thực chuyển thành công trong kỳ</span>
                  </div>
                </article>
              </div>
              <div className="analytics-operations-grid">
                {freelancerOperations.map((item) => {
                  const Icon = item.icon
                  return (
                    <Link
                      className={`analytics-operation-card analytics-operation-card--${item.tone}`}
                      key={item.key}
                      to={item.href}
                    >
                      <div className="analytics-operation-top">
                        <span className="analytics-operation-icon">
                          <Icon size={20} />
                        </span>
                        <ArrowUpRight size={17} aria-hidden="true" />
                      </div>
                      <strong>{data[item.key].toLocaleString('vi-VN')}</strong>
                      <h3>{item.label}</h3>
                      <p>{item.description}</p>
                    </Link>
                  )
                })}
              </div>
            </>
          )}
        </DataResult>
      </section>
      <div className="analytics-section-heading analytics-section-heading--compact">
        <div>
          <p className="analytics-eyebrow">TUYỂN DỤNG & NGUỒN NHÂN LỰC</p>
          <h2>Tổng quan kết nối việc làm</h2>
        </div>
      </div>
      <DataResult query={overview}>
        {(data) => (
          <div className="ws-cards">
            {cards.map((card) => (
              <article className="ws-card" key={card.key}>
                <card.icon size={22} />
                <p>{card.label}</p>
                <strong className="ws-number">
                  {data[card.key].toLocaleString('vi-VN')}
                </strong>
              </article>
            ))}
          </div>
        )}
      </DataResult>
      <Panel title="Xuất báo cáo & cập nhật matching">
        <div className="ws-filters">
          <label>
            Loại báo cáo
            <select
              value={exportType}
              onChange={(e) => setExportType(e.target.value)}
            >
              {[
                ['dashboard.pdf', 'Tổng quan PDF'],
                ['students.xlsx', 'Sinh viên Excel'],
                ['companies.xlsx', 'Doanh nghiệp Excel'],
                ['jobs.xlsx', 'Tin tuyển dụng Excel'],
                ['applications.xlsx', 'Đơn ứng tuyển Excel'],
                ['skill-report.xlsx', 'Kỹ năng Excel'],
              ].map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <Button
            pending={download.isPending}
            onClick={() => download.mutate()}
          >
            Tải báo cáo
          </Button>
          <Button
            variant="secondary"
            pending={recompute.isPending}
            onClick={() => {
              if (window.confirm('Xếp hàng tính lại matching?'))
                recompute.mutate()
            }}
          >
            Tính lại matching
          </Button>
        </div>
        <Notice
          error={download.error || recompute.error}
          success={
            recompute.isSuccess
              ? 'Đã xếp hàng tính lại matching. Backend chưa cung cấp tiến độ xử lý.'
              : undefined
          }
        />
      </Panel>
      <div className="ws-grid">
        {(Object.keys(sections) as (keyof typeof sections)[]).map((section) => (
          <AnalyticsTable
            key={section + JSON.stringify(filters)}
            section={section}
            filters={filters}
          />
        ))}
      </div>
    </div>
  )
}
