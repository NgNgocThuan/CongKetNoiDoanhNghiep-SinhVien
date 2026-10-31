import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/Button'
import {
  Feedback,
  QueryState,
} from '@/features/student-jobs/components/StudentUI'
import { profileApi } from '@/features/student-profile/api'
import type { FullProfile } from '@/features/student-profile/types'
import { cvsApi } from '../api'
import type { CV } from '../types'

const schema = z.object({
  title: z.string().trim().min(1, 'Nhập tiêu đề CV.').max(255),
  summary: z.string(),
  skills: z.string(),
  experience: z.string(),
  projects: z.string(),
  career_goal: z.string(),
  contact_email: z.union([z.email(), z.literal('')]),
  contact_phone: z.string().max(20),
  github_url: z.string().max(500),
  linkedin_url: z.string().max(500),
})
function text(value: unknown): string {
  return typeof value === 'string'
    ? value
    : Array.isArray(value)
      ? value
          .map((v) => (typeof v === 'string' ? v : JSON.stringify(v)))
          .join('\n')
      : value
        ? JSON.stringify(value)
        : ''
}
export function CVEditor({ cv, onDone }: { cv?: CV; onDone: () => void }) {
  const profile = useQuery({
    queryKey: ['student-profile'],
    queryFn: ({ signal }) => profileApi.get(signal),
  })
  return (
    <>
      <QueryState query={profile} />
      {profile.data && (
        <CVForm cv={cv} profile={profile.data} onDone={onDone} />
      )}
    </>
  )
}
function CVForm({
  cv,
  profile,
  onDone,
}: {
  cv?: CV
  profile: FullProfile
  onDone: () => void
}) {
  const content = cv?.content_json || {},
    self = profile.self_declared,
    official = profile.official
  const defaults = cv
    ? content
    : {
        summary: self.profile.bio,
        career_goal: self.profile.career_goal,
        skills: self.skills.map((skill) => skill.name),
        contact_email: self.profile.contact_email,
        contact_phone: self.profile.contact_phone,
        github_url: self.profile.github_url,
        linkedin_url: self.profile.linkedin_url,
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
      }
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: cv?.title || '',
      summary: text(defaults.summary),
      skills: text(defaults.skills),
      experience: text(defaults.experience),
      projects: text(defaults.projects),
      career_goal: text(defaults.career_goal),
      contact_email: text(defaults.contact_email),
      contact_phone: text(defaults.contact_phone),
      github_url: text(defaults.github_url),
      linkedin_url: text(defaults.linkedin_url),
    },
  })
  const action = useStudentAction(['student-cvs'])
  return (
    <form
      className="student-form"
      onSubmit={form.handleSubmit(async (values) => {
        const additional = Object.fromEntries(
          Object.entries(content).filter(([key]) => key !== 'official'),
        )
        const { title, ...fields } = values
        const content_json = {
          ...additional,
          ...fields,
          skills: values.skills
            .split('\n')
            .map((value) => value.trim())
            .filter(Boolean),
        }
        if (
          await action.run(() =>
            cv
              ? cvsApi.update(cv.id, { title, content_json })
              : cvsApi.create({ title, content_json }),
          )
        )
          onDone()
      })}
    >
      <h3>Thông tin nhà trường · chỉ đọc</h3>
      <p className="student-notice">
        Thông tin học thuật được backend tự điền khi lưu. Bạn chỉ chỉnh sửa
        thông tin bổ sung.
      </p>
      <dl className="student-definition">
        {[
          ['Mã sinh viên', official.student_code],
          ['Họ và tên', official.full_name],
          ['Khoa', official.faculty.name],
          ['Ngành', official.major.name],
          ['Lớp', official.class_name],
          ['Khóa', official.cohort],
          ['GPA', official.gpa],
          ['Xếp loại', official.academic_result],
        ].map(([label, value]) => (
          <div key={String(label)}>
            <dt>{label}</dt>
            <dd>{value ?? 'Chưa cập nhật'}</dd>
          </div>
        ))}
      </dl>
      <label>
        Tiêu đề CV *<input maxLength={255} {...form.register('title')} />
        <span className="field__error">
          {form.formState.errors.title?.message}
        </span>
      </label>
      {(
        [
          ['summary', 'Giới thiệu'],
          ['career_goal', 'Mục tiêu nghề nghiệp'],
          ['skills', 'Kỹ năng (mỗi dòng một kỹ năng)'],
          ['experience', 'Kinh nghiệm'],
          ['projects', 'Dự án'],
        ] as const
      ).map(([key, label]) => (
        <label key={key}>
          {label}
          <textarea {...form.register(key)} />
        </label>
      ))}
      {(
        [
          ['contact_email', 'Email liên hệ'],
          ['contact_phone', 'Điện thoại'],
          ['github_url', 'GitHub'],
          ['linkedin_url', 'LinkedIn'],
        ] as const
      ).map(([key, label]) => (
        <label key={key}>
          {label}
          <input
            type={
              key === 'contact_email'
                ? 'email'
                : key.endsWith('_url')
                  ? 'url'
                  : 'text'
            }
            {...form.register(key)}
          />
          <span className="field__error">
            {form.formState.errors[key]?.message}
          </span>
        </label>
      ))}
      <Feedback {...action} />
      <Button type="submit" pending={action.pending}>
        Lưu CV
      </Button>
    </form>
  )
}
