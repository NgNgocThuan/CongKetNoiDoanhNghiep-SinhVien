import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { CheckCircle2 } from 'lucide-react'
import { authApi } from '../api/auth.api'
import { useAuth, roleHome } from '@/features/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { ErrorState } from '@/components/common/States'
import { toApiError } from '@/lib/api-error'

export default function PasswordPage({ mode }: { mode: 'activate' | 'reset' | 'change' }) {
  const [params] = useSearchParams(), { user } = useAuth()
  const [done, setDone] = useState(false), [error, setError] = useState('')
  const schema = z.object({ password: z.string().min(8, 'Mật khẩu cần ít nhất 8 ký tự.').max(128), confirm: z.string(), current: z.string() })
    .refine(data => data.password === data.confirm, { message: 'Mật khẩu xác nhận chưa khớp.', path: ['confirm'] })
    .refine(data => mode !== 'change' || !!data.current, { message: 'Nhập mật khẩu hiện tại.', path: ['current'] })
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema), defaultValues: { current: '', password: '', confirm: '' } })
  const token = params.get('token'), title = mode === 'activate' ? 'Kích hoạt tài khoản' : mode === 'reset' ? 'Đặt lại mật khẩu' : 'Đổi mật khẩu'
  async function submit(data: z.infer<typeof schema>) {
    setError('')
    try {
      if (mode === 'change') await authApi.changePassword(data.current, data.password)
      else if (mode === 'activate') await authApi.activate(token!, data.password)
      else await authApi.resetPassword(token!, data.password)
      setDone(true)
    } catch (err) { setError(toApiError(err).message) }
  }
  if (mode !== 'change' && !token) return <ErrorState title="Liên kết chưa hợp lệ" message="Hãy mở lại liên kết đầy đủ trong email." />
  return <div className={mode === 'change' ? 'card form-card' : 'auth-content'}><p className="eyebrow">BẢO MẬT TÀI KHOẢN</p><h1>{title}</h1>
    {done ? <div className="success-panel" role="status"><CheckCircle2 size={32} /><h2>Đã hoàn tất</h2><p>{mode === 'activate' ? 'Tài khoản của bạn đã sẵn sàng. Hãy đăng nhập để bắt đầu.' : 'Mật khẩu mới đã được lưu.'}</p><Link to={mode === 'change' && user ? roleHome[user.role] : '/login'} className="button button--primary">Tiếp tục</Link></div>
    : <form onSubmit={handleSubmit(submit)} className="form-stack" noValidate><p className="muted">Dùng mật khẩu riêng, tối thiểu 8 ký tự.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      {mode === 'change' && <Field id="current" label="Mật khẩu hiện tại" error={errors.current?.message}><Input id="current" type="password" autoComplete="current-password" {...register('current')} /></Field>}
      <Field id="new-password" label="Mật khẩu mới" error={errors.password?.message}><Input id="new-password" type="password" autoComplete="new-password" {...register('password')} /></Field>
      <Field id="confirm" label="Xác nhận mật khẩu" error={errors.confirm?.message}><Input id="confirm" type="password" autoComplete="new-password" {...register('confirm')} /></Field>
      <Button type="submit" pending={isSubmitting}>{title}</Button>
    </form>}
  </div>
}
