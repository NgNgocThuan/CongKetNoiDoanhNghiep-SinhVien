import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { EmptyState } from '@/components/common/States'
import { Pagination } from '@/components/common/Pagination'
import { jobsApi } from '../api'
import { JobCard } from '../components/JobCard'
import { StudentPage, QueryState } from '../components/StudentUI'
export default function SavedJobsPage(){
 const [params,setParams]=useSearchParams(), page=Math.max(1,Number(params.get('page'))||1)
 const query=useQuery({queryKey:['saved-jobs',page],queryFn:({signal})=>jobsApi.saved(page,signal)})
 return <StudentPage title="Việc làm đã lưu" description="Giữ lại những cơ hội bạn quan tâm và quay lại khi sẵn sàng."><QueryState query={query}/>{query.data && <>{query.data.items.length ? <div className="student-grid">{query.data.items.map(item=><JobCard key={item.job.id} job={item.job} saved/>)}</div> : <EmptyState title="Bạn chưa lưu việc làm nào" description="Lưu một cơ hội từ trang tìm việc để xem lại tại đây."/>}<Pagination {...query.data} onChange={page=>setParams({page:String(page)})}/></>}</StudentPage>
}

