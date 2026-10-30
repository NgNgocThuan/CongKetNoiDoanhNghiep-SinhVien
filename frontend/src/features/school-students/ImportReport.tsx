/**
 * Báo cáo kết quả một lần import (dùng cho import sinh viên và import danh sách sinh viên của đợt).
 * Hiển thị tổng số dòng, thành công, thất bại và bảng lỗi theo số dòng; dòng thành công không bị che bởi lỗi.
 */
import { Alert, Col, Row, Statistic, Table } from 'antd'
import type { ImportBatchDetail, ImportRowError } from './types'

export default function ImportReport({
  batch,
  note,
  successLabel = 'Thành công',
}: {
  batch: ImportBatchDetail
  note?: string
  successLabel?: string
}) {
  const allFailed = batch.failed_rows > 0 && batch.success_rows === 0
  return (
    <div>
      <Alert
        type={batch.failed_rows === 0 ? 'success' : allFailed ? 'error' : 'warning'}
        showIcon
        title={
          batch.failed_rows === 0
            ? `Import thành công toàn bộ ${batch.total_rows} dòng`
            : allFailed
              ? `Không có dòng nào được import (${batch.failed_rows}/${batch.total_rows} dòng lỗi)`
              : `${batch.success_rows} dòng đã được lưu, ${batch.failed_rows} dòng bị bỏ qua do lỗi`
        }
        description={
          [note, batch.failed_rows > 0 ? 'Các dòng lỗi không làm ảnh hưởng đến các dòng đã lưu. Sửa file rồi import lại các dòng lỗi.' : null]
            .filter(Boolean)
            .join(' ') || undefined
        }
        style={{ marginBottom: 16 }}
      />
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={8}>
          <Statistic title="Tổng số dòng" value={batch.total_rows} />
        </Col>
        <Col xs={8}>
          <Statistic title={successLabel} value={batch.success_rows} styles={{ content: { color: '#16A34A' } }} />
        </Col>
        <Col xs={8}>
          <Statistic
            title="Dòng lỗi"
            value={batch.failed_rows}
            styles={{ content: { color: batch.failed_rows > 0 ? '#DC2626' : undefined } }}
          />
        </Col>
      </Row>
      {batch.errors.length > 0 && (
        <Table<ImportRowError>
          size="small"
          rowKey={(r) => `${r.row}-${r.key ?? ''}`}
          dataSource={batch.errors}
          scroll={{ x: 'max-content' }}
          pagination={batch.errors.length > 10 ? { pageSize: 10, showSizeChanger: false } : false}
          columns={[
            { title: 'Dòng', dataIndex: 'row', width: 80 },
            { title: 'Mã sinh viên', dataIndex: 'key', width: 150, render: (v: string | null) => v ?? '—' },
            { title: 'Lý do lỗi', dataIndex: 'message' },
          ]}
        />
      )}
    </div>
  )
}
