/** Tạo / sửa đợt thực tập. Ngày bắt đầu phải trước hoặc bằng ngày kết thúc. */
import { App, DatePicker, Form, Input, Modal } from 'antd'
import dayjs, { type Dayjs } from 'dayjs'
import { getErrorMessage } from '@/lib/http'
import { useSaveTerm } from './api'
import type { Term } from './types'

interface FormValues {
  name: string
  semester: string
  academic_year: string
  period: [Dayjs, Dayjs]
}

export default function TermFormModal({
  open,
  term,
  onClose,
  onSaved,
}: {
  open: boolean
  /** Có giá trị: sửa đợt này; không có: tạo mới */
  term?: Term
  onClose: () => void
  onSaved?: (term: Term) => void
}) {
  const { message } = App.useApp()
  const [form] = Form.useForm<FormValues>()
  const save = useSaveTerm()

  const initialValues = term
    ? {
        name: term.name,
        semester: term.semester,
        academic_year: term.academic_year,
        period: [dayjs(term.start_date), dayjs(term.end_date)] as [Dayjs, Dayjs],
      }
    : undefined

  const submit = async () => {
    const v = await form.validateFields()
    try {
      const saved = await save.mutateAsync({
        id: term?.id,
        body: {
          name: v.name.trim(),
          semester: v.semester.trim(),
          academic_year: v.academic_year.trim(),
          start_date: v.period[0].format('YYYY-MM-DD'),
          end_date: v.period[1].format('YYYY-MM-DD'),
        },
      })
      message.success(term ? 'Đã cập nhật đợt thực tập' : 'Đã tạo đợt thực tập')
      onSaved?.(saved)
      onClose()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Modal
      open={open}
      title={term ? 'Cấu hình đợt thực tập' : 'Tạo đợt thực tập'}
      okText="Lưu"
      cancelText="Hủy"
      confirmLoading={save.isPending}
      onOk={submit}
      onCancel={onClose}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" requiredMark="optional" preserve={false} initialValues={initialValues}>
        <Form.Item name="name" label="Tên đợt" rules={[{ required: true, message: 'Vui lòng nhập tên đợt' }]}>
          <Input maxLength={255} placeholder="Ví dụ: Thực tập tốt nghiệp HK1 2025-2026" />
        </Form.Item>
        <Form.Item name="academic_year" label="Năm học" rules={[{ required: true, message: 'Vui lòng nhập năm học' }]}>
          <Input maxLength={20} placeholder="2025-2026" />
        </Form.Item>
        <Form.Item name="semester" label="Học kỳ" rules={[{ required: true, message: 'Vui lòng nhập học kỳ' }]}>
          <Input maxLength={20} placeholder="HK1" />
        </Form.Item>
        <Form.Item name="period" label="Thời gian" rules={[{ required: true, message: 'Vui lòng chọn thời gian đợt' }]}>
          <DatePicker.RangePicker format="DD/MM/YYYY" style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
