import { dateText } from '@/features/student-jobs/format'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Mail } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/States'
import { Pagination } from '@/components/common/Pagination'
import { ApplyDialog } from '@/features/student-applications'
import { jobsApi } from '@/features/student-jobs/api'
import { StudentPage, QueryState, Status } from '@/features/student-jobs/components/StudentUI'
import { invitationsApi } from '../api'
import type { Invitation } from '../api'
export default function InvitationsPage(){
 const [params,setParams]=useSearchParams(),page=Math.max(1,Number(params.get('page'))||1)
 const query=useQuery({queryKey:['student-invitations',page],queryFn:({signal})=>invitationsApi.list(page,signal)})
 return <StudentPage title="Lời mời từ doanh nghiệp" description="Một kết nối mới, một cơ hội mới. Xem lời nhắn và chọn cơ hội phù hợp với bạn."><QueryState query={query}/>{query.data && <>{query.data.items.length ? <div className="student-stack">{query.data.items.map(item=><InvitationCard key={item.id} invitation={item}/>)}</div>:<EmptyState title="Chưa có lời mời" description="Hoàn thiện hồ sơ và bật tìm việc để doanh nghiệp tìm thấy bạn." action={<Link to="/student/profile">Cập nhật hồ sơ →</Link>}/>}<Pagination {...query.data} onChange={page=>setParams({page:String(page)})}/></>}</StudentPage>
}
function InvitationCard({invitation:item}:{invitation:Invitation}){
 const [apply,setApply]=useState(false),[decline,setDecline]=useState(false),client=useQueryClient(),navigate=useNavigate()
 const job=useQuery({queryKey:['student-job',item.job_id],queryFn:({signal})=>jobsApi.detail(item.job_id,signal),retry:false})
 const company=useQuery({queryKey:['student-company',item.company_id],queryFn:({signal})=>jobsApi.company(item.company_id,signal),enabled:!job.data,retry:false})
 return <article className="student-panel"><div className="student-card-top"><span className="student-logo"><Mail/></span><div><h2>{job.data?.title || 'Lời mời ứng tuyển'}</h2><p>{job.data?.company.name || company.data?.name || 'Doanh nghiệp gửi lời mời'}</p></div><Status value={item.status}/></div><p className="muted">Nhận ngày {dateText(item.created_at)}</p><blockquote className="student-rich">{item.message || 'Doanh nghiệp mời bạn tìm hiểu vị trí tuyển dụng và gửi hồ sơ.'}</blockquote>{job.error && <p className="muted">Chi tiết tin hiện không khả dụng. Bạn có thể thử mở lại tin để kiểm tra.</p>}<div className="student-actions"><Link className="button button--secondary" to={'/student/jobs/'+item.job_id}>Xem tin</Link>{item.status==='PENDING' && <><Button variant="secondary" onClick={()=>setDecline(true)}>Từ chối</Button><Button onClick={()=>setApply(true)}>Ứng tuyển theo lời mời</Button></>}</div><ApplyDialog open={apply} jobId={item.job_id} invitationId={item.id} onClose={()=>setApply(false)} onSuccess={app=>navigate('/student/applications/'+app.id)}/><ConfirmDialog open={decline} onOpenChange={setDecline} title="Từ chối lời mời?" description="Doanh nghiệp sẽ thấy phản hồi từ chối cho lời mời này." confirmLabel="Từ chối lời mời" onConfirm={async()=>{await invitationsApi.decline(item.id);await client.invalidateQueries({queryKey:['student-invitations']})}}/></article>
}

