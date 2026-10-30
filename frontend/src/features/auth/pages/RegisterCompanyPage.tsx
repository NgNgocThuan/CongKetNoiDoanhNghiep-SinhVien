import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Clock3 } from 'lucide-react'
import { publicHttp } from '@/lib/http'
import { toApiError } from '@/lib/api-error'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'

const schema = z.object({ company_name: z.string().trim().min(1, 'Nhập tên doanh nghiệp.').max(255), tax_code: z.string().trim().min(1, 'Nhập mã số thuế.').max(20), email: z.string().trim().email('Nhập email hợp lệ.'), password: z.string().min(8, 'Mật khẩu tối thiểu 8 ký tự.').max(128) })
export default function RegisterCompanyPage() {
  const [done, setDone] = useState(false), [error, setError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) })
  async function submit(data: z.infer<typeof schema>) {
    setError('')
    try { await publicHttp.post('/auth/register-company', data); setDone(true) } catch (err) { setError(toApiError(err).message) }
  }
  return <div className="auth-content"><p className="eyebrow">ĐỐI TÁC DOANH NGHIỆP</p><h1>Kết nối nhân tài.</h1>
    {done ? <div className="success-panel" role="status"><Clock3 size={32} /><h2>Đang chờ nhà trường phê duyệt</h2><p>Hồ sơ đăng ký đã được gửi. Bạn có thể đăng nhập sau khi tài khoản được duyệt.</p><Link to="/login" className="button button--secondary">Về đăng nhập</Link></div>
    : <><p className="muted auth-intro">Tạo tài khoản để đồng hành cùng thế hệ nhân sự mới.</p><form className="form-stack" noValidate onSubmit={handleSubmit(submit)}>
      {error && <p className="form-error" role="alert">{error}</p>}
      <Field id="company-name" label="Tên doanh nghiệp" error={errors.company_name?.message}><Input id="company-name" autoComplete="organization" {...register('company_name')} /></Field>
      <Field id="tax-code" label="Mã số thuế" error={errors.tax_code?.message}><Input id="tax-code" {...register('tax_code')} /></Field>
      <Field id="email" label="Email đăng nhập" error={errors.email?.message}><Input id="email" type="email" autoComplete="username" {...register('email')} /></Field>
      <Field id="password" label="Mật khẩu" error={errors.password?.message}><Input id="password" type="password" autoComplete="new-password" {...register('password')} /></Field>
      <Button type="submit" pending={isSubmitting}>Gửi đăng ký</Button>
    </form><p className="auth-register">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></p></>}
  </div>
}
