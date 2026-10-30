import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft, MailCheck } from 'lucide-react'
import { authApi } from '../api/auth.api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { toApiError } from '@/lib/api-error'

const schema = z.object({ email: z.string().trim().email('Nhập địa chỉ email hợp lệ.') })
export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false), [error, setError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) })
  async function submit(values: z.infer<typeof schema>) {
    setError('')
    try { await authApi.forgotPassword(values.email); setSent(true) } catch (err) { setError(toApiError(err).message) }
  }
  return <div className="auth-content"><Link className="back-link" to="/login"><ArrowLeft size={16} /> Về đăng nhập</Link><h1>Quên mật khẩu?</h1>
    {sent ? <div className="success-panel" role="status"><MailCheck size={32} /><h2>Kiểm tra hộp thư của bạn</h2><p>Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi đến hòm thư của bạn.</p><p>Hãy kiểm tra cả mục thư rác.</p></div>
    : <><p className="muted auth-intro">Nhập email tài khoản để nhận hướng dẫn đặt lại mật khẩu.</p><form className="form-stack" onSubmit={handleSubmit(submit)} noValidate>
      {error && <p className="form-error" role="alert">{error}</p>}<Field id="email" label="Địa chỉ email" error={errors.email?.message}><Input id="email" autoComplete="email" type="email" {...register('email')} aria-invalid={!!errors.email} /></Field><Button type="submit" pending={isSubmitting}>Gửi hướng dẫn</Button></form></>}
  </div>
}
