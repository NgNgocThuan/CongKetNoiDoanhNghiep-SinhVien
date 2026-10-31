import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/Button'
import { Feedback } from '@/features/student-jobs/components/StudentUI'
import { profileApi } from '../api'
import type { Profile } from '../types'
const nullableString=z.string().max(500).nullable()
const schema=z.object({avatar_url:nullableString,bio:z.string().nullable(),career_goal:z.string().nullable(),contact_email:z.union([z.email(),z.literal('')]).nullable(),contact_phone:z.string().max(20).nullable(),address:nullableString,linkedin_url:nullableString,github_url:nullableString,is_open_to_work:z.boolean(),show_gpa:z.boolean(),show_contact:z.boolean(),show_achievements:z.boolean()})
const fields=[['bio','Giới thiệu'],['career_goal','Mục tiêu nghề nghiệp'],['contact_email','Email liên hệ'],['contact_phone','Điện thoại'],['address','Địa chỉ'],['linkedin_url','LinkedIn (URL)'],['github_url','GitHub (URL)'],['avatar_url','Ảnh đại diện (URL)']] as const
export function ProfileForm({profile}:{profile:Profile}){
 const {register,handleSubmit,formState:{errors}}=useForm<z.infer<typeof schema>>({resolver:zodResolver(schema),defaultValues:profile})
 const action=useStudentAction(['student-profile'])
 return <form className="student-form" onSubmit={handleSubmit(async values=>{const body=Object.fromEntries(Object.entries(values).map(([key,value])=>[key,value===''?null:value]));await action.run(()=>profileApi.update(body))})}><h2>Thông tin tự khai</h2><div className="student-form-grid">{fields.map(([key,label])=><label key={key}>{label}{key==='bio'||key==='career_goal'?<textarea {...register(key)}/>:<input type={key==='contact_email'?'email':'text'} {...register(key)}/>}<span className="field__error">{errors[key]?.message}</span></label>)}</div><h2>Quyền riêng tư & tìm việc</h2><p className="muted">Các lựa chọn này quyết định thông tin được chia sẻ với doanh nghiệp trong gợi ý ứng viên.</p>{([['is_open_to_work','Sẵn sàng tìm việc','Cho phép xuất hiện trong gợi ý ứng viên.'],['show_gpa','Chia sẻ GPA','Cho phép doanh nghiệp xem điểm học tập.'],['show_contact','Chia sẻ liên hệ','Cho phép xem thông tin liên hệ tự khai.'],['show_achievements','Chia sẻ thành tích','Cho phép xem thành tích do nhà trường xác nhận.']] as const).map(([key,label,hint])=><label className="student-check" key={key}><input type="checkbox" {...register(key)}/><span><strong>{label}</strong><br/>{hint}</span></label>)}<Feedback {...action}/><Button type="submit" pending={action.pending}>Lưu thông tin & quyền riêng tư</Button></form>
}

