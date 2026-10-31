import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/common/PageHeader'
import {
  ActionDialog,
  CatalogSelect,
  DataResult,
  FieldsForm,
  Notice,
  Panel,
  RecordTable,
} from '@/components/common/Workspace'
import { getData, textValue } from '@/components/common/workspace-api'
import type { Row, Field } from '@/components/common/Workspace'
import { Button } from '@/components/ui/Button'
import { http } from '@/lib/http'

const profileFields: Field[] = [
  { name: 'bio', label: 'Giới thiệu bản thân', type: 'textarea' },
  { name: 'career_goal', label: 'Mục tiêu nghề nghiệp', type: 'textarea' },
  { name: 'contact_email', label: 'Email liên hệ', type: 'email' },
  { name: 'contact_phone', label: 'Điện thoại', maxLength: 20 },
  { name: 'address', label: 'Địa chỉ', maxLength: 500 },
  {
    name: 'avatar_url',
    label: 'URL ảnh đại diện',
    type: 'url',
    maxLength: 500,
  },
  { name: 'linkedin_url', label: 'LinkedIn', type: 'url', maxLength: 500 },
  { name: 'github_url', label: 'GitHub', type: 'url', maxLength: 500 },
  { name: 'is_open_to_work', label: 'Sẵn sàng tìm việc', type: 'checkbox' },
  { name: 'show_gpa', label: 'Chia sẻ GPA với doanh nghiệp', type: 'checkbox' },
  {
    name: 'show_contact',
    label: 'Chia sẻ thông tin liên hệ',
    type: 'checkbox',
  },
  { name: 'show_achievements', label: 'Chia sẻ thành tích', type: 'checkbox' },
]
const entities: Record<
  string,
  { title: string; fields: Field[]; columns: string[][] }
