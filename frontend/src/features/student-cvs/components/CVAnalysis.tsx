import { useMutation,useQueryClient } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { http } from '@/lib/http'
import { Button } from '@/components/ui/Button'
import { Feedback } from '@/features/student-jobs/components/StudentUI'
import type { CV } from '../types'
const labels:Record<string,string>={summary:'Tóm tắt',skills:'Kỹ năng',experience:'Kinh nghiệm',experiences:'Kinh nghiệm',projects:'Dự án',education:'Học vấn',fields:'Lĩnh vực',domains:'Lĩnh vực',name:'Tên',description:'Mô tả',level:'Mức độ',title:'Tiêu đề',company:'Công ty',position:'Vị trí',official:'Dữ liệu nhà trường',full_name:'Họ tên',student_code:'Mã sinh viên',faculty:'Khoa',major:'Ngành',cohort:'Khóa',gpa:'GPA',class_name:'Lớp',date_of_birth:'Ngày sinh',academic_result:'Xếp loại'}
export function CVContent({value}:{value:unknown}){
 if(value===null||value===undefined)return <span className="muted">Chưa có dữ liệu</span>
 if(Array.isArray(value))return <ul>{value.map((v,i)=><li key={i}><CVContent value={v}/></li>)}</ul>
 if(typeof value==='object')return <dl>{Object.entries(value).filter(([key])=>key!=='id').map(([key,v])=><div key={key}><dt className="student-label">{labels[key]||key.replaceAll('_',' ')}</dt><dd style={{margin:'4px 0 16px'}}><CVContent value={v}/></dd></div>)}</dl>
 return <span className="student-rich">{String(value)}</span>
}
export function CVAnalysis({cv}:{cv:CV}){
 const client=useQueryClient()
 const mutation=useMutation({mutationFn:async()=>(await http.post<{cv_id:number;parsed_json:Record<string,unknown>}>('/cvs/'+cv.id+'/analyze')).data,onSuccess:()=>client.invalidateQueries({queryKey:['student-cvs']})})
 return <section className="student-panel student-stack"><span className="student-tag teal"><Sparkles size={14}/>Phân tích CV</span><h2>Hiểu rõ thế mạnh của bạn</h2><p className="muted">Trích xuất kỹ năng, kinh nghiệm và dự án từ CV. Kết quả AI mang tính tham khảo.</p><h3>{cv.title}</h3><Button pending={mutation.isPending} onClick={()=>mutation.mutate()}><Sparkles size={16}/>{cv.parsed_json?'Phân tích lại':'Phân tích CV'}</Button><Feedback error={mutation.error?.message}/>{mutation.data?.parsed_json||cv.parsed_json ? <CVContent value={mutation.data?.parsed_json||cv.parsed_json}/>:<p className="muted">Chưa có kết quả phân tích.</p>}</section>
}

