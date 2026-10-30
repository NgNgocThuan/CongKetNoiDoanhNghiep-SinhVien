import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowUpRight, Lightbulb, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Pagination } from '@/components/common/Pagination'
import { usePublicCompany, useRecommendedJobs } from '../hooks'
import { positiveId, scoreLabel } from '../format'
import type { JobRecommendation } from '../types'
import { MatchPanel, MatchSummary } from '../components/MatchPanel'
import { JobInformation } from '../components/JobInformation'
import { ApplyDialog } from '../components/ApplyDialog'
import { SaveJobButton } from '../components/SaveJobButton'
import '../matching.css'

function JobCard({ item, selected, onSelect, onApply, onDetail }: { item: JobRecommendation; selected: boolean; onSelect: () => void; onApply: () => void; onDetail: () => void }) {
  const company = usePublicCompany(item.company_id)
  return <article className={'match-card' + (selected ? ' match-card--selected' : '')}><div className="match-card__top"><span className="match-avatar" aria-hidden="true">{(company.data?.name || item.title).slice(0, 2).toUpperCase()}</span><div className="match-card__identity">{company.data && <p>{company.data.name}</p>}<h2>{item.title}</h2></div><span className="match-score-badge"><Sparkles size={14} />Phù hợp {scoreLabel(item.match.score)}</span></div>
    {company.isError && <p className="match-inline-error">Không tải được tên doanh nghiệp. <button className="match-text-button" onClick={() => void company.refetch()}>Thử lại</button></p>}
    <MatchSummary match={item.match} /><div className="match-card__actions"><Button onClick={onApply}>Ứng tuyển</Button><Button variant="secondary" aria-pressed={selected} onClick={onSelect}>Vì sao được gợi ý?</Button><Button variant="ghost" size="sm" onClick={onDetail}>Xem tin<ArrowUpRight size={15} /></Button><SaveJobButton jobId={item.job_id} /></div>
  </article>
}
export default function RecommendedJobsPage() {
  const [params, setParams] = useSearchParams()
  const page = positiveId(params.get('page')) ?? 1
  const query = useRecommendedJobs(page)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [apply, setApply] = useState<JobRecommendation | null>(null), [detailId, setDetailId] = useState<number | null>(null)
  const [mobileDetail, setMobileDetail] = useState(false)
  const selected = query.data?.items.find(item => item.job_id === selectedId) ?? query.data?.items[0]
  function openApply(item: JobRecommendation) { setMobileDetail(false); setApply(item) }
  function openJob(id: number) { setMobileDetail(false); setDetailId(id) }
  const panel = selected && <MatchPanel match={selected.match} title={selected.title} actions={<><Button onClick={() => openApply(selected)}>Ứng tuyển ngay</Button><Button variant="secondary" onClick={() => openJob(selected.job_id)}>Xem tin tuyển dụng</Button></>} />
  function changePage(next: number) { const nextParams = new URLSearchParams(params); nextParams.set('page', String(next)); setParams(nextParams); setMobileDetail(false) }
  return <div className="matching-page"><header className="match-page-heading"><span className="match-eyebrow"><Sparkles size={14} />GỢI Ý THEO HỒ SƠ</span><h1>Cơ hội phù hợp với bạn</h1><p>Khám phá những công việc phù hợp với kỹ năng và hồ sơ của bạn.</p></header>
    <div className="match-profile-tip"><Lightbulb size={23} /><p>Cập nhật hồ sơ và kỹ năng để hệ thống có thêm dữ liệu đánh giá mức độ phù hợp.</p><Link className="button button--primary button--md" to="/student/profile">Cập nhật hồ sơ</Link></div>
    {query.isPending ? <LoadingState label="Đang tính và tải gợi ý việc làm. Quá trình này có thể mất một lúc…" /> : query.isError ? <ErrorState title="Không tải được gợi ý việc làm" message={query.error.message} onRetry={() => void query.refetch()} /> :
      !query.data.items.length ? <div className="match-empty"><EmptyState title={page > 1 ? 'Không có kết quả ở trang này' : 'Chưa có việc làm phù hợp'} description="Kết quả phụ thuộc vào hồ sơ, điều kiện tuyển dụng và các tin còn hạn. Bạn có thể cập nhật hồ sơ hoặc xem lại sau." action={page > 1 ? <Button onClick={() => changePage(1)}>Về trang đầu</Button> : <Link to="/student/profile" className="button button--primary button--md">Cập nhật hồ sơ</Link>} /></div> :
        <><div className="match-results-heading"><div><h2><span>{query.data.total}</span> việc làm phù hợp với hồ sơ của bạn</h2><p>Xếp theo điểm phù hợp do hệ thống trả về</p></div><Button variant="ghost" size="sm" pending={query.isFetching} onClick={() => void query.refetch()}>Làm mới</Button></div>
          <div className="match-columns"><div className="match-list">{query.data.items.map(item => <JobCard key={item.job_id} item={item} selected={selected?.job_id === item.job_id} onSelect={() => { setSelectedId(item.job_id); if (window.matchMedia('(max-width: 1180px)').matches) setMobileDetail(true) }} onApply={() => openApply(item)} onDetail={() => openJob(item.job_id)} />)}<Pagination page={page} pages={query.data.pages} total={query.data.total} onChange={changePage} /></div><aside className="match-desktop-panel">{panel}</aside></div>
          {mobileDetail && <Dialog open onOpenChange={setMobileDetail} title="Vì sao được gợi ý?">{panel}</Dialog>}</>}
    {apply && <ApplyDialog key={apply.job_id} jobId={apply.job_id} title={apply.title} onClose={() => setApply(null)} />}
    {detailId !== null && <JobInformation jobId={detailId} onClose={() => setDetailId(null)} />}
  </div>
}
