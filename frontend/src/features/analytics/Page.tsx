import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  GraduationCap,
  Users,
  UserCheck,
} from 'lucide-react'
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
  'flow-comparison': {
    title: 'So sánh luồng tuyển dụng',
    columns: [
      ['flow', 'Luồng'],
      ['jobs', 'Tin tuyển dụng'],
      ['applications', 'Đơn ứng tuyển'],
      ['hired', 'Đã tuyển'],
    ],
  },
}
function GroupName({ group, groupBy }: { group: unknown; groupBy: string }) {
  const id = Number(group)
  const resource =
    groupBy === 'faculty'
      ? '/catalog/faculties/'
      : groupBy === 'major'
        ? '/catalog/majors/'
        : '/internship-terms/'
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
                  ) : key === 'flow' ? (
                    row[key] === 'free' ? (
                      'Tự do'
                    ) : (
                      'Theo đợt'
                    )
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
            Mã đợt thực tập
            <input
              type="number"
              min="1"
              value={draft.term_id || ''}
              onChange={(e) => update('term_id', e.target.value)}
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
                ['term', 'Đợt'],
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
