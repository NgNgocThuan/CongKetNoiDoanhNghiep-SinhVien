/** Sửa dữ liệu học thuật của sinh viên (chỉ nhà trường được sửa). Ngành phải thuộc khoa đã chọn. */
import { App, DatePicker, Form, Input, InputNumber, Modal } from 'antd'
import dayjs from 'dayjs'
import { FacultySelect, MajorSelect } from '@/features/catalog/selectors'
import { getErrorMessage } from '@/features/school-shared/http'
import { useUpdateStudent } from './api'
import type { AdminStudent } from './types'
import { toUpdateBody } from './academic-form'
import type { FormValues } from './academic-form'

export default function EditAcademicModal({
  student,
  open,
  onClose,
}: {
  student: AdminStudent
  open: boolean
  onClose: () => void
}) {
  const { message } = App.useApp()
  const [form] = Form.useForm<FormValues>()
  const update = useUpdateStudent(student.id)
  const facultyId = Form.useWatch('faculty_id', form)

  // Form được dựng lại mỗi lần mở modal (destroyOnHidden) nên initialValues luôn lấy dữ liệu mới nhất
  const initialValues: FormValues = {
    full_name: student.full_name,
    date_of_birth: student.date_of_birth ? dayjs(student.date_of_birth) : null,
    class_name: student.class_name ?? '',
    faculty_id: student.faculty_id,
    major_id: student.major_id,
    cohort: student.cohort,
    gpa: student.gpa === null ? null : Number(student.gpa),
    academic_result: student.academic_result ?? '',
    phone: student.phone ?? '',
  }

  const submit = async () => {
    const values = await form.validateFields()
    try {
      await update.mutateAsync(toUpdateBody(values))
      message.success('Đã cập nhật dữ liệu học thuật')
      onClose()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Modal
      open={open}
      title="Sửa dữ liệu học thuật"
      okText="Lưu"
      cancelText="Hủy"
      confirmLoading={update.isPending}
      onOk={submit}
      onCancel={onClose}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" requiredMark="optional" preserve={false} initialValues={initialValues}>
        <Form.Item name="full_name" label="Họ và tên" rules={[{ required: true, message: 'Vui lòng nhập họ tên' }]}>
          <Input maxLength={255} />
        </Form.Item>
        <Form.Item name="date_of_birth" label="Ngày sinh">
          <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} disabledDate={(d) => d.isAfter(dayjs())} />
        </Form.Item>
        <Form.Item name="class_name" label="Lớp">
          <Input maxLength={50} />
        </Form.Item>
        <Form.Item name="faculty_id" label="Khoa" rules={[{ required: true, message: 'Vui lòng chọn khoa' }]}>
          <FacultySelect onChange={() => form.setFieldValue('major_id', undefined)} />
        </Form.Item>
        <Form.Item name="major_id" label="Ngành" rules={[{ required: true, message: 'Vui lòng chọn ngành thuộc khoa' }]}>
          <MajorSelect facultyId={facultyId} disabled={!facultyId} />
        </Form.Item>
        <Form.Item name="cohort" label="Khóa học" rules={[{ required: true, message: 'Vui lòng nhập khóa' }]}>
          <Input maxLength={20} />
        </Form.Item>
        <Form.Item name="gpa" label="GPA (thang 4)">
          <InputNumber min={0} max={4} step={0.01} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="academic_result" label="Xếp loại">
          <Input maxLength={50} />
        </Form.Item>
        <Form.Item name="phone" label="Điện thoại">
          <Input maxLength={20} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
