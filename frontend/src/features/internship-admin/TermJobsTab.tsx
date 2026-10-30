/** Tab "Tin tuyển dụng thuộc đợt": danh sách tin gắn với đợt (admin thấy mọi trạng thái). */
import { useState } from 'react'
import { Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import QueryError from '@/features/school-shared/components/QueryError'
import { formatDate } from '@/features/school-shared/format'
import { useTermJobs } from './api'
import { JobStatusBadge } from './badges'
import type { JobStatus, Term, TermJob } from './types'

export default function TermJobsTab({ term }: { term: Term }) {
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const query = useTermJobs(term.id, { page, size })

  const columns: ColumnsType<TermJob> = [
    {
      title: 'Tin tuyển dụng',
      dataIndex: 'title',
      render: (title: string, j) => (
        <div>
          <div style={{ fontWeight: 600 }}>{title}</div>
          <div style={{ fontSize: 12, color: '#64748B' }}>{j.position}</div>
        </div>
      ),
    },
    { title: 'Doanh nghiệp', dataIndex: 'company_name' },
    { title: 'Số lượng', dataIndex: 'quantity', width: 100 },
    { title: 'Hạn nộp', dataIndex: 'deadline', width: 120, render: formatDate },
    { title: 'Trạng thái', dataIndex: 'status', width: 140, render: (s: JobStatus) => <JobStatusBadge status={s} /> },
  ]

  return (
    <>
      {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
      <Table<TermJob>
        rowKey="id"
        loading={query.isFetching}
        columns={columns}
        dataSource={query.data?.items ?? []}
        scroll={{ x: 'max-content' }}
        locale={{ emptyText: 'Chưa có tin tuyển dụng nào thuộc đợt này' }}
        pagination={{
          current: page,
          pageSize: size,
          total: query.data?.total ?? 0,
          showSizeChanger: true,
          showTotal: (total) => `${total} tin`,
          onChange: (p, s) => {
            setPage(p)
            setSize(s)
          },
        }}
      />
    </>
  )
}
