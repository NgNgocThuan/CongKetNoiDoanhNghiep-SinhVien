import { useQuery } from '@tanstack/react-query'
import { Building2 } from 'lucide-react'
import { jobsApi } from '../api'
import { QueryState } from './StudentUI'
export function CompanyPublicProfile({companyId}: {companyId:number}) {
 const query=useQuery({queryKey:['student-company',companyId],queryFn:({signal})=>jobsApi.company(companyId,signal)})
 const company=query.data
 return <><QueryState query={query}/>{company && <article className="student-panel student-stack"><span className="student-logo"><Building2/></span><h2>{company.name}</h2><p className="muted">{company.address || 'Chưa cập nhật địa chỉ'}</p><p>Quy mô: {company.company_size || 'Chưa cập nhật'}</p>{company.website && /^https?:\/\//i.test(company.website) && <a href={company.website} target="_blank" rel="noreferrer">Website doanh nghiệp ↗</a>}{[['Giới thiệu',company.description],['Công nghệ',company.tech_stack],['Quyền lợi',company.benefits]].map(([label,value])=><section key={label}><h3>{label}</h3><p className="student-rich">{value || 'Chưa cập nhật'}</p></section>)}</article>}</>
}

