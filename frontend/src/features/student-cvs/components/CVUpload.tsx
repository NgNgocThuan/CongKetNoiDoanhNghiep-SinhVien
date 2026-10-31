import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Feedback } from '@/features/student-jobs/components/StudentUI'
import { cvsApi } from '../api'
export function CVUpload({ onDone }: { onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null),
    [title, setTitle] = useState(''),
    [error, setError] = useState('')
  const action = useStudentAction(['student-cvs'])
  return (
    <form
      className="student-form"
      onSubmit={async (e) => {
        e.preventDefault()
        setError('')
        if (!file || !title.trim()) {
          setError('Chọn file và nhập tiêu đề CV.')
          return
        }
        if (!/\.(pdf|docx)$/i.test(file.name)) {
          setError('Chỉ hỗ trợ PDF hoặc DOCX.')
          return
        }
        if (file.size === 0) {
          setError('File CV trống.')
          return
        }
        if (await action.run(() => cvsApi.upload(title.trim(), file))) onDone()
      }}
    >
      <label>
        Tiêu đề CV
        <input value={title} maxLength={255} required onChange={(e) => setTitle(e.target.value)} />
      </label>
      <label className="student-upload">
        Chọn file PDF hoặc DOCX
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
      </label>
      <p className="muted">
        Giới hạn dung lượng do máy chủ kiểm tra. CV đã nộp được lưu riêng tại thời điểm ứng tuyển.
      </p>
      <Feedback error={error || action.error} />
      <Button type="submit" pending={action.pending}>
        Tải CV lên
      </Button>
    </form>
  )
}
