/** Admin: danh sách sinh viên (dữ liệu chính thức của trường) với bộ lọc và phân trang. */
import { useState } from 'react'
import { Button, Flex, Input, Select, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { UploadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/ui/PageHeader'
import QueryError from '@/components/ui/QueryError'
import { FacultySelect, MajorSelect } from '@/features/catalog/selectors'
import { useDebounced } from '@/lib/useDebounced'
import { useStudents } from './api'
import { ACCOUNT_STATUS_OPTIONS, AccountStatusBadge } from './labels'
import type { AccountStatus, AdminStudent } from './types'

export default function StudentListPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [search, setSearch] = useState('')
  const [cohort, setCohort] = useState('')
  const [facultyId, setFacultyId] = useState<number | undefined>()
  const [majorId, setMajorId] = useState<number | undefined>()
  const [status, setStatus] = useState<AccountStatus | undefined>()
  const q = useDebounced(search)
  const cohortFilter = useDebounced(cohort)

  const query = useStudents({
    page,
    size,
    q,
    cohort: cohortFilter.trim(),
    faculty_id: facultyId,
    major_id: majorId,
    account_status: status,
  })

  const hasFilter = Boolean(q || cohortFilter || facultyId || majorId || status)
  const reset = () => setPage(1)

  const columns: ColumnsType<AdminStudent> = [
    { title: 'Mã SV', dataIndex: 'student_code', width: 120 },
    {
      title: 'Họ và tên',
      dataIndex: 'full_name',
      render: (name: string, s) => (
        <div>
          <div style={{ fontWeight: 600 }}>{name}</div>
          <div style={{ fontSize: 12, color: '#64748B' }}>{s.email}</div>
        </div>
      ),
    },
    { title: 'Khoa', dataIndex: 'faculty_name' },
    { title: 'Ngành', dataIndex: 'major_name' },
    { title: 'Khóa', dataIndex: 'cohort', width: 90 },
    { title: 'GPA', dataIndex: 'gpa', width: 80, render: (v: string | null) => v ?? '—' },
    {
      title: 'Tài khoản',
      dataIndex: 'account_status',
      width: 150,
      render: (s: AccountStatus) => <AccountStatusBadge status={s} />,
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 110,
      render: (_, s) => (
        <Button size="small" onClick={() => navigate(`/admin/students/${s.id}`)}>
          Xem chi tiết
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="Phân hệ quản trị"
        title="Quản lý sinh viên"
        subtitle="Tài khoản sinh viên được nhà trường tạo qua import; sinh viên không tự đăng ký."
        extra={
          <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/admin/students/import')}>
            Import sinh viên
          </Button>
        }
      />
      <div className="sc-card" style={{ padding: 24 }}>
        <Flex gap={12} wrap align="center" style={{ marginBottom: 16 }}>
          <Input.Search
            allowClear
            placeholder="Tìm theo tên, mã hoặc email"
            style={{ width: 280 }}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              reset()
            }}
          />
          <FacultySelect
            allowClear
            placeholder="Khoa"
            style={{ width: 220 }}
            value={facultyId}
            onChange={(v) => {
              setFacultyId(v)
              setMajorId(undefined)
              reset()
            }}
          />
          <MajorSelect
            allowClear
            placeholder="Ngành"
            style={{ width: 220 }}
            facultyId={facultyId}
            value={majorId}
            onChange={(v) => {
              setMajorId(v)
              reset()
            }}
          />
          <Input
            allowClear
            placeholder="Khóa (vd K65)"
            style={{ width: 140 }}
            value={cohort}
            onChange={(e) => {
              setCohort(e.target.value)
              reset()
            }}
          />
          <Select<AccountStatus>
            allowClear
            placeholder="Trạng thái tài khoản"
            style={{ width: 190 }}
            options={ACCOUNT_STATUS_OPTIONS}
            value={status}
            onChange={(v) => {
              setStatus(v)
              reset()
            }}
          />
        </Flex>

        {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
        <Table<AdminStudent>
          rowKey="id"
          loading={query.isFetching}
          columns={columns}
          dataSource={query.data?.items ?? []}
          scroll={{ x: 'max-content' }}
          locale={{
            emptyText: hasFilter ? 'Không có sinh viên phù hợp bộ lọc' : 'Chưa có sinh viên. Hãy import danh sách từ file Excel/CSV.',
          }}
          onRow={(s) => ({ onClick: () => navigate(`/admin/students/${s.id}`), style: { cursor: 'pointer' } })}
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
      </div>
    </>
  )
}
