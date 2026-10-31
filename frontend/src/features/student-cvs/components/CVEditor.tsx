import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/Button'
import { Feedback } from '@/features/student-jobs/components/StudentUI'
import { cvsApi } from '../api'
import type { CV } from '../types'
const cvSchema=z.object({title:z.string().trim().min(1,'Nhập tiêu đề CV.').max(255),summary:z.string(),skills:z.string(),experience:z.string(),projects:z.string()})
function text(value:unknown){return typeof value==='string'?value:Array.isArray(value)?value.map(v=>typeof v==='string'?v:JSON.stringify(v)).join('\n'):value?JSON.stringify(value):''}
export function CVEditor({cv,onDone}:{cv?:CV;onDone:()=>void}){
 const content=cv?.content_json||{}
 const form=useForm<z.infer<typeof cvSchema>>({resolver:zodResolver(cvSchema),defaultValues:{title:cv?.title||'',summary:text(content.summary),skills:text(content.skills),experience:text(content.experience),projects:text(content.projects)}})
 const action=useStudentAction(['student-cvs'])
 return <form className="student-form" onSubmit={form.handleSubmit(async values=>{
 const content_json={...content,summary:values.summary,skills:values.skills.split('\n').map(v=>v.trim()).filter(Boolean),experience:values.experience,projects:values.projects}
 if(await action.run(()=>cv?cvsApi.update(cv.id,{title:values.title,...(cv.type==='ONLINE'?{content_json}:{})}):cvsApi.create({title:values.title,content_json})))onDone()
 })}><label>Tiêu đề CV *<input maxLength={255} {...form.register('title')}/><span className="field__error">{form.formState.errors.title?.message}</span></label>{(!cv||cv.type==='ONLINE') && <><p className="student-notice">Dữ liệu học thuật được tự điền từ nhà trường và không sửa trong CV.</p>{([['summary','Giới thiệu'],['skills','Kỹ năng (mỗi dòng một kỹ năng)'],['experience','Kinh nghiệm'],['projects','Dự án']] as const).map(([key,label])=><label key={key}>{label}<textarea {...form.register(key)}/></label>)}</>}<Feedback {...action}/><Button type="submit" pending={action.pending}>Lưu CV</Button></form>
}

