import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import { DataResult, Panel, RecordTable } from '@/components/common/Workspace'
import { Pagination } from '@/components/common/Pagination'
import { statusLabel } from '@/features/administration/status'
import { companyApi } from './api'

export default function InvitationsPage() {
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: ['invitations', 'company', page],
    queryFn: () => companyApi.invitations(page),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Lời mời đã gửi"
        description="Theo dõi lời mời ứng tuyển được gửi cho sinh viên."
      />
      <Panel title="Danh sách lời mời">
        <DataResult query={query}>
          {(data) => (
            <>
              <RecordTable
                rows={data.items}
                columns={[
                  { key: 'id', label: 'Mã lời mời' },
                  {
                    key: 'job_id',
                    label: 'Tin tuyển dụng',
                    render: (row) => (
                      <Link to={'/company/candidates?job_id=' + row.job_id}>
                        Tin #{row.job_id}
                      </Link>
                    ),
                  },
                  { key: 'student_id', label: 'Mã sinh viên' },
                  {
                    key: 'status',
                    label: 'Trạng thái',
                    render: (row) => statusLabel(row.status),
                  },
                  { key: 'message', label: 'Lời nhắn' },
                  { key: 'created_at', label: 'Ngày gửi' },
                ]}
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
    </div>
  )
}
