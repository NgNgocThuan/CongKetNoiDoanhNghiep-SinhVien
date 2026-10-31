import { BriefcaseBusiness, CalendarDays, MapPin, Wallet } from 'lucide-react'
import { Dialog } from '@/components/ui/Dialog'
import { ErrorState, LoadingState } from '@/components/common/States'
import { useJob } from '../hooks'
import { salaryLabel, workModes } from '../format'
import type { Job } from '../types'
import { SkillTags } from './MatchPanel'
import '../matching.css'
export function JobMetadata({ job }: { job: Job }) {
  return <div className="match-job-meta"><span><MapPin size={15} />{job.location || 'Chưa cung cấp địa điểm'}</span><span><BriefcaseBusiness size={15} />{job.job_type.name} · {workModes[job.work_mode]}</span><span><CalendarDays size={15} />Hạn nộp: {job.deadline.split('-').reverse().join('/')}</span><strong><Wallet size={15} />{salaryLabel(job)}</strong></div>
}
export function JobInformation({ jobId, onClose }: { jobId: number; onClose: () => void }) {
  const query = useJob(jobId)
  return <Dialog open onOpenChange={open => { if (!open) onClose() }} title="Chi tiết tin tuyển dụng">
    {query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : <div className="match-job-detail"><p className="eyebrow">{query.data.company.name}</p><h3>{query.data.title}</h3><JobMetadata job={query.data} />
      <h4>Mô tả công việc</h4><p className="match-preline">{query.data.description}</p>{query.data.requirements && <><h4>Yêu cầu</h4><p className="match-preline">{query.data.requirements}</p></>}
      {query.data.benefits && <><h4>Quyền lợi</h4><p className="match-preline">{query.data.benefits}</p></>}
      <h4>Kỹ năng yêu cầu</h4><SkillTags skills={query.data.skills.map(item => item.skill.name)} />
    </div>}
  </Dialog>
}
