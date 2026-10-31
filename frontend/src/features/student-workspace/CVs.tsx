import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/common/PageHeader'
import {
  ActionDialog,
  DataResult,
  FieldsForm,
  Notice,
  Panel,
} from '@/components/common/Workspace'
import { getData, textValue } from '@/components/common/workspace-api'
import type { Field, Row } from '@/components/common/Workspace'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { http } from '@/lib/http'
import { downloadFile } from '@/utils/download'
import type { CV } from './types'

const cvFields: Field[] = [
  { name: 'title', label: 'Tên CV', required: true, maxLength: 255 },
  { name: 'summary', label: 'Giới thiệu bản thân', type: 'textarea' },
  { name: 'career_goal', label: 'Mục tiêu nghề nghiệp', type: 'textarea' },
  { name: 'skills', label: 'Kỹ năng (phân cách bằng dấu phẩy)' },
  { name: 'experience', label: 'Kinh nghiệm', type: 'textarea' },
  { name: 'projects', label: 'Dự án', type: 'textarea' },
  { name: 'contact_email', label: 'Email liên hệ', type: 'email' },
  { name: 'contact_phone', label: 'Điện thoại', maxLength: 20 },
  { name: 'github_url', label: 'GitHub', type: 'url', maxLength: 500 },
  { name: 'linkedin_url', label: 'LinkedIn', type: 'url', maxLength: 500 },
]

function AcademicInformation({ official }: { official: Row }) {
  const fields = [
    ['student_code', 'Mã sinh viên'],
    ['full_name', 'Họ và tên'],
    ['date_of_birth', 'Ngày sinh'],
    ['class_name', 'Lớp'],
    ['cohort', 'Khóa'],
    ['gpa', 'GPA'],
    ['academic_result', 'Kết quả học tập'],
  ]
  return (
    <>
      <p className="muted">
        Dữ liệu do nhà trường quản lý, được backend đưa vào CV khi lưu. Bạn
        không thể sửa các thông tin này trong CV.
      </p>
      <dl className="ws-detail">
        {fields.map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>{textValue(official[key])}</dd>
          </div>
        ))}
        <div>
          <dt>Khoa</dt>
          <dd>{textValue((official.faculty as Row)?.name)}</dd>
        </div>
        <div>
          <dt>Ngành</dt>
          <dd>{textValue((official.major as Row)?.name)}</dd>
        </div>
      </dl>
    </>
  )
}

function CVEditor({ cv, onClose }: { cv?: CV; onClose: () => void }) {
  const client = useQueryClient()
  const profile = useQuery({
    queryKey: ['student-profile'],
    queryFn: () =>
      getData<{
        official: Row
        self_declared: {
          profile: Row
          skills: Row[]
          experiences: Row[]
          projects: Row[]
        }
      }>('/students/me'),
  })
  const mutation = useMutation({
    mutationFn: (values: Row) => {
      const content: Row = Object.fromEntries(
        cvFields
          .filter((field) => field.name !== 'title')
          .map((field) => [field.name, values[field.name] || '']),
      )
      content.skills = String(values.skills || '')
        .split(',')
        .map((skill) => skill.trim())
        .filter(Boolean)
      // Only self-declared fields are sent; official is always supplied by the backend.
      const body = { title: values.title, content_json: content }
      return cv
        ? http.put('/cvs/' + cv.id, body)
        : http.post('/cvs/online', body)
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['cvs'] })
      await client.invalidateQueries({ queryKey: ['matching'] })
      onClose()
    },
  })
  return (
    <Dialog
      open
      wide
      title={cv ? 'Chỉnh sửa CV online' : 'Tạo CV online'}
      onOpenChange={(open) => {
        if (!open && !mutation.isPending) onClose()
      }}
    >
      <DataResult query={profile}>
        {(data) => {
          const self = data.self_declared
          const content = cv?.content_json
          const initial: Row = content
            ? {
                ...content,
                skills: Array.isArray(content.skills)
                  ? content.skills.join(', ')
                  : '',
              }
            : {
                summary: self.profile.bio || '',
                career_goal: self.profile.career_goal || '',
                skills: self.skills.map((skill) => skill.name).join(', '),
                experience: self.experiences
                  .map((item) =>
                    [item.position, item.company_name, item.description]
                      .filter(Boolean)
                      .join(' · '),
                  )
                  .join('\n'),
                projects: self.projects
                  .map((item) =>
                    [item.name, item.role, item.tech_stack, item.description]
                      .filter(Boolean)
                      .join(' · '),
                  )
                  .join('\n'),
                contact_email: self.profile.contact_email || '',
                contact_phone: self.profile.contact_phone || '',
                github_url: self.profile.github_url || '',
                linkedin_url: self.profile.linkedin_url || '',
              }
          return (
            <>
              <h3>Thông tin nhà trường · chỉ đọc</h3>
              <AcademicInformation official={data.official} />
              <h3>Thông tin bổ sung</h3>
              <p className="muted">
                Các mục dưới được gợi sẵn từ hồ sơ của bạn. Thay đổi ở đây chỉ
                lưu vào CV này.
              </p>
              <FieldsForm
                fields={cvFields}
                initial={{ ...initial, title: cv?.title || '' }}
                submit={(values) => mutation.mutate(values)}
                pending={mutation.isPending}
                error={mutation.error}
                label="Lưu CV online"
              />
            </>
          )
        }}
      </DataResult>
    </Dialog>
  )
}

