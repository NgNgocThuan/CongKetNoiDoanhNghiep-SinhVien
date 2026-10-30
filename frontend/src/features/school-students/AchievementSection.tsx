/** Thành tích / nghiên cứu khoa học do nhà trường xác nhận: xem, thêm, xóa. */
import { useState } from 'react'
import { App, Button, DatePicker, Flex, Form, Input, Modal, Popconfirm, Select, Typography } from 'antd'
import ItemList from '@/features/school-shared/components/ItemList'
import { PlusOutlined } from '@ant-design/icons'
import { Badge } from '@/features/school-shared/components/StatusTag'
import { getErrorMessage } from '@/features/school-shared/http'
import { formatDate } from '@/features/school-shared/format'
import { useAddAchievement, useDeleteAchievement } from './api'
import { ACHIEVEMENT_TYPE_LABEL } from './labels.constants'
import type { Achievement, AchievementType } from './types'

interface FormValues {
  type: AchievementType
  title: string
  description?: string
  achieved_at?: import('dayjs').Dayjs | null
}

export default function AchievementSection({ studentId, items }: { studentId: number; items: Achievement[] }) {
  const { message } = App.useApp()
  const [open, setOpen] = useState(false)
  const [form] = Form.useForm<FormValues>()
  const add = useAddAchievement(studentId)
  const remove = useDeleteAchievement(studentId)

  const submit = async () => {
    const values = await form.validateFields()
    try {
      await add.mutateAsync({
        type: values.type,
        title: values.title.trim(),
        description: values.description?.trim() || null,
        achieved_at: values.achieved_at ? values.achieved_at.format('YYYY-MM-DD') : null,
      })
      message.success('Đã thêm thành tích')
      setOpen(false)
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const removeItem = async (id: number) => {
    try {
      await remove.mutateAsync(id)
      message.success('Đã xóa thành tích')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <>
      <Flex justify="space-between" align="center" style={{ marginBottom: 12 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          Nghiên cứu khoa học & thành tích
        </Typography.Title>
        <Button
          icon={<PlusOutlined />}
          onClick={() => setOpen(true)}
        >
          Thêm
        </Button>
      </Flex>
      <ItemList
        items={items}
        rowKey={(a) => a.id}
        empty="Chưa có thành tích nào"
        render={(a) => ({
          title: (
            <Flex gap={8} align="center" wrap>
              <span>{a.title}</span>
              <Badge tone="info">{ACHIEVEMENT_TYPE_LABEL[a.type]}</Badge>
            </Flex>
          ),
          description: (
            <>
              {a.description && <div>{a.description}</div>}
              <div>Ngày đạt: {formatDate(a.achieved_at)}</div>
            </>
          ),
          actions: (
            <Popconfirm title="Xóa thành tích này?" okText="Xóa" cancelText="Hủy" onConfirm={() => removeItem(a.id)}>
              <Button size="small" danger>
                Xóa
              </Button>
            </Popconfirm>
          ),
        })}
      />
      <Modal
        open={open}
        title="Thêm thành tích"
        okText="Lưu"
        cancelText="Hủy"
        confirmLoading={add.isPending}
        onOk={submit}
        onCancel={() => setOpen(false)}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" requiredMark="optional" preserve={false} initialValues={{ type: 'ACHIEVEMENT' }}>
          <Form.Item name="type" label="Loại" rules={[{ required: true }]}>
            <Select
              options={(Object.keys(ACHIEVEMENT_TYPE_LABEL) as AchievementType[]).map((k) => ({
                value: k,
                label: ACHIEVEMENT_TYPE_LABEL[k],
              }))}
            />
          </Form.Item>
          <Form.Item name="title" label="Tiêu đề" rules={[{ required: true, message: 'Vui lòng nhập tiêu đề' }]}>
            <Input maxLength={255} />
          </Form.Item>
          <Form.Item name="description" label="Mô tả">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="achieved_at" label="Ngày đạt">
            <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
