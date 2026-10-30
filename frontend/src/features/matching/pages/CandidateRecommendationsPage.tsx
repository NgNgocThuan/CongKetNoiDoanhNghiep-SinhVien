import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { BriefcaseBusiness, LockKeyhole, Mail, ShieldCheck, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Pagination } from '@/components/common/Pagination'
import { matchingApi } from '../api'
import { positiveId, jobStatuses, scoreLabel } from '../format'
import { useCandidates, useJob, useMajor } from '../hooks'
import type { CandidateRecommendation } from '../types'
import { MatchPanel, MatchSummary, SkillTags } from '../components/MatchPanel'
import { JobInformation, JobMetadata } from '../components/JobInformation'
import { InviteDialog } from '../components/InviteDialog'
import '../matching.css'

function MajorName({ id }: { id: number }) {
  const query = useMajor(id)
  return <span>{query.data?.name ?? (query.isError ? 'Chưa tải được tên ngành' : 'Đang tải ngành học…')}</span>
}
function SharedInformation({ item }: { item: CandidateRecommendation }) {
  return <div className="match-shared-info"><div><span>Ngành học</span><strong><MajorName id={item.major_id} /></strong></div><div><span>GPA được chia sẻ</span><strong>{item.gpa === null ? 'Không chia sẻ' : Number(item.gpa).toLocaleString('vi-VN', { maximumFractionDigits: 2 }) + ' / 4'}</strong></div><div><span>Email liên hệ</span><strong>{item.contact_email || 'Không chia sẻ'}</strong></div><div><span>Số điện thoại</span><strong>{item.contact_phone || 'Không chia sẻ'}</strong></div>{item.achievements.length > 0 && <div className="match-achievements"><span>Thành tích được chia sẻ</span><ul>{item.achievements.map((achievement, index) => <li key={index}><strong>{achievement.title}</strong>{achievement.description && <p>{achievement.description}</p>}</li>)}</ul></div>}</div>
}
export default function CandidateRecommendationsPage() {
  const [params, setParams] = useSearchParams()
  const jobId = positiveId(params.get('job_id')), page = positiveId(params.get('page')) ?? 1, jobsPage = positiveId(params.get('jobs_page')) ?? 1
  const jobs = useQuery({ queryKey: ['jobs', 'me', jobsPage], queryFn: ({ signal }) => matchingApi.companyJobs(jobsPage, signal), staleTime: 60_000 })
  const job = useJob(jobId)
  const candidates = useCandidates(jobId, page, job.isSuccess)
  const [selectedKey, setSelectedKey] = useState(''), [mobileDetail, setMobileDetail] = useState(false)
  const [invite, setInvite] = useState<{ jobId: number; jobTitle: string; candidate: CandidateRecommendation } | null>(null)
  const [sent, setSent] = useState<Set<string>>(new Set())
  const [detailId, setDetailId] = useState<number | null>(null)
  const selected = candidates.data?.items.find(item => jobId + ':' + item.student_id === selectedKey) ?? candidates.data?.items[0]
  const sentKey = (studentId: number) => jobId + ':' + studentId
  const canInvite = (item: CandidateRecommendation) => !sent.has(sentKey(item.student_id))
  function openInvite(item: CandidateRecommendation) { if (jobId && job.data) { setMobileDetail(false); setInvite({ jobId, jobTitle: job.data.title, candidate: item }) } }
  function change(key: string, value: number | null) {
    const next = new URLSearchParams(params)
    if (value === null) next.delete(key); else next.set(key, String(value))
    if (key === 'job_id') { next.delete('page'); setMobileDetail(false) }
    setParams(next)
  }
  const panel = selected && <MatchPanel match={selected.match} title={selected.full_name} subtitle={job.data?.title} actions={<Button onClick={() => openInvite(selected)} disabled={!canInvite(selected)}><Mail size={16} />{canInvite(selected) ? 'Mời ứng tuyển' : 'Đã gửi lời mời'}</Button>}><SharedInformation item={selected} /></MatchPanel>
  return <div className="matching-page"><header className="match-page-heading"><span className="match-eyebrow"><Sparkles size={14} />GỢI Ý THEO TIN TUYỂN DỤNG</span><h1>Kết nối với ứng viên phù hợp</h1><p>Chọn một tin tuyển dụng để khám phá ứng viên phù hợp với yêu cầu của doanh nghiệp.</p></header>
    <section className="match-job-picker" aria-label="Phạm vi gợi ý"><div><BriefcaseBusiness size={23} /><div><h2>Tin tuyển dụng áp dụng</h2><p>Mỗi tin có danh sách gợi ý và điểm phù hợp riêng.</p></div></div>
      {jobs.isPending ? <LoadingState label="Đang tải tin tuyển dụng…" /> : jobs.isError ? <ErrorState message={jobs.error.message} onRetry={() => void jobs.refetch()} /> : <><label className="match-select-label">Chọn tin tuyển dụng<select aria-label="Chọn tin tuyển dụng" value={jobId ?? ''} onChange={event => change('job_id', positiveId(event.target.value))}><option value="">— Chọn một tin tuyển dụng —</option>{jobId && !jobs.data.items.some(item => item.id === jobId) && <option value={jobId}>{job.data?.title ?? 'Tin #' + jobId}</option>}{jobs.data.items.map(item => <option key={item.id} value={item.id}>{item.title} · {jobStatuses[item.status] || item.status}</option>)}</select></label>{jobs.data.pages > 1 && <Pagination page={jobsPage} pages={jobs.data.pages} total={jobs.data.total} onChange={next => change('jobs_page', next)} />}</>}
    </section>
    {jobId === null ? <div className="match-empty"><EmptyState title={jobs.isSuccess && jobs.data.total === 0 ? 'Chưa có tin tuyển dụng' : 'Chưa chọn tin tuyển dụng'} description={jobs.isSuccess && jobs.data.total === 0 ? 'Doanh nghiệp cần có tin tuyển dụng trước khi xem gợi ý ứng viên.' : 'Chọn một tin ở phía trên để xem ứng viên và kết quả phù hợp cho vị trí đó.'} action={jobs.isSuccess && jobs.data.total === 0 ? <Link className="button button--secondary button--md" to="/company/jobs">Đến tin tuyển dụng</Link> : undefined} /></div> :
      job.isPending ? <LoadingState label="Đang tải tin đã chọn…" /> : job.isError ? <ErrorState title="Không xem được tin đã chọn" message={job.error.message} onRetry={() => void job.refetch()} /> : <>
        <section className="match-selected-job"><div className="match-selected-job__title"><span className="match-status">{jobStatuses[job.data.status] || job.data.status}</span><h2>{job.data.title}</h2></div><JobMetadata job={job.data} /><div className="match-selected-job__bottom"><SkillTags skills={job.data.skills.map(item => item.skill.name)} /><Button variant="secondary" size="sm" onClick={() => setDetailId(jobId)}>Xem tin tuyển dụng</Button></div></section>
        {candidates.isPending ? <LoadingState label="Đang tính và tải gợi ý ứng viên cho tin này. Quá trình này có thể mất một lúc…" /> : candidates.isError ? <ErrorState title="Không tải được gợi ý ứng viên" message={candidates.error.message} onRetry={() => void candidates.refetch()} /> : !candidates.data?.items.length ? <div className="match-empty"><EmptyState title={page > 1 ? 'Không có kết quả ở trang này' : 'Chưa có ứng viên phù hợp'} description="Hệ thống chỉ gợi ý sinh viên đang tìm việc và đáp ứng điều kiện của tin tuyển dụng đã chọn." action={page > 1 ? <Button onClick={() => change('page', 1)}>Về trang đầu</Button> : undefined} /></div> :
          <><div className="match-results-heading"><div><h2><span>{candidates.data.total}</span> ứng viên phù hợp</h2><p><ShieldCheck size={14} />Chỉ hiển thị dữ liệu được phép chia sẻ</p></div><Button variant="ghost" size="sm" pending={candidates.isFetching} onClick={() => void candidates.refetch()}>Làm mới</Button></div>
            <div className="match-columns"><div className="match-list">{candidates.data.items.map(item => <article key={item.student_id} className={'match-card' + (selected?.student_id === item.student_id ? ' match-card--selected' : '')}><div className="match-card__top"><span className="match-avatar">{item.full_name.split(' ').slice(-2).map(part => part[0]).join('')}</span><div className="match-card__identity"><h2>{item.full_name}</h2><p><MajorName id={item.major_id} /></p></div><span className="match-score-badge">Phù hợp {scoreLabel(item.match.score)}</span></div><div className="match-privacy-line"><LockKeyhole size={14} />GPA: {item.gpa === null ? 'Không chia sẻ' : Number(item.gpa).toLocaleString('vi-VN') + ' / 4'}</div><MatchSummary match={item.match} /><div className="match-card__actions"><Button variant="secondary" aria-pressed={selected?.student_id === item.student_id} onClick={() => { setSelectedKey(sentKey(item.student_id)); if (window.matchMedia('(max-width: 1180px)').matches) setMobileDetail(true) }}>Xem mức độ phù hợp</Button><Button onClick={() => openInvite(item)} disabled={!canInvite(item)}><Mail size={15} />{canInvite(item) ? 'Mời ứng tuyển' : 'Đã gửi lời mời'}</Button></div></article>)}<Pagination page={page} pages={candidates.data.pages} total={candidates.data.total} onChange={next => { change('page', next); setMobileDetail(false) }} /></div><aside className="match-desktop-panel">{panel}</aside></div>
            {mobileDetail && <Dialog open onOpenChange={setMobileDetail} title="Mức độ phù hợp của ứng viên">{panel}</Dialog>}</>}
      </>}
    {invite && <InviteDialog key={invite.jobId + ':' + invite.candidate.student_id} jobId={invite.jobId} jobTitle={invite.jobTitle} studentId={invite.candidate.student_id} fullName={invite.candidate.full_name} onClose={() => setInvite(null)} onSent={() => setSent(previous => new Set([...previous, invite.jobId + ':' + invite.candidate.student_id]))} />}
    {detailId !== null && <JobInformation jobId={detailId} onClose={() => setDetailId(null)} />}
  </div>
}