> = {
  experiences: {
    title: 'Kinh nghiệm',
    fields: [
      {
        name: 'company_name',
        label: 'Doanh nghiệp',
        required: true,
        maxLength: 255,
      },
      { name: 'position', label: 'Vị trí', required: true, maxLength: 255 },
      { name: 'start_date', label: 'Ngày bắt đầu', type: 'date' },
      { name: 'end_date', label: 'Ngày kết thúc', type: 'date' },
      { name: 'description', label: 'Mô tả', type: 'textarea' },
    ],
    columns: [
      ['company_name', 'Doanh nghiệp'],
      ['position', 'Vị trí'],
      ['start_date', 'Bắt đầu'],
      ['end_date', 'Kết thúc'],
    ],
  },
  projects: {
    title: 'Dự án',
    fields: [
      { name: 'name', label: 'Tên dự án', required: true, maxLength: 255 },
      { name: 'role', label: 'Vai trò', maxLength: 255 },
      { name: 'tech_stack', label: 'Công nghệ', maxLength: 500 },
      { name: 'project_url', label: 'URL dự án', type: 'url', maxLength: 500 },
      { name: 'start_date', label: 'Ngày bắt đầu', type: 'date' },
      { name: 'end_date', label: 'Ngày kết thúc', type: 'date' },
      { name: 'description', label: 'Mô tả', type: 'textarea' },
    ],
    columns: [
      ['name', 'Dự án'],
      ['role', 'Vai trò'],
      ['tech_stack', 'Công nghệ'],
    ],
  },
  certificates: {
    title: 'Chứng chỉ tự khai',
    fields: [
      { name: 'name', label: 'Tên chứng chỉ', required: true, maxLength: 255 },
      { name: 'issuer', label: 'Đơn vị cấp', maxLength: 255 },
      { name: 'issued_at', label: 'Ngày cấp', type: 'date' },
      { name: 'expires_at', label: 'Ngày hết hạn', type: 'date' },
      {
        name: 'credential_url',
        label: 'URL chứng chỉ',
        type: 'url',
        maxLength: 500,
      },
    ],
    columns: [
      ['name', 'Chứng chỉ'],
      ['issuer', 'Đơn vị cấp'],
      ['is_verified', 'Đã xác thực'],
    ],
  },
}
function cleanFields(values: Row, fields: Field[]) {
  return Object.fromEntries(
    fields.map((field) => [
      field.name,
      field.type === 'checkbox'
        ? Boolean(values[field.name])
        : values[field.name] === ''
          ? null
          : (values[field.name] ?? null),
    ]),
  )
}
function ProfileEditor({ initial }: { initial: Row }) {
  const client = useQueryClient()
  const save = useMutation({
    mutationFn: (values: Row) =>
      http.put('/students/me/profile', cleanFields(values, profileFields)),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ['student-profile'] }),
  })
  return (
    <>
      <FieldsForm
        initial={initial}
        fields={profileFields}
        submit={(v) => save.mutate(v)}
        pending={save.isPending}
        error={save.error}
      />
      <Notice
        success={
          save.isSuccess ? 'Đã lưu thông tin và quyền riêng tư.' : undefined
        }
      />
    </>
  )
}
function Skills({ skills }: { skills: Row[] }) {
  const [skillId, setSkillId] = useState(''),
    [level, setLevel] = useState('BEGINNER')
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: ({
      method,
      id,
      data,
    }: {
      method: 'post' | 'put' | 'delete'
      id?: number
      data?: Row
    }) =>
      http.request({
        method,
        url: '/students/me/skills' + (id ? '/' + id : ''),
        data,
      }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ['student-profile'] }),
  })
  const levels = [
    { value: 'BEGINNER', label: 'Cơ bản' },
    { value: 'INTERMEDIATE', label: 'Trung cấp' },
    { value: 'ADVANCED', label: 'Nâng cao' },
    { value: 'EXPERT', label: 'Thành thạo' },
  ]
  return (
    <Panel title="Kỹ năng">
      <form
        className="ws-filters"
        onSubmit={(e) => {
          e.preventDefault()
          if (skillId)
            mutation.mutate({
              method: 'post',
              data: { skill_id: Number(skillId), level },
            })
        }}
      >
        <CatalogSelect
          resource="skills"
          name="skill_id"
          label="Kỹ năng"
          value={skillId}
          onChange={setSkillId}
        />
        <label>
          Mức độ
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            {levels.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit" disabled={!skillId} pending={mutation.isPending}>
          Thêm kỹ năng
        </Button>
      </form>
      <Notice error={mutation.error} />
      <RecordTable
        rows={skills}
        columns={[
          { key: 'name', label: 'Kỹ năng' },
          {
            key: 'level',
            label: 'Mức độ',
            render: (r: Row) => (
              <select
                aria-label={'Mức độ ' + r.name}
                value={String(r.level)}
                disabled={mutation.isPending || r.source === 'SCHOOL'}
                onChange={(e) =>
                  mutation.mutate({
                    method: 'put',
                    id: Number(r.skill_id),
                    data: { level: e.target.value },
                  })
                }
              >
                {levels.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            ),
          },
          { key: 'source', label: 'Nguồn' },
        ]}
        actions={(r) =>
          r.source !== 'SCHOOL' && (
            <Button
              variant="danger"
              size="sm"
              disabled={mutation.isPending}
              onClick={() => {
                if (window.confirm('Xóa kỹ năng này?'))
                  mutation.mutate({ method: 'delete', id: Number(r.skill_id) })
              }}
            >
              Xóa
            </Button>
          )
        }
      />
    </Panel>
  )
}
function ProfileCollection({ kind, rows }: { kind: string; rows: Row[] }) {
  const cfg = entities[kind],
    [edit, setEdit] = useState<Row | null>(null),
    [remove, setRemove] = useState<Row | null>(null)
  const writable = (row: Row) =>
    kind !== 'certificates' || row.source === 'SELF'
  return (
    <Panel
      title={cfg.title}
      actions={
        <Button size="sm" variant="secondary" onClick={() => setEdit({})}>
          Thêm
        </Button>
      }
    >
      <RecordTable
        rows={rows}
        columns={cfg.columns.map(([key, label]) => ({
          key,
          label,
          render: (r: Row) =>
            key === 'is_verified'
              ? r[key]
                ? 'Đã xác thực'
                : 'Chưa xác thực'
              : textValue(r[key]),
        }))}
        actions={(r) =>
          writable(r) && (
            <>
              <Button size="sm" variant="secondary" onClick={() => setEdit(r)}>
                Sửa
              </Button>
              <Button size="sm" variant="danger" onClick={() => setRemove(r)}>
                Xóa
              </Button>
            </>
          )
        }
      />
      {edit && (
        <ActionDialog
          key={String(edit.id ?? 'new')}
          title={(edit.id ? 'Sửa ' : 'Thêm ') + cfg.title.toLowerCase()}
          path={'/students/me/' + kind + (edit.id ? '/' + edit.id : '')}
          method={edit.id ? 'put' : 'post'}
          fields={cfg.fields}
          initial={edit}
          transform={(values) => cleanFields(values, cfg.fields)}
          invalidate={['student-profile']}
          onClose={() => setEdit(null)}
        />
      )}
      {remove && (
        <ActionDialog
          title="Xóa mục này"
          path={'/students/me/' + kind + '/' + remove.id}
          method="delete"
          invalidate={['student-profile']}
          onClose={() => setRemove(null)}
        />
      )}
    </Panel>
  )
}
export default function ProfilePage() {
  const query = useQuery({
    queryKey: ['student-profile'],
    queryFn: () =>
      getData<{
        official: Row
        self_declared: {
          profile: Row
          skills: Row[]
          experiences: Row[]
          projects: Row[]
          certificates: Row[]
        }
      }>('/students/me'),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Hồ sơ của tôi"
        description="Thông tin học thuật từ nhà trường và năng lực do bạn bổ sung."
      />
      <DataResult query={query}>
        {(data) => (
          <>
            <Panel title="Dữ liệu nhà trường · chỉ đọc">
              <dl className="ws-detail">
                {[
                  ['student_code', 'Mã sinh viên'],
                  ['full_name', 'Họ tên'],
                  ['cohort', 'Khóa'],
                  ['class_name', 'Lớp'],
                  ['gpa', 'GPA'],
                  ['academic_result', 'Kết quả học tập'],
                  ['date_of_birth', 'Ngày sinh'],
                ].map(([key, label]) => (
                  <div key={key}>
                    <dt>{label}</dt>
                    <dd>{textValue(data.official[key])}</dd>
                  </div>
                ))}
                <div>
                  <dt>Khoa</dt>
                  <dd>{textValue((data.official.faculty as Row)?.name)}</dd>
                </div>
                <div>
                  <dt>Ngành</dt>
                  <dd>{textValue((data.official.major as Row)?.name)}</dd>
                </div>
              </dl>
            </Panel>
            <Panel title="Giới thiệu & quyền riêng tư">
              <ProfileEditor initial={data.self_declared.profile} />
            </Panel>
            <Skills skills={data.self_declared.skills} />
            {Object.keys(entities).map((kind) => (
              <ProfileCollection
                key={kind}
                kind={kind}
                rows={
                  data.self_declared[
                    kind as 'experiences' | 'projects' | 'certificates'
                  ]
                }
              />
            ))}
            <Panel title="Thành tích do nhà trường xác nhận">
              <RecordTable
                rows={(data.official.achievements || []) as Row[]}
                columns={[
                  { key: 'title', label: 'Thành tích' },
                  { key: 'description', label: 'Nội dung' },
                  { key: 'achieved_at', label: 'Ngày đạt' },
                ]}
              />
            </Panel>
            <Panel title="Chứng chỉ do nhà trường cung cấp · chỉ đọc">
              <RecordTable
                rows={(data.official.certificates || []) as Row[]}
                columns={[
                  { key: 'name', label: 'Chứng chỉ' },
                  { key: 'issuer', label: 'Đơn vị cấp' },
                  { key: 'issued_at', label: 'Ngày cấp' },
                ]}
              />
            </Panel>
          </>
        )}
      </DataResult>
    </div>
  )
}
