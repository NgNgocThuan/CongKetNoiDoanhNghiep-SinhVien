import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileText, Download, UserRound } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { ErrorState, LoadingState } from '@/components/common/States'
import { UserAvatar } from '@/components/common/UserAvatar'
import { ResumeDocument, ResumeSection } from '@/components/common/ResumeDocument'
import { http } from '@/lib/http'

interface CandidateProfile {
  user_id: number; full_name: string; major_name: string; cohort: string; gpa: number | null
  bio: string | null; career_goal: string | null; contact_email: string | null; contact_phone: string | null
  skills: { name: string; level: string }[]
  experiences: { company_name: string; position: string; description: string | null; start_date: string | null; end_date: string | null }[]
  projects: { name: string; role: string | null; description: string | null; tech_stack: string | null }[]
  certificates: { name: string; issuer: string | null; is_verified: boolean }[]
  achievements: { title: string; description: string | null }[]
  cv: { title: string; type: string } | null
}

export function CandidateProfileDialog({ jobId, studentId, onClose }: { jobId: number; studentId: number; onClose: () => void }) {
  const path = `/matching/jobs/${jobId}/candidates/${studentId}`
  const [tab, setTab] = useState<'profile' | 'cv'>('profile')
  const [url, setUrl] = useState('')
  const profile = useQuery({ queryKey: ['candidate-profile', jobId, studentId], queryFn: async () => (await http.get<CandidateProfile>(path + '/profile')).data })
  const cv = useQuery({
    queryKey: ['candidate-cv', jobId, studentId], enabled: tab === 'cv' && Boolean(profile.data?.cv), retry: false,
    queryFn: async () => {
      const response = await http.get<Blob>(path + '/cv', { responseType: 'blob' })
      const mime = String(response.headers['content-type'] || '')
      return { blob: response.data, mime, content: mime.includes('json') ? JSON.parse(await response.data.text()) as { content: unknown } : null }
    },
  })
  useEffect(() => {
    if (!cv.data) return
    const value = URL.createObjectURL(cv.data.blob)
    setUrl(value)
    return () => URL.revokeObjectURL(value)
  }, [cv.data])
  const data = profile.data
  return <Dialog open wide className="candidate-dialog" onOpenChange={open => { if (!open) onClose() }} title="Hồ sơ ứng viên">
    <div className="candidate-tabs" role="tablist" aria-label="Thông tin ứng viên">
      <button id="candidate-profile-tab" role="tab" aria-controls="candidate-profile-panel" aria-selected={tab === 'profile'} onClick={() => setTab('profile')}><UserRound size={14} /> Hồ sơ nghề nghiệp</button>
      <button id="candidate-cv-tab" role="tab" aria-controls="candidate-cv-panel" aria-selected={tab === 'cv'} onClick={() => setTab('cv')}><FileText size={14} /> CV giới thiệu</button>
    </div>
    <div className="candidate-content">
      {profile.isPending ? <LoadingState /> : profile.isError ? <ErrorState message={profile.error.message} onRetry={() => void profile.refetch()} /> : data && <>
        {tab === 'profile' ? <div role="tabpanel" id="candidate-profile-panel" aria-labelledby="candidate-profile-tab">
          <header className="candidate-hero"><UserAvatar userId={data.user_id} name={data.full_name} size={64} /><div><h2>{data.full_name}</h2><p>{data.major_name} · {data.cohort}</p></div></header>
          <div className="candidate-sections">
            <ResumeSection title="Giới thiệu & định hướng"><p>{data.bio || 'Chưa cập nhật giới thiệu.'}</p>{data.career_goal && <p>{data.career_goal}</p>}</ResumeSection>
            <ResumeSection title="Thông tin được chia sẻ"><dl>{[['GPA', data.gpa == null ? 'Không chia sẻ' : Number(data.gpa).toLocaleString('vi-VN')], ['Email liên hệ', data.contact_email || 'Không chia sẻ'], ['Điện thoại', data.contact_phone || 'Không chia sẻ']].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></ResumeSection>
            <ResumeSection title="Kỹ năng đã xác nhận"><div className="resume-skill-list">{data.skills.map(item => <span key={item.name}>{item.name}</span>)}</div></ResumeSection>
            <ResumeSection title="Kinh nghiệm làm việc">{data.experiences.length ? data.experiences.map((item, index) => <article key={index}><strong>{item.position} · {item.company_name}</strong><p>{item.start_date || 'Chưa cập nhật'} – {item.end_date || 'Hiện tại'}</p><p>{item.description}</p></article>) : <p>Chưa cập nhật kinh nghiệm.</p>}</ResumeSection>
            <ResumeSection title="Dự án tiêu biểu">{data.projects.length ? data.projects.map((item, index) => <article key={index}><strong>{item.name}</strong><p>{item.role} {item.tech_stack && `· ${item.tech_stack}`}</p><p>{item.description}</p></article>) : <p>Chưa cập nhật dự án.</p>}</ResumeSection>
            <ResumeSection title="Chứng chỉ & thành tích">{data.certificates.map((item, index) => <article key={index}><strong>{item.name}</strong><p>{item.issuer}{item.is_verified && ' · Đã xác minh'}</p></article>)}{data.achievements.map((item, index) => <article key={index}><strong>{item.title}</strong><p>{item.description}</p></article>)}{!data.certificates.length && !data.achievements.length && <p>Chưa cập nhật.</p>}</ResumeSection>
          </div>
          <div className="candidate-cv-toolbar" style={{ marginTop: 18 }}><div><strong>{data.cv?.title || 'CV giới thiệu'}</strong><span>{data.cv ? 'Xem bản CV ứng viên chọn để giới thiệu năng lực.' : 'Ứng viên chưa có CV khả dụng.'}</span></div>{data.cv && <Button onClick={() => setTab('cv')}><FileText size={16} />Mở CV sinh viên</Button>}</div>
        </div> : <div role="tabpanel" id="candidate-cv-panel" aria-labelledby="candidate-cv-tab">
          {!data.cv ? <div className="candidate-file-message"><FileText size={36} /><h3>Chưa có CV giới thiệu</h3><p>Ứng viên chưa có CV khả dụng. Bạn vẫn có thể đánh giá thông tin trong hồ sơ nghề nghiệp.</p></div> : <>
            <div className="candidate-cv-toolbar"><div><strong>{data.cv.title}</strong><span>{data.full_name} · {data.cv.type === 'ONLINE' ? 'CV trực tuyến' : 'Tài liệu ứng viên cung cấp'}</span></div>{url && !cv.data?.content && <a className="button button--secondary button--md" href={url} download={`CV-${data.full_name}.${cv.data?.mime.includes('pdf') ? 'pdf' : 'docx'}`}><Download size={15} />Tải CV</a>}</div>
            {cv.isPending ? <LoadingState label="Đang mở CV ứng viên…" /> : cv.isError ? <ErrorState message={cv.error.message} onRetry={() => void cv.refetch()} /> : cv.data && <>
              {cv.data.content ? <ResumeDocument content={cv.data.content.content} title={data.cv.title} fullName={data.full_name} /> :
                cv.data.mime.includes('pdf') && url ? <object className="candidate-pdf" data={url} type="application/pdf" aria-label={`CV ${data.full_name}`}><div className="candidate-file-message"><p>Trình duyệt không hỗ trợ xem PDF trực tiếp. Bấm Tải CV ở trên để mở tài liệu.</p></div></object> :
                <div className="candidate-file-message"><FileText size={42} /><h3>Tài liệu Word</h3><p>CV được giữ nguyên định dạng của ứng viên. Bấm Tải CV để mở bằng Word hoặc ứng dụng đọc tài liệu.</p></div>}
            </>}
          </>}
        </div>}
      </>}
    </div>
  </Dialog>
}
