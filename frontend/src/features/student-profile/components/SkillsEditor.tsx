import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { jobsApi } from '@/features/student-jobs/api'
import { Feedback } from '@/features/student-jobs/components/StudentUI'
import { profileApi } from '../api'
import type { StudentSkill } from '../types'
const levels: Record<string, string> = {
  BEGINNER: 'Cơ bản',
  INTERMEDIATE: 'Trung bình',
  ADVANCED: 'Nâng cao',
  EXPERT: 'Chuyên gia',
}
export function SkillsEditor({ skills }: { skills: StudentSkill[] }) {
  const [q, setQ] = useState(''),
    [skill, setSkill] = useState(''),
    [level, setLevel] = useState('BEGINNER'),
    [remove, setRemove] = useState<number | null>(null)
  const query = useQuery({
    queryKey: ['student-catalog', 'skills', q],
    queryFn: () => jobsApi.catalog('skills', q),
  })
  const action = useStudentAction(['student-profile'])
  return (
    <section className="student-panel student-stack">
      <h2>Kỹ năng tự khai</h2>
      {skills.map((item) => (
        <div key={item.skill_id} className="student-record">
          <strong>{item.name}</strong>
          <div className="student-actions">
            <label className="student-form">
              Mức độ
              <select
                aria-label={'Mức độ ' + item.name}
                value={item.level}
                disabled={action.pending}
                onChange={(e) =>
                  void action.run(() =>
                    profileApi.save('skills', { level: e.target.value }, item.skill_id),
                  )
                }
              >
                {Object.entries(levels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <Button variant="ghost" onClick={() => setRemove(item.skill_id)}>
              Xóa
            </Button>
          </div>
        </div>
      ))}
      <form
        className="student-form"
        onSubmit={(e) => {
          e.preventDefault()
          if (skill)
            void action.run(() => profileApi.save('skills', { skill_id: Number(skill), level }))
        }}
      >
        <label>
          Tìm tên kỹ năng
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Python, React…" />
        </label>
        <label>
          Kỹ năng
          <select value={skill} onChange={(e) => setSkill(e.target.value)} required>
            <option value="">Chọn kỹ năng</option>
            {query.data?.items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        {query.error && <p role="alert">{query.error.message}</p>}
        <label>
          Mức độ
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            {Object.entries(levels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit" pending={action.pending}>
          Thêm kỹ năng
        </Button>
        <Feedback {...action} />
      </form>
      <ConfirmDialog
        open={remove !== null}
        onOpenChange={(open) => {
          if (!open) setRemove(null)
        }}
        title="Xóa kỹ năng?"
        description="Kỹ năng tự khai sẽ được xóa khỏi hồ sơ."
        danger
        onConfirm={async () => {
          await profileApi.remove('skills', remove!)
          await action.run(async () => undefined)
        }}
      />
    </section>
  )
}
