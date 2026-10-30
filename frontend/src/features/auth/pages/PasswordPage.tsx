import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  GraduationCap,
  KeyRound,
  Lock,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  XCircle,
} from 'lucide-react'
import { authApi } from '../api/auth.api'
import { useAuth, roleHome } from '@/features/auth'
import { toApiError } from '@/lib/api-error'

interface PasswordPageProps {
  mode: 'activate' | 'reset' | 'change'
}

export default function PasswordPage({ mode }: PasswordPageProps) {
  const [params] = useSearchParams()
  const { user } = useAuth()
  const token = params.get('token')

  const [done, setDone] = useState(false)
  const [error, setError] = useState<{ code: string; message: string } | null>(null)
  const [showCurrent, setShowCurrent] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const schema = z
    .object({
      current: z.string(),
      password: z.string().min(8, 'Mật khẩu cần ít nhất 8 ký tự.').max(128),
      confirm: z.string(),
    })
    .refine(data => data.password === data.confirm, {
      message: 'Mật khẩu xác nhận chưa khớp với mật khẩu mới.',
      path: ['confirm'],
    })
    .refine(data => mode !== 'change' || (data.current && data.current.length > 0), {
      message: 'Vui lòng nhập mật khẩu hiện tại.',
      path: ['current'],
    })

  type FormValues = z.infer<typeof schema>

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { current: '', password: '', confirm: '' },
  })

  const pwdValue = watch('password') || ''

  // Tính điểm độ mạnh mật khẩu (0 - 4)
  const getStrength = (pwd: string) => {
    let score = 0
    if (pwd.length >= 8) score += 1
    if (/[A-Z]/.test(pwd)) score += 1
    if (/[0-9]/.test(pwd)) score += 1
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1
    return score
  }

  const strength = getStrength(pwdValue)

  const onSubmit = async (data: FormValues) => {
    setError(null)
    try {
      if (mode === 'change') {
        await authApi.changePassword(data.current, data.password)
      } else if (mode === 'activate') {
        if (!token) throw new Error('Token kích hoạt không tồn tại.')
        await authApi.activate(token, data.password)
      } else {
        if (!token) throw new Error('Token đặt lại mật khẩu không tồn tại.')
        await authApi.resetPassword(token, data.password)
      }
      setDone(true)
    } catch (err: unknown) {
      const apiErr = toApiError(err)
      setError({ code: apiErr.code, message: apiErr.message })
    }
  }

  // Tiêu đề & Cấu hình theo mode
  const isActivate = mode === 'activate'
  const isReset = mode === 'reset'
  const isChange = mode === 'change'

  const title = isActivate
    ? 'Kích hoạt tài khoản sinh viên'
    : isReset
      ? 'Đặt lại mật khẩu mới'
      : 'Đổi mật khẩu tài khoản'

  // Kiểm tra thiếu token cho activate & reset
  if (!isChange && !token) {
    return (
      <div className="min-h-screen bg-[#FAF8FF] flex flex-col justify-center items-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl border border-red-200 p-8 shadow-sm text-center">
          <div className="w-14 h-14 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-8 h-8" />
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-50 text-red-600 border border-red-200 mb-2 inline-block">
            TOKEN_MISSING
          </span>
          <h2 className="text-xl font-bold text-[#131B2E] m-0">Đường dẫn không hợp lệ</h2>
          <p className="text-xs text-[#444653] mt-2 mb-6 leading-relaxed">
            Liên kết xác thực thiếu mã token. Vui lòng kiểm tra lại toàn bộ đường dẫn trong email được gửi từ Nhà trường.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white text-xs font-semibold transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Về trang Đăng nhập
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className={isChange ? 'w-full max-w-2xl mx-auto py-6' : 'min-h-screen bg-[#FAF8FF] text-[#131B2E] flex flex-col justify-between'}>
      {/* Header cho trang công khai (activate & reset) */}
      {!isChange && (
        <header className="bg-white border-b border-[#E2E8F0] sticky top-0 z-50 px-6 lg:px-12 py-3.5 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-xl bg-[#00288E] flex items-center justify-center text-white shadow-sm ring-2 ring-blue-100">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-[#00288E]">Student Connect</span>
                <span
                  className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full ${
                    isActivate ? 'bg-teal-50 text-[#006A63] border border-teal-200' : 'bg-blue-50 text-[#00288E] border border-blue-200'
                  }`}
                >
                  {isActivate ? 'Kênh Onboarding Sinh viên' : 'Cổng Khôi phục Mật khẩu'}
                </span>
              </div>
              <p className="text-xs text-[#444653] m-0">Hệ thống Xác thực &amp; Bảo mật Tập trung</p>
            </div>
          </div>

          <Link
            to="/login"
            className="inline-flex items-center space-x-2 text-sm font-medium text-[#00288E] hover:text-[#001E6C] transition-colors px-4 py-2 rounded-full hover:bg-blue-50 border border-transparent hover:border-blue-100"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Quay lại Đăng nhập</span>
          </Link>
        </header>
      )}

      {/* Main Container */}
      <main className={isChange ? '' : 'w-full max-w-xl mx-auto px-4 sm:px-6 py-10 flex-1 flex items-center justify-center'}>
        <div
          className={`w-full bg-white rounded-2xl border ${
            isActivate ? 'border-2 border-teal-600/30' : 'border-[#E2E8F0]'
          } p-6 sm:p-8 shadow-sm`}
        >
          {/* Header Card */}
          <div className="flex items-center justify-between pb-4 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2.5">
              <span
                className={`w-8 h-8 rounded-lg ${
                  isActivate
                    ? 'bg-teal-50 text-[#006A63]'
                    : isChange
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'bg-blue-50 text-[#00288E]'
                } flex items-center justify-center font-bold text-xs`}
              >
                {isActivate ? 'A05' : isChange ? 'A06' : 'A04'}
              </span>
              <div>
                <h1 className="text-lg font-bold text-[#131B2E] m-0">{title}</h1>
                <p className="text-[11px] text-[#444653] m-0">
                  {isActivate
                    ? 'Thiết lập mật khẩu khởi tạo cho tài khoản mới'
                    : isChange
                      ? 'Cập nhật mật khẩu bảo vệ tài khoản'
                      : 'Đặt lại mật khẩu truy cập hệ thống'}
                </p>
              </div>
            </div>

            <span
              className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                isActivate
                  ? 'bg-[#CCFBF1] text-[#0F766E] border border-[#99F6E4]'
                  : isChange
                    ? 'bg-[#E0E7FF] text-[#3730A3] border border-[#C7D2FE]'
                    : 'bg-[#DBEAFE] text-[#1E40AF] border border-[#BFDBFE]'
              }`}
            >
              {isActivate ? 'Xác thực Token' : isChange ? 'Authenticated Session' : 'Xác thực Email'}
            </span>
          </div>

          {/* Lời chào onboarding cho sinh viên khi kích hoạt (A05) */}
          {isActivate && !done && (
            <div className="mt-4 p-3.5 rounded-xl bg-[#F0FDFA] border border-[#CCFBF1]">
              <div className="flex items-start gap-2.5">
                <div className="w-8 h-8 rounded-full bg-teal-100 text-[#006A63] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  <UserCheck className="w-4 h-4" />
                </div>
                <div className="text-xs">
                  <span className="font-bold text-[#131B2E] block">Chào mừng bạn gia nhập Student Connect!</span>
                  <p className="text-[11px] text-[#444653] mt-1 mb-2 leading-relaxed">
                    Hồ sơ học thuật của bạn đã được Phòng Đào tạo xác nhận. Vui lòng thiết lập mật khẩu khởi tạo để kích hoạt quyền nộp hồ sơ thực tập và nhận lời mời tuyển dụng.
                  </p>
                  <div className="inline-flex items-center gap-1.5 text-[10px] text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                    <span>Chỉ đặt mật khẩu. Không thể tự sửa điểm và thông tin học thuật.</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* THÔNG BÁO LỖI TOKEN HOẶC LỖI TỪ BACKEND */}
          {error && (
            <div className="mt-4 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700" role="alert">
              <div className="flex items-start gap-2.5">
                <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0 text-red-600" />
                <div className="flex-1 text-xs">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="font-bold text-red-800">
                      {error.code === 'TOKEN_EXPIRED'
                        ? 'Token đã hết hạn'
                        : error.code === 'TOKEN_USED'
                          ? 'Token đã được sử dụng'
                          : error.code === 'TOKEN_INVALID'
                            ? 'Token không hợp lệ'
                            : 'Không thể hoàn tất thao tác:'}
                    </span>
                    <span className="text-[10px] font-bold bg-white text-red-600 px-1.5 py-0.5 rounded border border-red-200">
                      {error.code}
                    </span>
                  </div>
                  <p className="mt-1 mb-2 leading-relaxed text-red-700">{error.message}</p>
                  {!isChange && (
                    <div className="pt-2 border-t border-red-200 flex items-center justify-between text-[11px]">
                      <span>Thời hạn token: 15 - 48 giờ kể từ lúc tạo</span>
                      <Link to="/forgot-password" className="font-semibold underline hover:text-red-900">
                        Yêu cầu gửi lại link mới →
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* MÀN HÌNH HOÀN TẤT THÀNH CÔNG */}
          {done ? (
            <div className="mt-6 text-center space-y-4" role="status">
              <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#131B2E] m-0">
                  {isActivate ? 'Kích hoạt tài khoản thành công!' : 'Cập nhật mật khẩu thành công!'}
                </h3>
                <p className="text-xs text-[#444653] mt-1.5 mb-0 max-w-sm mx-auto leading-relaxed">
                  {isActivate
                    ? 'Tài khoản sinh viên đã sẵn sàng hoạt động. Bạn có thể đăng nhập ngay để cập nhật CV và ứng tuyển việc làm.'
                    : 'Mật khẩu mới đã được lưu vào hệ thống an toàn. Email thông báo bảo mật đã được gửi tới tài khoản của bạn.'}
                </p>
              </div>

              <div className="pt-2">
                <Link
                  to={isChange && user ? roleHome[user.role] : '/login'}
                  className={`inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-full ${
                    isActivate ? 'bg-[#006A63] hover:bg-[#00544E]' : 'bg-[#00288E] hover:bg-[#001E6C]'
                  } text-white text-xs font-semibold transition-colors`}
                >
                  <span>{isChange ? 'Quay lại Bảng điều khiển' : 'Đăng nhập ngay'}</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ) : (
            /* FORM NHẬP MẬT KHẨU */
            <form onSubmit={handleSubmit(onSubmit)} className="mt-5 space-y-4" noValidate>
              {/* Mật khẩu cũ (chỉ dành cho Change Password) */}
              {isChange && (
                <div>
                  <label htmlFor="old-password" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                    Mật khẩu hiện tại <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      id="old-password"
                      type={showCurrent ? 'text' : 'password'}
                      autoComplete="current-password"
                      placeholder="Nhập mật khẩu đang sử dụng"
                      className={`w-full pl-10 pr-10 py-2.5 bg-white border ${
                        errors.current ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                      } rounded-xl text-xs text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-colors`}
                      {...register('current')}
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrent(!showCurrent)}
                      aria-label={showCurrent ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 bg-transparent border-0 cursor-pointer"
                    >
                      {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.current && (
                    <p className="text-[11px] text-red-600 mt-1 m-0">{errors.current.message}</p>
                  )}
                </div>
              )}

              {/* Mật khẩu mới */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="new-password" className="block text-xs font-semibold text-[#131B2E]">
                    {isActivate ? 'Mật khẩu khởi tạo' : 'Mật khẩu mới'} <span className="text-red-500">*</span>
                  </label>
                  <span className="text-[11px] text-[#444653]">Tối thiểu 8 ký tự</span>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    id="new-password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    placeholder="Mật khẩu có chữ hoa, số và ký tự đặc biệt"
                    className={`w-full pl-10 pr-10 py-2.5 bg-white border ${
                      errors.password ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                    } rounded-xl text-xs text-[#131B2E] font-mono focus:outline-none focus:ring-2 ${
                      isActivate ? 'focus:ring-[#006A63]/20 focus:border-[#006A63]' : 'focus:ring-[#00288E]/20 focus:border-[#00288E]'
                    } transition-colors`}
                    {...register('password')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 bg-transparent border-0 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Thanh đo độ mạnh mật khẩu */}
                {pwdValue.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <div className="flex items-center gap-1.5">
                      <div className={`h-1 flex-1 rounded-full ${strength >= 1 ? 'bg-rose-500' : 'bg-slate-200'}`} />
                      <div className={`h-1 flex-1 rounded-full ${strength >= 2 ? 'bg-amber-500' : 'bg-slate-200'}`} />
                      <div className={`h-1 flex-1 rounded-full ${strength >= 3 ? 'bg-teal-500' : 'bg-slate-200'}`} />
                      <div className={`h-1 flex-1 rounded-full ${strength >= 4 ? 'bg-emerald-500' : 'bg-slate-200'}`} />
                    </div>
                    <span className="text-[10px] text-[#444653] block text-right font-medium">
                      Độ an toàn: {strength <= 1 ? 'Yếu' : strength <= 2 ? 'Trung bình' : strength <= 3 ? 'Khá' : 'Rất mạnh (Tối ưu)'}
                    </span>
                  </div>
                )}

                {errors.password && (
                  <p className="text-[11px] text-red-600 mt-1 m-0">{errors.password.message}</p>
                )}
              </div>

              {/* Xác nhận mật khẩu mới */}
              <div>
                <label htmlFor="confirm-password" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                  Xác nhận mật khẩu mới <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    id="confirm-password"
                    type={showConfirm ? 'text' : 'password'}
                    autoComplete="new-password"
                    placeholder="Nhập lại chính xác mật khẩu ở trên"
                    className={`w-full pl-10 pr-10 py-2.5 bg-white border ${
                      errors.confirm ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                    } rounded-xl text-xs text-[#131B2E] font-mono focus:outline-none focus:ring-2 ${
                      isActivate ? 'focus:ring-[#006A63]/20 focus:border-[#006A63]' : 'focus:ring-[#00288E]/20 focus:border-[#00288E]'
                    } transition-colors`}
                    {...register('confirm')}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    aria-label={showConfirm ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 bg-transparent border-0 cursor-pointer"
                  >
                    {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.confirm && (
                  <p className="text-[11px] text-red-600 mt-1 m-0">{errors.confirm.message}</p>
                )}
              </div>

              {/* Ghi chú chính sách xác thực session */}
              {isChange && (
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-[#444653] space-y-1">
                  <div className="flex items-center gap-1.5 text-[#131B2E] font-semibold">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#00288E]" />
                    <span>Chính sách bảo mật phiên làm việc:</span>
                  </div>
                  <p className="m-0 text-slate-600">
                    • <strong>Không yêu cầu mã OTP</strong> khi bạn đang đăng nhập phiên hợp lệ.
                  </p>
                  <p className="m-0 text-slate-600">
                    • Hệ thống tự động thu hồi phiên đăng nhập trên các thiết bị lạ sau khi cập nhật thành công.
                  </p>
                </div>
              )}

              {/* Nút Submit */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`w-full py-2.5 px-4 ${
                    isActivate ? 'bg-[#006A63] hover:bg-[#00544E]' : 'bg-[#00288E] hover:bg-[#001E6C]'
                  } disabled:opacity-50 text-white text-xs font-semibold rounded-full transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer border-0`}
                >
                  <span>
                    {isSubmitting
                      ? 'Đang xử lý…'
                      : isActivate
                        ? 'Kích hoạt tài khoản'
                        : isChange
                          ? 'Cập nhật mật khẩu'
                          : 'Lưu mật khẩu mới'}
                  </span>
                  {!isSubmitting && <ArrowRight className="w-3.5 h-3.5" />}
                </button>
              </div>
            </form>
          )}

          {/* Footer Card */}
          {!isChange && (
            <div className="mt-6 pt-4 border-t border-[#E2E8F0] text-center">
              <Link
                to="/login"
                className="text-xs font-semibold text-[#00288E] hover:underline inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Quay lại trang Đăng nhập
              </Link>
            </div>
          )}
        </div>
      </main>

      {/* Footer cho trang công khai */}
      {!isChange && (
        <footer className="w-full bg-white border-t border-[#E2E8F0] py-4">
          <div className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#444653]">
            <div>
              <span className="font-semibold text-[#131B2E]">Student Connect Portal</span> • © 2025. Cổng kết nối Đào tạo &amp; Tuyển dụng Đại học 3 Bên.
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login" className="hover:text-[#00288E] transition-colors">
                Chính sách bảo mật mật khẩu
              </Link>
            </div>
          </div>
        </footer>
      )}
    </div>
  )
}
