/** Admin: danh sách đợt thực tập, lọc theo năm học/học kỳ/trạng thái, tạo đợt mới. */
import { useState } from 'react'
import { Button, Flex, Input, Select, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/features/school-shared/components/PageHeader'
import QueryError from '@/features/school-shared/components/QueryError'
import { formatDate } from '@/features/school-shared/format'
import { useDebounced } from '@/features/school-shared/useDebounced'
import { useTerms } from './api'
import { TermStatusBadge } from './badges'
import { TERM_STATUS_LABEL, TERM_STEPS } from './rules'
import TermFormModal from './TermFormModal'
import type { Term, TermStatus } from './types'

export default function TermListPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [year, setYear] = useState('')
  const [semester, setSemester] = useState('')
  const [status, setStatus] = useState<TermStatus | undefined>()
  const [creating, setCreating] = useState(false)
  const yearFilter = useDebounced(year).trim()
  const semesterFilter = useDebounced(semester).trim()

  const query = useTerms({ page, size, academic_year: yearFilter, semester: semesterFilter, status })
  const hasFilter = Boolean(yearFilter || semesterFilter || status)

  const columns: ColumnsType<Term> = [
    { title: 'Tên đợt', dataIndex: 'name', render: (n: string) => <span style={{ fontWeight: 600 }}>{n}</span> },
    { title: 'Năm học', dataIndex: 'academic_year', width: 120 },
    { title: 'Học kỳ', dataIndex: 'semester', width: 90 },
    {
      title: 'Thời gian',
      key: 'period',
      render: (_, t) => `${formatDate(t.start_date)} - ${formatDate(t.end_date)}`,
    },
    { title: 'Sinh viên', dataIndex: 'student_count', width: 100 },
    { title: 'Trạng thái', dataIndex: 'status', width: 170, render: (s: TermStatus) => <TermStatusBadge status={s} /> },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 110,
      render: (_, t) => (
        <Button size="small" onClick={() => navigate(`/admin/internships/${t.id}`)}>
          Xem chi tiết
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="Phân hệ quản trị"
        title="Đợt thực tập"
        subtitle="Quản lý các đợt thực tập, sinh viên tham gia, phân công giảng viên và kết quả."
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreating(true)}>
            Tạo đợt thực tập
          </Button>
        }
      />
      <div className="sc-card" style={{ padding: 24 }}>
        <Flex gap={12} wrap align="center" style={{ marginBottom: 16 }}>
          <Input
            allowClear
            placeholder="Năm học (vd 2025-2026)"
            style={{ width: 220 }}
            value={year}
            onChange={(e) => {
              setYear(e.target.value)
              setPage(1)
            }}
          />
          <Input
            allowClear
            placeholder="Học kỳ (vd HK1)"
            style={{ width: 160 }}
            value={semester}
            onChange={(e) => {
              setSemester(e.target.value)
              setPage(1)
            }}
          />
          <Select<TermStatus>
            allowClear
            placeholder="Trạng thái"
            style={{ width: 190 }}
            value={status}
            options={TERM_STEPS.map((s) => ({ value: s, label: TERM_STATUS_LABEL[s] }))}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
          />
        </Flex>
        {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
        <Table<Term>
          rowKey="id"
          loading={query.isFetching}
          columns={columns}
          dataSource={query.data?.items ?? []}
          scroll={{ x: 'max-content' }}
          locale={{ emptyText: hasFilter ? 'Không có đợt phù hợp bộ lọc' : 'Chưa có đợt thực tập nào. Hãy tạo đợt đầu tiên.' }}
          onRow={(t) => ({ onClick: () => navigate(`/admin/internships/${t.id}`), style: { cursor: 'pointer' } })}
          pagination={{
            current: page,
            pageSize: size,
            total: query.data?.total ?? 0,
            showSizeChanger: true,
            showTotal: (total) => `${total} đợt`,
            onChange: (p, s) => {
              setPage(p)
              setSize(s)
            },
          }}
        />
      </div>
      <TermFormModal
        open={creating}
        onClose={() => setCreating(false)}
        onSaved={(t) => navigate(`/admin/internships/${t.id}`)}
      />
    </>
  )
}
