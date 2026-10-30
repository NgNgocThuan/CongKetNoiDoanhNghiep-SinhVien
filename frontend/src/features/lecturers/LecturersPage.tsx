/** Admin: quản lý giảng viên (chưa có tài khoản đăng nhập riêng cho giảng viên). */
import { useState } from 'react'
import { App, Button, Flex, Form, Input, Modal, Popconfirm, Switch, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined } from '@ant-design/icons'
import PageHeader from '@/components/ui/PageHeader'
import QueryError from '@/components/ui/QueryError'
import { ActiveBadge } from '@/components/ui/StatusTag'
import { useFaculties } from '@/features/catalog/hooks'
import { FacultySelect } from '@/features/catalog/selectors'
import { getErrorMessage } from '@/lib/http'
import { useDebounced } from '@/lib/useDebounced'
import { useDeactivateLecturer, useLecturers, useSaveLecturer, type Lecturer } from './api'

interface FormValues {
  code?: string
  full_name: string
  faculty_id: number
  email?: string
  phone?: string
}

export default function LecturersPage() {
  const { message } = App.useApp()
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [search, setSearch] = useState('')
  const [facultyId, setFacultyId] = useState<number | undefined>()
  const [includeInactive, setIncludeInactive] = useState(false)
  const [editing, setEditing] = useState<Lecturer | 'new' | null>(null)
  const [form] = Form.useForm<FormValues>()
  const q = useDebounced(search)

  const query = useLecturers({ page, size, q, faculty_id: facultyId, include_inactive: includeInactive })
  const { data: faculties } = useFaculties()
  const facultyName = new Map(faculties?.items.map((f) => [f.id, f.name]))
  const save = useSaveLecturer()
  const deactivate = useDeactivateLecturer()

  const openForm = (item: Lecturer | 'new') => setEditing(item)
  const initialValues =
    editing !== null && editing !== 'new'
      ? { ...editing, code: editing.code ?? '', email: editing.email ?? '', phone: editing.phone ?? '' }
      : undefined

  const submit = async () => {
    const values = await form.validateFields()
    // Trường tùy chọn để trống gửi null để xóa giá trị cũ
    const body = {
      code: values.code?.trim() || null,
      full_name: values.full_name.trim(),
      faculty_id: values.faculty_id,
      email: values.email?.trim() || null,
      phone: values.phone?.trim() || null,
    }
    try {
      await save.mutateAsync({ id: editing === 'new' || editing === null ? undefined : editing.id, body })
      message.success(editing === 'new' ? 'Đã thêm giảng viên' : 'Đã cập nhật giảng viên')
      setEditing(null)
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const toggleActive = async (item: Lecturer) => {
    try {
      if (item.is_active) {
        await deactivate.mutateAsync(item.id)
        message.success('Đã ngừng hoạt động giảng viên')
      } else {
        await save.mutateAsync({ id: item.id, body: { is_active: true } })
        message.success('Đã kích hoạt lại giảng viên')
      }
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const columns: ColumnsType<Lecturer> = [
    { title: 'Mã', dataIndex: 'code', width: 120, render: (v: string | null) => v ?? '—' },
    { title: 'Họ và tên', dataIndex: 'full_name' },
    { title: 'Khoa', dataIndex: 'faculty_id', render: (id: number) => facultyName.get(id) ?? `#${id}` },
    { title: 'Email', dataIndex: 'email', render: (v: string | null) => v ?? '—' },
    { title: 'Điện thoại', dataIndex: 'phone', render: (v: string | null) => v ?? '—' },
    { title: 'Trạng thái', dataIndex: 'is_active', width: 160, render: (a: boolean) => <ActiveBadge active={a} /> },
    {
      title: 'Thao tác',
      key: 'actions',
      width: 230,
      render: (_, item) => (
        <Flex gap={4} wrap>
          <Button size="small" onClick={() => openForm(item)}>
            Sửa
          </Button>
          <Popconfirm
            title={item.is_active ? 'Ngừng hoạt động giảng viên này?' : 'Kích hoạt lại giảng viên này?'}
            description={item.is_active ? 'Giảng viên sẽ không được chọn phân công nữa; các phân công cũ vẫn giữ.' : undefined}
            okText="Đồng ý"
            cancelText="Hủy"
            onConfirm={() => toggleActive(item)}
          >
            <Button size="small" danger={item.is_active}>
              {item.is_active ? 'Ngừng hoạt động' : 'Kích hoạt lại'}
            </Button>
          </Popconfirm>
        </Flex>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="Phân hệ quản trị"
        title="Giảng viên"
        subtitle="Danh sách giảng viên hướng dẫn thực tập. Giảng viên chưa có tài khoản đăng nhập; nhà trường nhập nhận xét thay."
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openForm('new')}>
            Thêm giảng viên
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
              setPage(1)
            }}
          />
          <FacultySelect
            allowClear
            placeholder="Lọc theo khoa"
            style={{ width: 240 }}
            value={facultyId}
            onChange={(v) => {
              setFacultyId(v)
              setPage(1)
            }}
          />
          <Flex align="center" gap={8}>
            <Switch
              checked={includeInactive}
              onChange={(v) => {
                setIncludeInactive(v)
                setPage(1)
              }}
            />
            <span>Hiện cả giảng viên đã ngừng hoạt động</span>
          </Flex>
        </Flex>

        {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
        <Table<Lecturer>
          rowKey="id"
          loading={query.isFetching}
          columns={columns}
          dataSource={query.data?.items ?? []}
          scroll={{ x: 'max-content' }}
          locale={{ emptyText: q || facultyId ? 'Không có giảng viên phù hợp bộ lọc' : 'Chưa có giảng viên nào' }}
          pagination={{
            current: page,
            pageSize: size,
            total: query.data?.total ?? 0,
            showSizeChanger: true,
            showTotal: (total) => `${total} giảng viên`,
            onChange: (p, s) => {
              setPage(p)
              setSize(s)
            },
          }}
        />
      </div>

      <Modal
        open={editing !== null}
        title={editing === 'new' ? 'Thêm giảng viên' : 'Sửa giảng viên'}
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={save.isPending}
        onOk={submit}
        onCancel={() => setEditing(null)}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" requiredMark="optional" preserve={false} initialValues={initialValues}>
          <Form.Item name="code" label="Mã giảng viên">
            <Input maxLength={30} placeholder="Tùy chọn" />
          </Form.Item>
          <Form.Item name="full_name" label="Họ và tên" rules={[{ required: true, message: 'Vui lòng nhập họ tên' }]}>
            <Input maxLength={255} />
          </Form.Item>
          <Form.Item name="faculty_id" label="Khoa" rules={[{ required: true, message: 'Vui lòng chọn khoa' }]}>
            <FacultySelect />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: 'email', message: 'Email không hợp lệ' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="Điện thoại">
            <Input maxLength={20} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
