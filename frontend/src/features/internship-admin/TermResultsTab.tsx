/** Tab "Kết quả & đánh giá": lọc theo kết quả/giảng viên, mở chi tiết để nhập nhận xét và xác nhận. */
import { useState } from 'react'
import { Button, Flex, Select, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import QueryError from '@/components/ui/QueryError'
import LecturerSelect from '@/features/lecturers/LecturerSelect'
import { formatScore } from '@/lib/format'
import { useTermResults } from './api'
import { ResultBadge } from './badges'
import ResultDrawer from './ResultDrawer'
import { isResultLocked, RESULT_LABEL } from './rules'
import type { InternshipResult, ResultStatus, Term } from './types'

export default function TermResultsTab({ term }: { term: Term }) {
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [result, setResult] = useState<ResultStatus | undefined>()
  const [lecturerId, setLecturerId] = useState<number | undefined>()
  const [openId, setOpenId] = useState<number | null>(null)

  const query = useTermResults(term.id, { page, size, result, lecturer_id: lecturerId })
  // Lấy dòng đang mở từ dữ liệu mới nhất để drawer tự cập nhật sau khi lưu/xác nhận
  const opened = query.data?.items.find((r) => r.id === openId) ?? null

  const columns: ColumnsType<InternshipResult> = [
    {
      title: 'Sinh viên',
      key: 'student',
      render: (_, r) => (
        <div>
          <div style={{ fontWeight: 600 }}>{r.student_name}</div>
          <div style={{ fontSize: 12, color: '#64748B' }}>{r.student_code}</div>
        </div>
      ),
    },
    { title: 'Giảng viên', dataIndex: 'lecturer_name', render: (v: string | null) => v ?? '—' },
    {
      title: 'Doanh nghiệp',
      dataIndex: 'company_name',
      render: (v: string | null) => v ?? <span style={{ color: '#94A3B8' }}>Chưa có</span>,
    },
    { title: 'Điểm DN', dataIndex: 'company_score', width: 90, render: formatScore },
    { title: 'Điểm trường', dataIndex: 'lecturer_score', width: 100, render: formatScore },
    { title: 'Kết quả', dataIndex: 'result', width: 150, render: (r: ResultStatus) => <ResultBadge result={r} /> },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 120,
      render: (_, r) => (
        <Button size="small" type={isResultLocked(r) ? 'default' : 'primary'} onClick={() => setOpenId(r.id)}>
          {isResultLocked(r) ? 'Xem' : 'Xử lý'}
        </Button>
      ),
    },
  ]

  return (
    <>
      <Flex gap={12} wrap align="center" style={{ marginBottom: 16 }}>
        <Select<ResultStatus>
          allowClear
          placeholder="Kết quả"
          style={{ width: 180 }}
          value={result}
          options={(Object.keys(RESULT_LABEL) as ResultStatus[]).map((k) => ({ value: k, label: RESULT_LABEL[k] }))}
          onChange={(v) => {
            setResult(v)
            setPage(1)
          }}
        />
        <LecturerSelect
          allowClear
          placeholder="Lọc theo giảng viên"
          style={{ width: 240 }}
          value={lecturerId}
          onChange={(v) => {
            setLecturerId(v)
            setPage(1)
          }}
        />
      </Flex>
      {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
      <Table<InternshipResult>
        rowKey="id"
        loading={query.isFetching}
        columns={columns}
        dataSource={query.data?.items ?? []}
        scroll={{ x: 'max-content' }}
        locale={{ emptyText: result || lecturerId ? 'Không có kết quả phù hợp bộ lọc' : 'Đợt chưa có sinh viên nên chưa có kết quả' }}
        pagination={{
          current: page,
          pageSize: size,
          total: query.data?.total ?? 0,
          showSizeChanger: true,
          showTotal: (total) => `${total} sinh viên`,
          onChange: (p, s) => {
            setPage(p)
            setSize(s)
          },
        }}
      />
      <ResultDrawer result={opened} onClose={() => setOpenId(null)} />
    </>
  )
}
