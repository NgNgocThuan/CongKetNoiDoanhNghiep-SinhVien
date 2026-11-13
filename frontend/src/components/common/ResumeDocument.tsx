import type { ReactNode } from 'react'
import { BriefcaseBusiness, GraduationCap, Mail, MapPin, Phone } from 'lucide-react'
import './resume.css'

const labels: Record<string, string> = { description: 'Mô tả', name: 'Tên', title: 'Tiêu đề', role: 'Vai trò', position: 'Vị trí', company: 'Đơn vị', company_name: 'Doanh nghiệp', start_date: 'Từ', end_date: 'Đến', tech_stack: 'Công nghệ', issuer: 'Đơn vị cấp', issued_at: 'Ngày cấp', level: 'Trình độ', school: 'Trường', degree: 'Bằng cấp', major: 'Chuyên ngành', summary: 'Giới thiệu', bio: 'Giới thiệu', career_goal: 'Mục tiêu nghề nghiệp', experience: 'Kinh nghiệm', experiences: 'Kinh nghiệm', education: 'Học vấn', projects: 'Dự án', certificates: 'Chứng chỉ', certifications: 'Chứng chỉ', achievements: 'Thành tích', languages: 'Ngoại ngữ', interests: 'Sở thích', awards: 'Giải thưởng', self_declared: 'Thông tin bổ sung' }
function record(value: unknown): Record<string, unknown> { return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {} }
function text(value: unknown): string { return typeof value === 'string' || typeof value === 'number' ? String(value) : '' }
function hasContent(value: unknown): boolean {
  if (value == null || value === '') return false
  if (Array.isArray(value)) return value.some(hasContent)
  if (typeof value === 'object') return Object.values(value).some(hasContent)
  return true
}
function Readable({ value }: { value: unknown }) {
  if (!hasContent(value)) return null
  if (Array.isArray(value)) return <div className="resume-entry-list">{value.map((item, index) => <div className="resume-entry" key={index}><Readable value={item} /></div>)}</div>
  if (typeof value === 'object') return <dl className="resume-entry-fields">{Object.entries(record(value)).filter(([key, item]) => !['id', 'student_id', 'user_id', 'official'].includes(key) && hasContent(item)).map(([key, item]) => <div key={key}><dt>{labels[key] || key.replaceAll('_', ' ')}</dt><dd><Readable value={item} /></dd></div>)}</dl>
  return <p className="resume-copy">{String(value)}</p>
}
export function ResumeDocument({ content, title = 'Hồ sơ năng lực', fullName }: { content: unknown; title?: string; fullName?: string }) {
  const data = record(content), official = record(data.official)
  const name = fullName || text(official.full_name) || text(data.full_name) || title
  const major = text(official.major_name) || text(record(official.major).name)
  const contact = [
    { label: 'Email', value: text(data.contact_email || data.email), icon: Mail },
    { label: 'Điện thoại', value: text(data.contact_phone || data.phone), icon: Phone },
    { label: 'Địa chỉ', value: text(data.address), icon: MapPin },
  ].filter(item => item.value)
  const skills = Array.isArray(data.skills) ? data.skills.map(item => typeof item === 'string' ? item : text(record(item).name)).filter(Boolean) : text(data.skills).split(/[\n,]/).filter(Boolean)
  const sections: [string, unknown][] = [
    ['Giới thiệu', data.summary || data.bio], ['Mục tiêu nghề nghiệp', data.career_goal],
    ['Kinh nghiệm làm việc', data.experiences || data.experience], ['Dự án tiêu biểu', data.projects],
    ['Học vấn', data.education], ['Chứng chỉ', data.certificates || data.certifications],
    ['Thành tích', data.achievements || data.awards], ['Ngoại ngữ', data.languages],
  ]
  const known = new Set(['official', 'summary', 'bio', 'career_goal', 'experiences', 'experience', 'projects', 'education', 'certificates', 'certifications', 'achievements', 'awards', 'languages', 'skills', 'full_name', 'contact_email', 'contact_phone', 'email', 'phone', 'address', 'github_url', 'linkedin_url', 'id', 'student_id', 'user_id'])
  for (const [key, value] of Object.entries(data)) if (!known.has(key) && hasContent(value)) sections.push([labels[key] || key.replaceAll('_', ' '), value])
  return <article className="resume-document" aria-label={`CV ${name}`}>
    <header className="resume-header">
      <div className="resume-monogram" aria-hidden="true">{name.split(/\s+/).slice(-2).map(word => word[0]).join('').toUpperCase()}</div>
      <div><span className="resume-eyebrow">HỒ SƠ NĂNG LỰC</span><h1>{name}</h1><p>{major || title}</p></div>
    </header>
    <div className="resume-layout">
      <aside className="resume-sidebar">
        {contact.length > 0 && <section><h2>Liên hệ</h2>{contact.map(({ label, value, icon: Icon }) => <div className="resume-contact" key={label}><Icon size={15} /><div><span>{label}</span><strong>{value}</strong></div></div>)}</section>}
        <section><h2>Kỹ năng chuyên môn</h2><div className="resume-skill-list">{skills.length ? skills.map(skill => <span key={skill}>{skill}</span>) : <p className="resume-empty">Chưa cập nhật kỹ năng trong hồ sơ.</p>}</div></section>
        {(major || official.cohort || official.gpa != null) && <section><h2><GraduationCap size={16} />Học vấn</h2><dl className="resume-education">{[['Chuyên ngành', major], ['Khoa', text(record(official.faculty).name)], ['Khóa học', text(official.cohort)], ['GPA', official.gpa == null ? '' : text(official.gpa)]].filter(([, value]) => value).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></section>}
        {Boolean(data.github_url || data.linkedin_url) && <section><h2>Liên kết nghề nghiệp</h2>{['github_url', 'linkedin_url'].map(key => text(data[key]) && <p className="resume-link-text" key={key}>{text(data[key])}</p>)}</section>}
      </aside>
      <main className="resume-body">
        {sections.filter(([, value]) => hasContent(value)).map(([heading, value]) => <section className="resume-section" key={heading}><h2><span />{heading}</h2><Readable value={value} /></section>)}
        {!sections.some(([, value]) => hasContent(value)) && <div className="resume-empty"><BriefcaseBusiness size={28} /><h2>Giới thiệu năng lực</h2><p>Ứng viên chưa bổ sung nội dung chi tiết trong CV.</p></div>}
      </main>
    </div>
    <footer className="resume-footer">STUDENT CONNECT <span>·</span> {title}</footer>
  </article>
}

export function ResumeSection({ title, children }: { title: string; children: ReactNode }) {
  return <section className="candidate-section"><h3>{title}</h3>{children}</section>
}
