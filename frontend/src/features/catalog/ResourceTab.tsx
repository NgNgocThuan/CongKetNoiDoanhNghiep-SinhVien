/**
 * Một tab danh mục dùng chung: bộ lọc + bảng phân trang + form thêm/sửa + ngừng hoạt động / kích hoạt lại.
 * Danh mục không xóa vĩnh viễn: "Ngừng hoạt động" là xóa mềm (is_active=false), có thể kích hoạt lại.
 */
import { useState, type ReactNode } from 'react'
import { App, Button, Flex, Form, Input, Modal, Popconfirm, Switch, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { PlusOutlined } from '@ant-design/icons'
import { ActiveBadge } from '@/features/school-shared/components/StatusTag'
import QueryError from '@/features/school-shared/components/QueryError'
import { getErrorMessage } from '@/features/school-shared/http'
import { useDebounced } from '@/features/school-shared/useDebounced'
import { useCatalogList, useDeactivateCatalogItem, useSaveCatalogItem } from './hooks'
import type { CatalogItemMap, CatalogListParams, CatalogResource } from './types'

type Item = { id: number; is_active: boolean }

interface Props<R extends CatalogResource> {
  resource: R
  /** Tên loại danh mục viết thường, dùng trong nhãn nút/tiêu đề: "khoa", "ngành"... */
  noun: string
  columns: ColumnsType<CatalogItemMap[R]>
  /** Các Form.Item của form thêm/sửa */
  fields: ReactNode
  /** Trường tùy chọn: chuỗi rỗng được gửi là null để xóa giá trị. */
  optionalKeys?: string[]
  /** Bộ lọc thêm (vd chọn khoa cho tab Ngành); trả về tham số bổ sung cho API. */
  extraFilters?: (value: Partial<CatalogListParams>, onChange: (v: Partial<CatalogListParams>) => void) => ReactNode
  rowExtra?: (item: CatalogItemMap[R]) => ReactNode
}

export default function ResourceTab<R extends CatalogResource>({
  resource,
  noun,
  columns,
  fields,
  optionalKeys = [],
  extraFilters,
  rowExtra,
}: Props<R>) {
  type T = CatalogItemMap[R] & Item
  const { message } = App.useApp()
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(20)
  const [search, setSearch] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [extra, setExtra] = useState<Partial<CatalogListParams>>({})
  const [editing, setEditing] = useState<T | 'new' | null>(null)
  const [form] = Form.useForm()
  const q = useDebounced(search)

  const query = useCatalogList(resource, { page, size, q, include_inactive: includeInactive, ...extra })
  const save = useSaveCatalogItem(resource)
  const deactivate = useDeactivateCatalogItem(resource)

  const openForm = (item: T | 'new') => setEditing(item)

  const submit = async () => {
    const values = (await form.validateFields()) as Record<string, unknown>
    const body: Record<string, unknown> = {}
    for (const [key, raw] of Object.entries(values)) {
      const value = typeof raw === 'string' ? raw.trim() : raw
      body[key] = value === '' && optionalKeys.includes(key) ? null : value
    }
    try {
      await save.mutateAsync({ id: editing === 'new' || editing === null ? undefined : editing.id, body })
      message.success(editing === 'new' ? `Đã thêm ${noun}` : `Đã cập nhật ${noun}`)
      setEditing(null)
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const toggleActive = async (item: T) => {
    try {
      if (item.is_active) {
        await deactivate.mutateAsync(item.id)
        message.success(`Đã ngừng hoạt động ${noun}`)
      } else {
        await save.mutateAsync({ id: item.id, body: { is_active: true } })
        message.success(`Đã kích hoạt lại ${noun}`)
      }
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const allColumns: ColumnsType<T> = [
    ...(columns as unknown as ColumnsType<T>),
    {
      title: 'Trạng thái',
      dataIndex: 'is_active',
      width: 160,
      render: (active: boolean) => <ActiveBadge active={active} />,
    },
    {
      title: 'Thao tác',
      key: 'actions',
      width: rowExtra ? 300 : 220,
      render: (_, item) => (
        <Flex gap={4} wrap>
          <Button size="small" onClick={() => openForm(item)}>
            Sửa
          </Button>
          {rowExtra?.(item)}
          <Popconfirm
            title={item.is_active ? `Ngừng hoạt động ${noun} này?` : `Kích hoạt lại ${noun} này?`}
            description={item.is_active ? 'Mục sẽ không còn xuất hiện trong danh sách chọn, nhưng dữ liệu cũ vẫn giữ.' : undefined}
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
      <Flex gap={12} wrap align="center" justify="space-between" style={{ marginBottom: 16 }}>
        <Flex gap={12} wrap align="center">
          <Input.Search
            allowClear
            placeholder={`Tìm ${noun}`}
            style={{ width: 260 }}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
          {extraFilters?.(extra, (v) => {
            setExtra(v)
            setPage(1)
          })}
          <Flex align="center" gap={8}>
            <Switch
              checked={includeInactive}
              onChange={(v) => {
                setIncludeInactive(v)
                setPage(1)
              }}
            />
            <span>Hiện cả mục đã ngừng hoạt động</span>
          </Flex>
        </Flex>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => openForm('new')}>
          Thêm {noun}
        </Button>
      </Flex>

      {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}

      <Table<T>
        rowKey="id"
        loading={query.isFetching}
        columns={allColumns}
        dataSource={(query.data?.items as T[] | undefined) ?? []}
        scroll={{ x: 'max-content' }}
        locale={{ emptyText: q || includeInactive ? `Không có ${noun} phù hợp bộ lọc` : `Chưa có ${noun} nào` }}
        pagination={{
          current: page,
          pageSize: size,
          total: query.data?.total ?? 0,
          showSizeChanger: true,
          showTotal: (total) => `${total} mục`,
          onChange: (p, s) => {
            setPage(p)
            setSize(s)
          },
        }}
      />

      <Modal
        open={editing !== null}
        title={editing === 'new' ? `Thêm ${noun}` : `Sửa ${noun}`}
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={save.isPending}
        onOk={submit}
        onCancel={() => setEditing(null)}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          requiredMark="optional"
          preserve={false}
          initialValues={editing !== null && editing !== 'new' ? editing : undefined}
        >
          {fields}
        </Form>
      </Modal>
    </>
  )
}
