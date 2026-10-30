/**
 * Tab "Sinh viên trong đợt": danh sách, thêm (chọn) / import theo mã, xóa, phân công giảng viên hàng loạt.
 * Khi đợt đã đóng, mọi thao tác thay đổi bị ẩn.
 */
import { useState } from 'react'
import { Alert, App, Button, Flex, Input, Modal, Popconfirm, Select, Table, Typography, Upload } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { InboxOutlined, PlusOutlined, TeamOutlined, UploadOutlined } from '@ant-design/icons'
import QueryError from '@/components/ui/QueryError'
import LecturerSelect from '@/features/lecturers/LecturerSelect'
import { useStudents } from '@/features/school-students/api'
import ImportReport from '@/features/school-students/ImportReport'
import { validateImportFile } from '@/features/school-students/importTemplate'
import { getErrorMessage } from '@/lib/http'
import { useDebounced } from '@/lib/useDebounced'
import { useAddTermStudents, useAssignLecturers, useImportTermStudents, useRemoveTermStudent, useTermStudents } from './api'
import { isTermEditable } from './rules'
import type { Term, TermImportResult, TermStudent } from './types'

/** Ô chọn nhiều sinh viên: gõ để tìm theo mã/tên/email. Giá trị giữ cả nhãn để hiển thị lại. */
function StudentPicker({
  value,
  onChange,
}: {
  value: { value: number; label: string }[]
  onChange: (v: { value: number; label: string }[]) => void
}) {
  const [text, setText] = useState('')
  const q = useDebounced(text)
  const { data, isFetching } = useStudents({ q: q.trim(), size: 20 })
  return (
    <Select
      mode="multiple"
      labelInValue
      filterOption={false}
      value={value}
      onChange={onChange}
      onSearch={setText}
      loading={isFetching}
      style={{ width: '100%' }}
      placeholder="Gõ mã, tên hoặc email sinh viên để tìm"
      notFoundContent={q ? 'Không tìm thấy sinh viên' : 'Nhập từ khóa để tìm'}
      options={data?.items.map((s) => ({ value: s.id, label: `${s.student_code} - ${s.full_name}` }))}
    />
  )
}

