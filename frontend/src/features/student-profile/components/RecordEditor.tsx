import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Feedback } from '@/features/student-jobs/components/StudentUI'
import { profileApi } from '../api'
import type { StudentRecord } from '../types'
interface Field {
  key: string
  label: string
  required?: boolean
  type?: string
  max?: number
}
const configs: Record<string, Field[]> = {
  experiences: [
    { key: 'company_name', label: 'Công ty', required: true, max: 255 },
    { key: 'position', label: 'Vị trí', required: true, max: 255 },
    { key: 'start_date', label: 'Ngày bắt đầu', type: 'date' },
    { key: 'end_date', label: 'Ngày kết thúc', type: 'date' },
    { key: 'description', label: 'Mô tả', type: 'textarea' },
  ],
  projects: [
    { key: 'name', label: 'Tên dự án', required: true, max: 255 },
    { key: 'role', label: 'Vai trò', max: 255 },
    { key: 'tech_stack', label: 'Công nghệ', max: 500 },
    { key: 'project_url', label: 'URL dự án', max: 500 },
    { key: 'start_date', label: 'Ngày bắt đầu', type: 'date' },
    { key: 'end_date', label: 'Ngày kết thúc', type: 'date' },
    { key: 'description', label: 'Mô tả', type: 'textarea' },
  ],
  certificates: [
    { key: 'name', label: 'Tên chứng chỉ', required: true, max: 255 },
    { key: 'issuer', label: 'Đơn vị cấp', max: 255 },
    { key: 'issued_at', label: 'Ngày cấp', type: 'date' },
    { key: 'expires_at', label: 'Ngày hết hạn', type: 'date' },
    { key: 'credential_url', label: 'URL chứng chỉ', max: 500 },
  ],
}
export function RecordEditor({
  group,
  title,
  items,
}: {
  group: string
  title: string
  items: StudentRecord[]
}) {
  const [editor, setEditor] = useState<StudentRecord | null | undefined>(),
    [remove, setRemove] = useState<number | null>(null)
  const action = useStudentAction(['student-profile'])
  return (
    <section className="student-panel">
      <div className="student-section-title">
        <h2>{title}</h2>
        <Button variant="secondary" onClick={() => setEditor(null)}>
          + Thêm
        </Button>
      </div>
      {!items.length && <p className="muted">Chưa có thông tin.</p>}
      {items.map((item) => (
        <div className="student-record" key={item.id}>
          <div>
            <h3>{String(item.name || item.company_name || '')}</h3>
            <p>{String(item.position || item.role || item.issuer || '')}</p>
            {group === 'certificates' && (
              <span className="student-tag">
                {item.is_verified ? 'Đã xác thực' : 'Tự khai · Chờ xác thực'}
              </span>
            )}
            <p className="student-rich">{String(item.description || '')}</p>
          </div>
          <div className="student-actions">
            <Button variant="secondary" onClick={() => setEditor(item)}>
              Sửa
            </Button>
            <Button variant="ghost" onClick={() => setRemove(item.id)}>
              Xóa
            </Button>
          </div>
        </div>
      ))}
      <Dialog
        open={editor !== undefined}
        onOpenChange={(open) => {
          if (!open) setEditor(undefined)
        }}
        title={(editor ? 'Sửa ' : 'Thêm ') + title.toLowerCase()}
      >
        {editor !== undefined && (
          <RecordForm
            key={editor?.id || 'new'}
            group={group}
            item={editor}
            onDone={() => setEditor(undefined)}
          />
        )}
      </Dialog>
      <ConfirmDialog
        open={remove !== null}
        onOpenChange={(open) => {
          if (!open) setRemove(null)
        }}
        title={'Xóa ' + title.toLowerCase() + '?'}
        description="Thông tin tự khai này sẽ được xóa khỏi hồ sơ."
        danger
        onConfirm={async () => {
          await profileApi.remove(group, remove!)
          await action.run(async () => undefined)
        }}
      />
    </section>
  )
}
function RecordForm({
  group,
  item,
  onDone,
}: {
  group: string
  item: StudentRecord | null
  onDone: () => void
}) {
  const fields = configs[group]
  const schema = z.record(z.string(), z.string()).superRefine((data, ctx) => {
    for (const field of fields) {
      if (field.required && !data[field.key]?.trim())
        ctx.addIssue({
          code: 'custom',
          path: [field.key],
          message: 'Vui lòng nhập thông tin.',
        })
      if (field.max && (data[field.key]?.length || 0) > field.max)
        ctx.addIssue({
          code: 'custom',
          path: [field.key],
          message: 'Thông tin quá dài.',
        })
    }
    const start = data.start_date || data.issued_at,
      end = data.end_date || data.expires_at
    if (start && end && end < start)
      ctx.addIssue({
        code: 'custom',
        path: [data.end_date ? 'end_date' : 'expires_at'],
        message: 'Ngày kết thúc không được trước ngày bắt đầu.',
      })
  })
  const form = useForm<Record<string, string>>({
    resolver: zodResolver(schema),
    defaultValues: Object.fromEntries(fields.map((f) => [f.key, String(item?.[f.key] || '')])),
  })
  const action = useStudentAction(['student-profile'])
  return (
    <form
      className="student-form"
      onSubmit={form.handleSubmit(async (values) => {
        const body = Object.fromEntries(fields.map((f) => [f.key, values[f.key]?.trim() || null]))
        if (await action.run(() => profileApi.save(group, body, item?.id))) onDone()
      })}
    >
      {fields.map((field) => (
        <label key={field.key}>
          {field.label}
          {field.required ? ' *' : ''}
          {field.type === 'textarea' ? (
            <textarea {...form.register(field.key)} />
          ) : (
            <input
              type={field.type || 'text'}
              maxLength={field.max}
              {...form.register(field.key)}
            />
          )}
          <span className="field__error">{form.formState.errors[field.key]?.message}</span>
        </label>
      ))}
      {group === 'certificates' && (
        <p className="muted">
          Sau khi sửa nội dung, chứng chỉ sẽ cần được nhà trường xác thực lại.
        </p>
      )}
      <Feedback {...action} />
      <Button type="submit" pending={action.pending}>
        Lưu
      </Button>
    </form>
  )
}
