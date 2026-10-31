import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Search, SlidersHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState } from '@/components/common/States'
import { jobsApi } from '../api'
import { JobCard } from '../components/JobCard'
import { StudentPage, QueryState } from '../components/StudentUI'
import type { JobFilters } from '../types'
export default function JobsPage() {
 const [search,setSearch] = useSearchParams()
 const page = Math.max(1,Number(search.get('page')) || 1)
 const filters: JobFilters = { ...Object.fromEntries(search), page,size:12,skill_ids:search.getAll('skill_ids') }
 const query = useQuery({queryKey:['student-jobs',filters],queryFn:({signal})=>jobsApi.search(filters,signal)})
 return <StudentPage title="Tìm cơ hội. Bắt đầu hành trình." description="Khám phá việc làm và cơ hội thực tập đã được nhà trường kiểm duyệt.">
 <form key={search.toString()} className="student-filters" onSubmit={e=>{e.preventDefault(); const data=new FormData(e.currentTarget); const params=new URLSearchParams(); data.forEach((value,key)=>{if(String(value).trim()) params.append(key,String(value))}); setSearch(params)}}>
 <label className="wide student-form">Từ khóa<input name="q" defaultValue={search.get('q')||''} placeholder="Vị trí, công nghệ hoặc nội dung công việc…"/></label>
 <label className="student-form">Vị trí<input name="position" defaultValue={search.get('position')||''} placeholder="Ví dụ: Backend Developer"/></label>
 <label className="student-form">Địa điểm<input name="location" defaultValue={search.get('location')||''} placeholder="Ví dụ: Hà Nội"/></label>
 <label className="student-form">Hình thức<select name="work_mode" defaultValue={search.get('work_mode')||''}><option value="">Mọi hình thức</option><option value="ONSITE">Trực tiếp</option><option value="REMOTE">Từ xa</option><option value="HYBRID">Kết hợp</option></select></label>
 <CatalogFilter name="major_id" catalog="majors" label="Ngành học" value={search.get('major_id')||''}/>
 <CatalogFilter name="industry_id" catalog="industries" label="Lĩnh vực" value={search.get('industry_id')||''}/>
 <CatalogFilter name="job_type_id" catalog="job-types" label="Loại hình công việc" value={search.get('job_type_id')||''}/>
 <label className="student-form">Luồng tuyển dụng<select name="flow" defaultValue={search.get('flow')||''}><option value="">Mọi cơ hội</option><option value="free">Ứng tuyển tự do</option><option value="term">Theo đợt thực tập</option></select></label>
 <label className="student-form">Mức lương từ (đ)<input name="salary_from" type="number" min="0" defaultValue={search.get('salary_from')||''}/></label>
 <label className="student-form">Mức lương đến (đ)<input name="salary_to" type="number" min="0" defaultValue={search.get('salary_to')||''}/></label>
 <details className="wide"><summary><SlidersHorizontal size={14}/> Kỹ năng</summary><SkillFilter values={search.getAll('skill_ids')}/></details>
 <div className="student-actions wide"><Button type="submit"><Search size={16}/>Tìm kiếm</Button><Button variant="secondary" onClick={()=>setSearch({})}>Đặt lại bộ lọc</Button></div>
 </form>
 <QueryState query={query}/>{query.data && <><p className="muted">{query.data.total} cơ hội phù hợp với bộ lọc</p>{query.data.items.length ? <div className="student-grid">{query.data.items.map(job=><JobCard key={job.id} job={job}/>)}</div> : <EmptyState title="Chưa tìm thấy cơ hội phù hợp" description="Thử thay đổi từ khóa hoặc giảm bớt bộ lọc."/>}<Pagination {...query.data} onChange={value=>{const next=new URLSearchParams(search);next.set('page',String(value));setSearch(next)}}/></>}</StudentPage>
}
function CatalogFilter({name,catalog,label,value}: {name:string;catalog:string;label:string;value:string}) {
 const [search] = useSearchParams()
 const query=useQuery({queryKey:['student-catalog',catalog,search.get(catalog+'-q')||''],queryFn:()=>jobsApi.catalog(catalog,search.get(catalog+'-q')||'')})
 return <label className="student-form">{label}<input name={catalog+'-q'} defaultValue={search.get(catalog+'-q')||''} placeholder="Tìm danh mục theo tên…"/><select name={name} defaultValue={value} disabled={query.isPending}><option value="">Tất cả</option>{query.data?.items.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select>{query.error && <span role="alert">{query.error.message}</span>}</label>
}
function SkillFilter({values}: {values:string[]}) {
 const [search] = useSearchParams()
 const query=useQuery({queryKey:['student-catalog','skills',search.get('skills-q')||''],queryFn:()=>jobsApi.catalog('skills',search.get('skills-q')||'')})
 return <div className="student-form"><label>Tìm kỹ năng<input name="skills-q" defaultValue={search.get('skills-q')||''} placeholder="Nhập tên và bấm Tìm kiếm để cập nhật danh mục"/></label><div className="student-tags">{query.data?.items.map(item=><label key={item.id} className="student-choice"><input type="checkbox" name="skill_ids" value={item.id} defaultChecked={values.includes(String(item.id))}/>{item.name}</label>)}</div>{query.error && <p role="alert">{query.error.message}</p>}</div>
}

