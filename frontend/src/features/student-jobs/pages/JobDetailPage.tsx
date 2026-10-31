import { dateText } from '../format'
import { useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ApplyDialog } from '@/features/student-applications'
import { jobsApi } from '../api'
import { SaveJobButton } from '../components/SaveJobButton'
import { salaryText } from '../format'
import { StudentPage, QueryState } from '../components/StudentUI'
export default function JobDetailPage(){
 const {id}=useParams(), jobId=Number(id), [params]=useSearchParams(), navigate=useNavigate()
 const [apply,setApply]=useState(false)
 const query=useQuery({queryKey:['student-job',jobId],queryFn:({signal})=>jobsApi.detail(jobId,signal)})
 const job=query.data
 const closed=job && (job.status!=='APPROVED'||job.deadline<new Date().toISOString().slice(0,10))
 return <StudentPage title={job?.title || 'Chi tiết cơ hội'} description={job?.company.name}><Link to="/student/jobs">← Trở về tìm việc</Link><QueryState query={query}/>{job && <div className="student-split"><article className="student-panel student-stack">{[['Mô tả công việc',job.description],['Yêu cầu ứng viên',job.requirements],['Quyền lợi',job.benefits]].map(([title,content])=><section key={title}><h2>{title}</h2><p className="student-rich">{content || 'Chưa cập nhật'}</p></section>)}<section><h2>Kỹ năng</h2><div className="student-tags">{job.skills?.map(item=><span className="student-tag" key={item.skill_id}>{item.skill.name} · {item.is_required?'Bắt buộc':'Ưu tiên'}</span>)}</div></section><section><h2>Ngành học</h2><p>{job.majors?.map(item=>item.major.name).join(', ')||'Mọi ngành'}</p></section></article><aside className="student-stack"><div className="student-panel"><h2>Thông tin tuyển dụng</h2><p className="student-salary">{salaryText(job)}</p><p>{job.location||'Chưa cập nhật địa điểm'}</p><p>{job.job_type.name} · {job.work_mode}</p><p>Số lượng: {job.quantity}</p><p>Hạn nộp: {dateText(job.deadline)}</p>{job.min_gpa!=null && <p>GPA tối thiểu: {job.min_gpa}/4</p>}{job.min_experience_months!=null && <p>Kinh nghiệm: {job.min_experience_months} tháng</p>}<div className="student-stack"><Button disabled={!!closed} onClick={()=>setApply(true)}>{closed?'Không còn nhận hồ sơ':'Ứng tuyển ngay'}</Button><SaveJobButton jobId={job.id}/></div></div><div className="student-panel"><h3>{job.company.name}</h3><Link to={'/student/companies/'+job.company.id}>Xem hồ sơ doanh nghiệp ↗</Link></div></aside></div>}{job && <ApplyDialog open={apply} jobId={job.id} invitationId={Number(params.get('invitation_id'))||undefined} onClose={()=>setApply(false)} onSuccess={app=>navigate('/student/applications/'+app.id)}/>}</StudentPage>
}

