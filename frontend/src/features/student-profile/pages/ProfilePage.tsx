import { dateText } from '@/features/student-jobs/format'
import { useQuery } from '@tanstack/react-query'
import { ShieldCheck } from 'lucide-react'
import {
  StudentPage,
  QueryState,
} from '@/features/student-jobs/components/StudentUI'
import { profileApi } from '../api'
import { ProfileForm } from '../components/ProfileForm'
import { RecordEditor } from '../components/RecordEditor'
import { SkillsEditor } from '../components/SkillsEditor'
export default function ProfilePage() {
  const query = useQuery({
    queryKey: ['student-profile'],
    queryFn: ({ signal }) => profileApi.get(signal),
  })
  const official = query.data?.official,
    self = query.data?.self_declared
  return (
    <StudentPage
      title="Hồ sơ của tôi"
      description="Năng lực của bạn, được kể bằng những trải nghiệm thật."
    >
      <QueryState query={query} />
      {official && self && (
        <>
          <article className="student-panel">
            <div className="student-section-title">
              <div>
                <h2>{official.full_name}</h2>
                <p className="muted">
                  {official.student_code} · {official.major.name}
                </p>
              </div>
              <span className="student-tag teal">
                <ShieldCheck size={15} />
                Dữ liệu nhà trường · Chỉ đọc
              </span>
            </div>
            <dl className="student-definition">
              {[
                ['Khoa', official.faculty.name],
                ['Ngành', official.major.name],
                ['Lớp', official.class_name],
                ['Khóa', official.cohort],
                ['GPA (thang 4)', official.gpa],
                ['Xếp loại', official.academic_result],
                ['Ngày sinh', dateText(official.date_of_birth)],
                ['Điện thoại', official.phone],
              ].map(([label, value]) => (
                <div key={String(label)}>
                  <dt>{label}</dt>
                  <dd>{value ?? 'Chưa cập nhật'}</dd>
                </div>
              ))}
            </dl>
            <h3>Thành tích nhà trường</h3>
            {official.achievements.length ? (
              official.achievements.map((item) => (
                <p key={item.id}>
                  <strong>{String(item.title)}</strong>
                  <br />
                  {String(item.description || '')}
                </p>
              ))
            ) : (
              <p className="muted">Chưa có thành tích.</p>
            )}
            <h3>Chứng chỉ nhà trường</h3>
            {official.certificates.length ? (
              official.certificates.map((item) => (
                <p key={item.id}>
                  {String(item.name)}{' '}
                  <span className="student-tag teal">Nhà trường xác nhận</span>
                </p>
              ))
            ) : (
              <p className="muted">Chưa có chứng chỉ.</p>
            )}
          </article>
          <section className="student-panel">
            <ProfileForm key={self.profile.student_id} profile={self.profile} />
          </section>
          <SkillsEditor skills={self.skills} />
          <RecordEditor
            group="experiences"
            title="Kinh nghiệm"
            items={self.experiences}
          />
          <RecordEditor group="projects" title="Dự án" items={self.projects} />
          <RecordEditor
            group="certificates"
            title="Chứng chỉ tự khai"
            items={self.certificates.filter((item) => item.source === 'SELF')}
          />
        </>
      )}
    </StudentPage>
  )
}