function AddStudentsModal({ term, open, onClose }: { term: Term; open: boolean; onClose: () => void }) {
  const { message } = App.useApp()
  const [picked, setPicked] = useState<{ value: number; label: string }[]>([])
  const add = useAddTermStudents(term.id)

  const close = () => {
    setPicked([])
    onClose()
  }

  const submit = async () => {
    try {
      const r = await add.mutateAsync(picked.map((p) => p.value))
      const parts = [`Đã thêm ${r.added} sinh viên`]
      if (r.already_in_term) parts.push(`${r.already_in_term} sinh viên đã có trong đợt`)
      if (r.not_found_ids.length) parts.push(`${r.not_found_ids.length} sinh viên không tồn tại`)
      message.success(parts.join(', '))
      close()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Modal
      open={open}
      title="Thêm sinh viên vào đợt"
      okText={`Thêm ${picked.length || ''} sinh viên`.trim()}
      cancelText="Hủy"
      okButtonProps={{ disabled: picked.length === 0 }}
      confirmLoading={add.isPending}
      onOk={submit}
      onCancel={close}
      destroyOnHidden
    >
      <StudentPicker value={picked} onChange={setPicked} />
      <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
        Mỗi sinh viên được thêm sẽ nhận thông báo trong hệ thống.
      </Typography.Paragraph>
    </Modal>
  )
}

function ImportModal({ term, open, onClose }: { term: Term; open: boolean; onClose: () => void }) {
  const { message } = App.useApp()
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [result, setResult] = useState<TermImportResult | null>(null)
  const importMutation = useImportTermStudents(term.id)

  const close = () => {
    setFile(null)
    setFileError(null)
    setResult(null)
    onClose()
  }

  const submit = async () => {
    if (!file) return
    try {
      setResult(await importMutation.mutateAsync(file))
      setFile(null)
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Modal
      open={open}
      title="Import sinh viên vào đợt theo mã sinh viên"
      width={640}
      footer={
        result ? (
          <Button type="primary" onClick={close}>
            Đóng
          </Button>
        ) : (
          <Flex justify="flex-end" gap={8}>
            <Button onClick={close}>Hủy</Button>
            <Button type="primary" disabled={!file} loading={importMutation.isPending} onClick={submit}>
              Import
            </Button>
          </Flex>
        )
      }
      onCancel={close}
      destroyOnHidden
    >
      {result ? (
        <ImportReport batch={result.batch} successLabel="Đã thêm vào đợt" />
      ) : (
        <>
          <Typography.Paragraph type="secondary">
            File .xlsx hoặc .csv có cột <code>student_code</code> (mã sinh viên). Sinh viên phải đã tồn tại trong hệ thống.
          </Typography.Paragraph>
          <Upload.Dragger
            accept=".xlsx,.csv"
            maxCount={1}
            fileList={file ? [{ uid: '1', name: file.name, status: 'done' }] : []}
            beforeUpload={(f) => {
              const error = validateImportFile(f)
              setFileError(error)
              setFile(error ? null : f)
              return false
            }}
            onRemove={() => {
              setFile(null)
              setFileError(null)
            }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Kéo thả file vào đây hoặc bấm để chọn</p>
          </Upload.Dragger>
          {fileError && (
            <Typography.Text type="danger" style={{ display: 'block', marginTop: 8 }}>
              {fileError}
            </Typography.Text>
          )}
        </>
      )}
    </Modal>
  )
}

function AssignModal({
  term,
  studentIds,
  open,
  onClose,
  onDone,
}: {
  term: Term
  studentIds: number[]
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const { message } = App.useApp()
  const [lecturerId, setLecturerId] = useState<number | undefined>()
  const assign = useAssignLecturers(term.id)

  const close = () => {
    setLecturerId(undefined)
    onClose()
  }

  const submit = async () => {
    try {
      const r = await assign.mutateAsync({ lecturer_id: lecturerId ?? null, student_ids: studentIds })
      message.success(
        lecturerId === undefined ? `Đã bỏ phân công cho ${r.updated} sinh viên` : `Đã phân công cho ${r.updated} sinh viên`,
      )
      onDone()
      close()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Modal
      open={open}
      title="Phân công giảng viên hướng dẫn"
      okText={lecturerId === undefined ? 'Bỏ phân công' : 'Phân công'}
      okButtonProps={{ danger: lecturerId === undefined }}
      cancelText="Hủy"
      confirmLoading={assign.isPending}
      onOk={submit}
      onCancel={close}
      destroyOnHidden
    >
      <Typography.Paragraph>
        Áp dụng cho <b>{studentIds.length}</b> sinh viên đã chọn.
      </Typography.Paragraph>
      <LecturerSelect allowClear style={{ width: '100%' }} value={lecturerId} onChange={setLecturerId} />
      {lecturerId === undefined && (
        <Alert
          type="warning"
          showIcon
          title="Chưa chọn giảng viên: thao tác này sẽ BỎ phân công giảng viên của các sinh viên đã chọn."
          style={{ marginTop: 12 }}
        />
      )}
    </Modal>
  )
}

export default function TermStudentsTab({ term }: { term: Term }) {
  const { message } = App.useApp()
  const editable = isTermEditable(term.status)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [search, setSearch] = useState('')
  const [lecturerId, setLecturerId] = useState<number | undefined>()
  const [selected, setSelected] = useState<number[]>([])
  const [adding, setAdding] = useState(false)
  const [importing, setImporting] = useState(false)
  const [assigning, setAssigning] = useState(false)
  const q = useDebounced(search)

  const query = useTermStudents(term.id, { page, size, q: q.trim(), lecturer_id: lecturerId })
  const remove = useRemoveTermStudent(term.id)

  const removeStudent = async (studentId: number) => {
    try {
      await remove.mutateAsync(studentId)
      setSelected((s) => s.filter((id) => id !== studentId))
      message.success('Đã xóa sinh viên khỏi đợt')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const columns: ColumnsType<TermStudent> = [
    { title: 'Mã SV', dataIndex: 'student_code', width: 120 },
    { title: 'Họ và tên', dataIndex: 'full_name' },
    { title: 'Lớp', dataIndex: 'class_name', render: (v: string | null) => v ?? '—' },
    {
      title: 'Giảng viên hướng dẫn',
      dataIndex: 'lecturer_name',
      render: (v: string | null) => v ?? <span style={{ color: '#94A3B8' }}>Chưa phân công</span>,
    },
    ...(editable
      ? [
          {
            title: 'Thao tác',
            key: 'actions',
            width: 100,
            render: (_: unknown, s: TermStudent) => (
              <Popconfirm
                title="Xóa sinh viên khỏi đợt?"
                description="Không xóa được nếu sinh viên đã có đánh giá hoặc kết quả."
                okText="Xóa"
                cancelText="Hủy"
                onConfirm={() => removeStudent(s.student_id)}
              >
                <Button size="small" danger>
                  Xóa
                </Button>
              </Popconfirm>
            ),
          },
        ]
      : []),
  ]

  return (
    <>
      {!editable && (
        <Alert type="info" showIcon title="Đợt đã kết thúc: danh sách sinh viên và phân công không thể thay đổi." style={{ marginBottom: 16 }} />
      )}
      <Flex gap={12} wrap align="center" justify="space-between" style={{ marginBottom: 16 }}>
        <Flex gap={12} wrap align="center">
          <Input.Search
            allowClear
            placeholder="Tìm theo mã hoặc tên"
            style={{ width: 240 }}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
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
        {editable && (
          <Flex gap={8} wrap>
            <Button icon={<TeamOutlined />} disabled={selected.length === 0} onClick={() => setAssigning(true)}>
              Phân công giảng viên{selected.length ? ` (${selected.length})` : ''}
            </Button>
            <Button icon={<UploadOutlined />} onClick={() => setImporting(true)}>
              Import theo mã
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setAdding(true)}>
              Thêm sinh viên
            </Button>
          </Flex>
        )}
      </Flex>

      {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
      <Table<TermStudent>
        rowKey="student_id"
        loading={query.isFetching}
        columns={columns}
        dataSource={query.data?.items ?? []}
        scroll={{ x: 'max-content' }}
        rowSelection={
          editable
            ? { selectedRowKeys: selected, onChange: (keys) => setSelected(keys as number[]), preserveSelectedRowKeys: true }
            : undefined
        }
        locale={{ emptyText: q || lecturerId ? 'Không có sinh viên phù hợp bộ lọc' : 'Đợt chưa có sinh viên nào' }}
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

      <AddStudentsModal term={term} open={adding} onClose={() => setAdding(false)} />
      <ImportModal term={term} open={importing} onClose={() => setImporting(false)} />
      <AssignModal
        term={term}
        studentIds={selected}
        open={assigning}
        onClose={() => setAssigning(false)}
        onDone={() => setSelected([])}
      />
    </>
  )
}
