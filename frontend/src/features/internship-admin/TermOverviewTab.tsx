/** Tab "Tổng quan": các số liệu lấy thật từ API (số sinh viên, kết quả theo trạng thái). Không có số liệu giả. */
import { Card, Col, Descriptions, Row, Statistic } from 'antd'
import { formatDate } from '@/lib/format'
import { useTermResults } from './api'
import type { Term } from './types'

export default function TermOverviewTab({ term }: { term: Term }) {
  // Chỉ cần tổng số nên lấy 1 dòng mỗi trạng thái
  const pending = useTermResults(term.id, { size: 1, result: 'PENDING' })
  const passed = useTermResults(term.id, { size: 1, result: 'PASSED' })
  const failed = useTermResults(term.id, { size: 1, result: 'FAILED' })

  return (
    <>
      <Row gutter={[16, 16]}>
        <Col xs={12} lg={6}>
          <Card>
            <Statistic title="Sinh viên tham gia" value={term.student_count} />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card>
            <Statistic title="Chờ kết quả" value={pending.data?.total ?? '—'} loading={pending.isLoading} />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card>
            <Statistic
              title="Đạt"
              value={passed.data?.total ?? '—'}
              loading={passed.isLoading}
              styles={{ content: { color: '#16A34A' } }}
            />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card>
            <Statistic
              title="Không đạt"
              value={failed.data?.total ?? '—'}
              loading={failed.isLoading}
              styles={{ content: { color: '#DC2626' } }}
            />
          </Card>
        </Col>
      </Row>
      <Descriptions bordered size="small" column={{ xs: 1, md: 2 }} style={{ marginTop: 24 }}>
        <Descriptions.Item label="Tên đợt">{term.name}</Descriptions.Item>
        <Descriptions.Item label="Năm học / học kỳ">
          {term.academic_year} · {term.semester}
        </Descriptions.Item>
        <Descriptions.Item label="Bắt đầu">{formatDate(term.start_date)}</Descriptions.Item>
        <Descriptions.Item label="Kết thúc">{formatDate(term.end_date)}</Descriptions.Item>
      </Descriptions>
    </>
  )
}
