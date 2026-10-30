/** Admin: import sinh viên từ Excel/CSV, xem báo cáo từng dòng và lịch sử các lần import. */
import { useState } from 'react'
import { App, Button, Card, Col, Drawer, Flex, Row, Spin, Table, Typography, Upload } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { ArrowLeftOutlined, DownloadOutlined, InboxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/ui/PageHeader'
import QueryError from '@/components/ui/QueryError'
import { getErrorMessage } from '@/lib/http'
import { formatDateTime } from '@/lib/format'
import { useImportDetail, useImports, useImportStudents } from './api'
import ImportReport from './ImportReport'
import { downloadTemplate, IMPORT_COLUMNS, validateImportFile } from './importTemplate'
import type { ImportBatch, ImportResult } from './types'

export default function StudentImportPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [page, setPage] = useState(1)
  const [detailId, setDetailId] = useState<number | null>(null)

  const importMutation = useImportStudents()
  const history = useImports({ page, size: 10, type: 'STUDENTS' })
  const detail = useImportDetail(detailId)

  const pick = (picked: File) => {
    const error = validateImportFile(picked)
    setFileError(error)
    setFile(error ? null : picked)
    setResult(null)
  }

  const submit = async () => {
    if (!file) return
    try {
      const data = await importMutation.mutateAsync(file)
      setResult(data)
      setFile(null)
      message.success('Đã xử lý file import')
    } catch (e) {
      // Lỗi toàn file (thiếu cột, sai định dạng): giữ nguyên file để người dùng sửa và thử lại
      message.error(getErrorMessage(e))
    }
  }

  const historyColumns: ColumnsType<ImportBatch> = [
    { title: 'Thời gian', dataIndex: 'created_at', render: formatDateTime },
    { title: 'Tên file', dataIndex: 'file_name', render: (v: string | null) => v ?? '—' },
    { title: 'Tổng dòng', dataIndex: 'total_rows', width: 100 },
    { title: 'Thành công', dataIndex: 'success_rows', width: 110 },
    {
      title: 'Lỗi',
      dataIndex: 'failed_rows',
      width: 80,
      render: (v: number) => <span style={{ color: v > 0 ? '#DC2626' : undefined, fontWeight: v > 0 ? 600 : 400 }}>{v}</span>,
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 120,
      render: (_, b) => (
        <Button size="small" onClick={() => setDetailId(b.id)}>
          Xem chi tiết
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="Phân hệ quản trị"
        title="Import sinh viên"
        subtitle="Tạo hoặc cập nhật sinh viên từ file Excel/CSV. Mỗi sinh viên mới nhận email kích hoạt tài khoản."
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/admin/students')}>
            Về danh sách sinh viên
          </Button>
        }
      />

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={10}>
          <Card title="Cột trong file" extra={<Button size="small" icon={<DownloadOutlined />} onClick={downloadTemplate}>Tải file mẫu</Button>}>
            <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
              Dòng đầu là tiêu đề cột. Chấp nhận cả tiêu đề tiếng Việt thông dụng (Mã sinh viên, Họ và tên, Khóa học...).
            </Typography.Paragraph>
            <Table
              size="small"
              rowKey="name"
              pagination={false}
              dataSource={[...IMPORT_COLUMNS]}
              columns={[
                { title: 'Cột', dataIndex: 'name', render: (n: string) => <code>{n}</code> },
                { title: 'Bắt buộc', dataIndex: 'required', width: 90, render: (r: boolean) => (r ? 'Có' : 'Không') },
                { title: 'Ghi chú', dataIndex: 'note' },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="Tải file lên">
            <Upload.Dragger
              accept=".xlsx,.csv"
              maxCount={1}
              fileList={file ? [{ uid: '1', name: file.name, status: 'done' }] : []}
              beforeUpload={(f) => {
                pick(f)
                return false
              }}
              onRemove={() => {
                setFile(null)
                setFileError(null)
              }}
              disabled={importMutation.isPending}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">Kéo thả file vào đây hoặc bấm để chọn</p>
              <p className="ant-upload-hint">Hỗ trợ .xlsx và .csv (UTF-8), tối đa 10MB</p>
            </Upload.Dragger>
            {fileError && (
              <Typography.Text type="danger" style={{ display: 'block', marginTop: 8 }}>
                {fileError}
              </Typography.Text>
            )}
            <Flex justify="flex-end" style={{ marginTop: 16 }}>
              <Button type="primary" disabled={!file} loading={importMutation.isPending} onClick={submit}>
                Import
              </Button>
            </Flex>
            {result && (
              <div style={{ marginTop: 24 }}>
                <ImportReport
                  batch={result.batch}
                  note={
                    result.activation_emails_queued > 0
                      ? `Đã xếp hàng gửi ${result.activation_emails_queued} email kích hoạt cho sinh viên mới.`
                      : undefined
                  }
                  successLabel="Đã lưu"
                />
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="Lịch sử import" style={{ marginTop: 24 }}>
        {history.isError && <QueryError error={history.error} onRetry={() => history.refetch()} />}
        <Table<ImportBatch>
          rowKey="id"
          loading={history.isFetching}
          columns={historyColumns}
          dataSource={history.data?.items ?? []}
          scroll={{ x: 'max-content' }}
          locale={{ emptyText: 'Chưa có lần import nào' }}
          pagination={{
            current: page,
            pageSize: 10,
            total: history.data?.total ?? 0,
            showSizeChanger: false,
            onChange: setPage,
          }}
        />
      </Card>

      <Drawer open={detailId !== null} onClose={() => setDetailId(null)} size={640} title="Chi tiết lần import" destroyOnHidden>
        {detail.isError && <QueryError error={detail.error} onRetry={() => detail.refetch()} />}
        <Spin spinning={detail.isFetching}>
          {detail.data && (
            <>
              <Typography.Paragraph>
                <b>{detail.data.file_name ?? 'Không rõ tên file'}</b> · {formatDateTime(detail.data.created_at)}
              </Typography.Paragraph>
              <ImportReport batch={detail.data} successLabel="Đã lưu" />
            </>
          )}
        </Spin>
      </Drawer>
    </>
  )
}
