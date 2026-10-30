import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowRight, Eye, EyeOff, LockKeyhole } from 'lucide-react'
import { useAuth, roleHome } from '@/features/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { LoadingState } from '@/components/common/States'
import { toApiError } from '@/lib/api-error'

const schema = z.object({ email: z.string().trim().email('Nhập địa chỉ email hợp lệ.'), password: z.string().min(1, 'Nhập mật khẩu.') })
type Fields = z.infer<typeof schema>
export default function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate(), location = useLocation()
  const [show, setShow] = useState(false), [error, setError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Fields>({ resolver: zodResolver(schema), defaultValues: { email: '', password: '' } })
  if (auth.status === 'loading') return <LoadingState label="Đang kiểm tra phiên đăng nhập…" />
  if (auth.user) return <Navigate to={roleHome[auth.user.role]} replace />
  const submit = async (values: Fields) => {
    setError('')
    try {
      const user = await auth.login(values), home = roleHome[user.role]
      const from: unknown = (location.state as { from?: unknown } | null)?.from
      navigate(typeof from === 'string' && (from === home || from.startsWith(home + '/')) ? from : home, { replace: true })
    } catch (err) { setError(toApiError(err).message) }
  }
  return <div className="auth-content"><span className="section-label"><span className="dot" /> CHÀO MỪNG TRỞ LẠI</span><h1>Hành trình tiếp theo<br />bắt đầu từ đây.</h1><p className="muted auth-intro">Đăng nhập để kết nối với cơ hội của bạn.</p>
    <form onSubmit={handleSubmit(submit)} className="form-stack" noValidate>
      {error && <div className="form-error" role="alert">{error}</div>}
      <Field id="email" label="Địa chỉ email" error={errors.email?.message}><Input id="email" type="email" autoComplete="username" placeholder="ban@truong.edu.vn" aria-invalid={!!errors.email} aria-describedby={errors.email ? 'email-error' : undefined} {...register('email')} /></Field>
      <Field id="password" label="Mật khẩu" error={errors.password?.message}><div className="password-input"><Input id="password" type={show ? 'text' : 'password'} autoComplete="current-password" placeholder="Nhập mật khẩu của bạn" aria-invalid={!!errors.password} aria-describedby={errors.password ? 'password-error' : undefined} {...register('password')} /><button className="icon-button" type="button" aria-label={show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} onClick={() => setShow(!show)}>{show ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></Field>
      <div className="form-links"><span><LockKeyhole size={14} /> Kết nối an toàn</span><Link to="/forgot-password">Quên mật khẩu?</Link></div>
      <Button type="submit" pending={isSubmitting} className="button--full">Đăng nhập <ArrowRight size={17} /></Button>
    </form>
    <div className="auth-separator"><span />Dành cho đối tác<span /></div><p className="auth-register">Bạn là doanh nghiệp? <Link to="/register-company">Đăng ký kết nối <ArrowUp /></Link></p><p className="auth-note">Sinh viên sử dụng tài khoản được nhà trường cấp qua email.</p>
  </div>
}
function ArrowUp() { return <span aria-hidden="true">↗</span> }