function CVPreview({ cv, onClose }: { cv: CV; onClose: () => void }) {
  const content = cv.content_json || {}
  return (
    <Dialog
      open
      wide
      title={cv.title}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <h3>Thông tin học thuật đã lưu trong CV</h3>
      <AcademicInformation official={(content.official || {}) as Row} />
      {cvFields
        .filter((field) => field.name !== 'title' && content[field.name])
        .map((field) => (
          <section key={field.name}>
            <h3>{field.label}</h3>
            <p className="ws-preline">
              {Array.isArray(content[field.name])
                ? (content[field.name] as string[]).join(', ')
                : String(content[field.name])}
            </p>
          </section>
        ))}
      <p className="muted">
        Thông tin liên hệ nhập trong CV sẽ đi cùng hồ sơ khi bạn ứng tuyển.
      </p>
    </Dialog>
  )
}

function Analysis({ cv }: { cv: CV }) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: () =>
      http.post<{ parsed_json: Row }>('/cvs/' + cv.id + '/analyze', undefined, {
        timeout: 120000,
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ['cvs'] }),
  })
  const result = mutation.data?.data.parsed_json || cv.parsed_json
  const labels: Record<string, string> = {
    skills: 'Kỹ năng',
    experience_months: 'Kinh nghiệm (tháng)',
    keywords: 'Từ khóa',
    domains: 'Lĩnh vực',
    projects: 'Dự án',
  }
  return (
    <>
      <Button
        variant="secondary"
        size="sm"
        pending={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        Phân tích CV
      </Button>
      <Notice error={mutation.error} />
      {result && (
        <details>
          <summary>Kết quả phân tích</summary>
          <p className="muted">
            Dữ liệu trích xuất hỗ trợ matching. Kiểm tra lại thông tin trước khi
            sử dụng.
          </p>
          <dl className="ws-detail">
            {Object.entries(result).map(([key, value]) => (
              <div key={key}>
                <dt>{labels[key] || key}</dt>
                <dd>
                  {typeof value === 'object'
                    ? JSON.stringify(value, null, 2)
                    : String(value ?? '—')}
                </dd>
              </div>
            ))}
          </dl>
        </details>
      )}
    </>
  )
}

export default function CVsPage() {
  const client = useQueryClient()
  const query = useQuery({
    queryKey: ['cvs', 'me'],
    queryFn: () => getData<CV[]>('/cvs/me'),
  })
  const [edit, setEdit] = useState<CV | 'new' | null>(null)
  const [preview, setPreview] = useState<CV | null>(null)
  const [action, setAction] = useState<{ cv: CV; remove: boolean } | null>(null)
  const download = useMutation({
    mutationFn: (cv: CV) =>
      downloadFile('/api/v1/cvs/' + cv.id + '/download', cv.title + '.json'),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="CV của tôi"
        description="Tạo CV online từ thông tin nhà trường và bổ sung năng lực của bạn."
        actions={<Button onClick={() => setEdit('new')}>Tạo CV online</Button>}
      />
      <Notice error={download.error} />
      <DataResult query={query}>
        {(data) => {
          const onlineCVs = data.filter((cv) => cv.type === 'ONLINE')
          return onlineCVs.length ? (
            <div className="ws-cards">
              {onlineCVs.map((cv) => (
                <Panel key={cv.id} title={cv.title}>
                  <p>CV trực tuyến {cv.is_default && '· Mặc định'}</p>
                  <div className="ws-actions">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setPreview(cv)}
                    >
                      Xem CV
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setEdit(cv)}
                    >
                      Chỉnh sửa
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      pending={download.isPending}
                      onClick={() => download.mutate(cv)}
                    >
                      Tải dữ liệu CV (JSON)
                    </Button>
                    {!cv.is_default && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setAction({ cv, remove: false })}
                      >
                        Đặt mặc định
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => setAction({ cv, remove: true })}
                    >
                      Xóa
                    </Button>
                    <Analysis cv={cv} />
                  </div>
                </Panel>
              ))}
            </div>
          ) : (
            <Panel title="Chưa có CV online">
              <p>
                Tạo CV từ hồ sơ nhà trường, sau đó bổ sung thông tin và xem
                trước khi ứng tuyển.
              </p>
            </Panel>
          )
        }}
      </DataResult>
      {edit && (
        <CVEditor
          cv={edit === 'new' ? undefined : edit}
          onClose={() => setEdit(null)}
        />
      )}
      {preview && <CVPreview cv={preview} onClose={() => setPreview(null)} />}
      {action && (
        <ActionDialog
          title={action.remove ? 'Xóa CV' : 'Đặt CV mặc định'}
          path={'/cvs/' + action.cv.id + (action.remove ? '' : '/set-default')}
          method={action.remove ? 'delete' : 'post'}
          invalidate={['cvs']}
          onSuccess={() => {
            void client.invalidateQueries({ queryKey: ['matching'] })
          }}
          onClose={() => setAction(null)}
        />
      )}
    </div>
  )
}
