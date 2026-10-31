import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Building2,
  Eye,
  EyeOff,
  GraduationCap,
  HelpCircle,
  Lock,
  Mail,
  PhoneCall,
  ShieldAlert,
  ShieldCheck,
  User as UserIcon,
} from 'lucide-react'
import { useAuth, roleHome } from '@/features/auth'
import { LoadingState } from '@/components/common/States'
import { toApiError } from '@/lib/api-error'

const schema = z.object({
  email: z.string().trim().email('Nhập địa chỉ email hợp lệ.'),
  password: z.string().min(1, 'Nhập mật khẩu.'),
  remember: z.boolean().optional(),
})

type Fields = z.infer<typeof schema>

interface AuthBannerState {
  code: string
  message: string
}

export default function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showPassword, setShowPassword] = useState(false)
  const [banner, setBanner] = useState<AuthBannerState | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Fields>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '', remember: false },
  })

  if (auth.status === 'loading') {
    return <LoadingState label="Đang kiểm tra phiên đăng nhập…" />
  }

  if (auth.user) {
    return <Navigate to={roleHome[auth.user.role]} replace />
  }

  const onSubmit = async (values: Fields) => {
    setBanner(null)
    try {
      const user = await auth.login({
        email: values.email,
        password: values.password,
        remember: values.remember,
      })
      const home = roleHome[user.role]
      const from: unknown = (location.state as { from?: unknown } | null)?.from
      const target = typeof from === 'string' && (from === home || from.startsWith(home + '/')) ? from : home
      navigate(target, { replace: true })
    } catch (err: unknown) {
      const apiErr = toApiError(err)
      setBanner({
        code: apiErr.code,
        message: apiErr.message,
      })
    }
  }

  return (
    <div className="w-full min-h-screen flex flex-col lg:flex-row bg-[#FAF8FF] text-[#131B2E]">
      {/* CỘT TRÁI (45%): ACADEMIC GRADIENT HERO & 3 ROLES */}
      <div
        className="lg:w-[45%] text-white p-8 lg:p-14 flex flex-col justify-between relative overflow-hidden shrink-0"
        style={{ background: 'linear-gradient(145deg, #001A61 0%, #00288E 50%, #173B9E 100%)' }}
      >
        {/* Glow ambient background elements */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-blue-500/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-0 w-80 h-80 rounded-full bg-teal-400/15 blur-3xl pointer-events-none" />

        {/* Top Branding */}
        <div className="relative z-10">
          <div className="inline-flex items-center gap-3.5 bg-white/10 backdrop-blur-md px-4 py-2.5 rounded-full border border-white/20 shadow-sm">
            <div className="w-9 h-9 rounded-full bg-white flex items-center justify-center text-[#00288E] shadow-sm font-bold text-lg">
              <GraduationCap className="w-5 h-5 text-[#00288E]" />
            </div>
            <div className="flex flex-col text-left">
              <span className="font-extrabold text-base tracking-tight leading-none text-white">Student Connect</span>
              <span className="text-[10px] uppercase font-bold tracking-widest text-teal-300 mt-1">Portal 3 Bên Độc Lập</span>
            </div>
          </div>

          <div className="mt-8 lg:mt-12 max-w-lg">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-200 border border-teal-400/30 text-xs font-semibold mb-3">
              <span className="w-2 h-2 rounded-full bg-teal-300 animate-pulse" />
              Hệ thống Quản trị &amp; Kết nối Việc làm Số
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold leading-tight text-white m-0">
              Cổng kết nối Thực tập &amp; Tuyển dụng Đại học
            </h1>
            <p className="mt-3 text-blue-100/90 text-sm lg:text-base leading-relaxed">
              Nền tảng chuẩn hóa dữ liệu tuyển dụng khép kín giữa Nhà trường, Doanh nghiệp đối tác và Sinh viên.
            </p>
          </div>
        </div>

        {/* Middle 3 Roles Highlight Cards */}
        <div className="my-6 lg:my-8 space-y-3 relative z-10 max-w-lg">
          {/* Sinh viên */}
          <div className="rounded-2xl p-4 bg-white/10 backdrop-blur-md border border-white/15 flex items-start gap-3.5 transition-all hover:bg-white/15">
            <div className="w-10 h-10 rounded-xl bg-blue-500/30 border border-blue-300/30 flex items-center justify-center shrink-0 text-white">
              <UserIcon className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-white m-0">Sinh viên &amp; Ứng viên</h3>
                <span className="text-[10px] font-semibold text-blue-200 bg-blue-400/20 px-2 py-0.5 rounded-full">Kênh Học kỳ</span>
              </div>
              <p className="text-xs text-blue-100/80 mt-1 mb-0 leading-relaxed">
                Tiếp cận nguồn tin tuyển dụng thực tập được nhà trường kiểm duyệt, gợi ý việc làm theo đúng chuyên ngành.
              </p>
            </div>
          </div>

          {/* Doanh nghiệp */}
          <div className="rounded-2xl p-4 bg-white/10 backdrop-blur-md border border-white/15 flex items-start gap-3.5 transition-all hover:bg-white/15">
            <div className="w-10 h-10 rounded-xl bg-teal-500/30 border border-teal-300/30 flex items-center justify-center shrink-0 text-teal-200">
              <Building2 className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-white m-0">Doanh nghiệp Đối tác</h3>
                <span className="text-[10px] font-semibold text-teal-200 bg-teal-400/20 px-2 py-0.5 rounded-full">Ký kết MOU</span>
              </div>
              <p className="text-xs text-blue-100/80 mt-1 mb-0 leading-relaxed">
                Đăng tải cơ hội nghề nghiệp, sàng lọc ứng viên chính quy và tương tác trực tiếp với sinh viên chuẩn đầu ra.
              </p>
            </div>
          </div>

          {/* Nhà trường */}
          <div className="rounded-2xl p-4 bg-white/10 backdrop-blur-md border border-white/15 flex items-start gap-3.5 transition-all hover:bg-white/15">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/30 border border-indigo-300/30 flex items-center justify-center shrink-0 text-indigo-200">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-white m-0">Nhà trường &amp; Khoa Đào tạo</h3>
                <span className="text-[10px] font-semibold text-indigo-200 bg-indigo-400/20 px-2 py-0.5 rounded-full">Quản trị &amp; Báo cáo</span>
              </div>
              <p className="text-xs text-blue-100/80 mt-1 mb-0 leading-relaxed">
                Theo dõi tiến độ thực tập toàn trường, phân tích khoảng trống kỹ năng và đánh giá hiệu quả hợp tác 3 bên.
              </p>
            </div>
          </div>
        </div>

        {/* Footer Cột Trái */}
        <div className="relative z-10 pt-4 border-t border-white/15 flex items-center justify-between text-xs text-blue-200/75">
          <span>© 2025 Student Connect Portal</span>
          <span className="flex items-center gap-1.5 text-teal-300 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-300" /> Phiên bản v2.4 Academic
          </span>
        </div>
      </div>

      {/* CỘT PHẢI (55%): FORM CARD ĐĂNG NHẬP */}
      <div className="lg:w-[55%] p-6 sm:p-10 lg:p-14 flex items-center justify-center">
        <div className="w-full max-w-[480px]">
          {/* Header hiển thị trên Mobile */}
          <div className="lg:hidden mb-6 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#00288E] flex items-center justify-center text-white">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-[#00288E] text-base block">Student Connect</span>
              <span className="text-xs text-gray-500">Hệ thống Cổng thông tin 3 Bên</span>
            </div>
          </div>

          {/* MAIN CARD */}
          <div className="bg-white rounded-2xl border border-[#E2E8F0] p-6 sm:p-8 shadow-sm">
            {/* Header Form */}
            <div className="mb-6">
              <div className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-[#00288E] border border-blue-100 mb-2.5">
                <Lock className="w-3.5 h-3.5 text-[#00288E]" />
                Cổng xác thực tập trung
              </div>
              <h2 className="text-2xl font-extrabold text-[#131B2E] tracking-tight m-0">Đăng nhập tài khoản</h2>
              <p className="text-xs sm:text-sm text-[#444653] mt-1.5 mb-0">
                Sử dụng email nhà trường hoặc tài khoản doanh nghiệp đối tác
              </p>
            </div>

            {/* BANNER THÔNG BÁO CẢNH BÁO TRẠNG THÁI TÀI KHOẢN (SEMANTIC BANNERS) */}
            {banner && (
              <div className="mb-6" id="account-status-banners" role="alert">
                {banner.code === 'ACCOUNT_PENDING_APPROVAL' || banner.code === 'PENDING_APPROVAL' ? (
                  /* MẪU 1: CẢNH BÁO VÀNG - CHỜ DUYỆT (PENDING_APPROVAL) */
                  <div className="rounded-xl bg-[#FEF3C7] border border-[#FDE68A] p-3.5 flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-[#F59E0B]/20 text-[#D97706] flex items-center justify-center shrink-0 mt-0.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 text-xs leading-relaxed text-[#92400E]">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-[#B45309]">Lưu ý tài khoản:</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FDE68A] text-[#92400E]">
                          PENDING_APPROVAL
                        </span>
                      </div>
                      Tài khoản doanh nghiệp đang chờ nhà trường phê duyệt. Quý đối tác vui lòng kiểm tra email hoặc liên hệ Ban Hợp tác Doanh nghiệp để hoàn tất xác thực MOU.
                    </div>
                  </div>
                ) : banner.code === 'ACCOUNT_LOCKED' || banner.code === 'LOCKED' ? (
                  /* MẪU 2: CẢNH BÁO ĐỎ - ĐÃ KHÓA (LOCKED) */
                  <div className="rounded-xl bg-[#FEE2E2] border border-[#FECACA] p-3.5 flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-[#EF4444]/20 text-[#DC2626] flex items-center justify-center shrink-0 mt-0.5">
                      <ShieldAlert className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 text-xs leading-relaxed text-[#991B1B]">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-[#B91C1C]">Thông báo khóa tài khoản:</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FECACA] text-[#991B1B]">
                          LOCKED
                        </span>
                      </div>
                      {banner.message || 'Tài khoản đã bị khóa do vi phạm chính sách của nhà trường.'} Vui lòng liên hệ Quản trị viên để được hỗ trợ khiếu nại.
                    </div>
                  </div>
                ) : banner.code === 'ACCOUNT_NOT_ACTIVE' || banner.code === 'PENDING_ACTIVATION' ? (
                  /* MẪU 3: CẢNH BÁO CAM - CHƯA KÍCH HOẠT */
                  <div className="rounded-xl bg-[#FFF7ED] border border-[#FFEDD5] p-3.5 flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center shrink-0 mt-0.5">
                      <AlertCircle className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 text-xs leading-relaxed text-[#9A3412]">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-bold text-[#C2410C]">Chưa kích hoạt:</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFEDD5] text-[#9A3412]">
                          PENDING_ACTIVATION
                        </span>
                      </div>
                      Tài khoản sinh viên chưa được kích hoạt. Vui lòng kiểm tra hộp thư email trường cấp và bấm vào đường dẫn kích hoạt để thiết lập mật khẩu ban đầu.
                    </div>
                  </div>
                ) : banner.code === 'TOO_MANY_ATTEMPTS' ? (
                  /* MẪU 4: BRUTE FORCE LOCKOUT (429) */
                  <div className="rounded-xl bg-[#FEF2F2] border border-[#FCA5A5] p-3.5 flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0 mt-0.5">
                      <AlertCircle className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 text-xs leading-relaxed text-[#991B1B]">
                      <span className="font-bold block mb-0.5">Tạm khóa do quá nhiều lần thử:</span>
                      {banner.message || 'Quá nhiều lần đăng nhập thất bại. Vui lòng chờ 1 phút trước khi thử lại.'}
                    </div>
                  </div>
                ) : (
                  /* MẪU CHUNG: LỖI THƯỜNG / SAI MẬT KHẨU */
                  <div className="rounded-xl bg-[#FEF2F2] border border-[#FECACA] p-3.5 flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-red-100 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                      <AlertCircle className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 text-xs leading-relaxed text-[#991B1B]">
                      <span className="font-bold block mb-0.5">Đăng nhập không thành công:</span>
                      {banner.message}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* FORM ĐĂNG NHẬP */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              {/* TRƯỜNG EMAIL */}
              <div>
                <label htmlFor="email" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                  Địa chỉ Email <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    aria-label="Địa chỉ email"
                    autoComplete="username"
                    placeholder="tennguoidung@school.edu.vn hoặc hr@company.com"
                    className={`w-full pl-10 pr-3.5 py-3 rounded-xl border ${
                      errors.email ? 'border-rose-400 bg-rose-50/30' : 'border-[#E2E8F0] bg-[#FAF8FF]/60'
                    } text-sm text-[#131B2E] placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all`}
                    {...register('email')}
                  />
                </div>
                {errors.email ? (
                  <p className="mt-1 text-xs text-rose-600 m-0">{errors.email.message}</p>
                ) : (
                  <p className="mt-1 text-[11px] text-[#444653] m-0">
                    Dành cho: Sinh viên (@edu.vn), Cán bộ trường hoặc Email Doanh nghiệp đối tác
                  </p>
                )}
              </div>

              {/* TRƯỜNG MẬT KHẨU */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="password" className="block text-xs font-semibold text-[#131B2E]">
                    Mật khẩu <span className="text-rose-500">*</span>
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-xs font-medium text-[#00288E] hover:underline transition-colors"
                  >
                    Quên mật khẩu?
                  </Link>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    aria-label="Mật khẩu"
                    autoComplete="current-password"
                    placeholder="Nhập mật khẩu của bạn"
                    className={`w-full pl-10 pr-11 py-3 rounded-xl border ${
                      errors.password ? 'border-rose-400 bg-rose-50/30' : 'border-[#E2E8F0] bg-[#FAF8FF]/60'
                    } text-sm text-[#131B2E] placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all`}
                    {...register('password')}
                  />
                  <button
                    type="button"
                    title={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-gray-400 hover:text-[#00288E] transition-colors cursor-pointer bg-transparent border-0"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-xs text-rose-600 m-0">{errors.password.message}</p>
                )}
              </div>

              {/* GHI NHỚ ĐĂNG NHẬP */}
              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded text-[#00288E] focus:ring-[#00288E] border-gray-300"
                    {...register('remember')}
                  />
                  <span className="text-xs text-[#444653]">Duy trì đăng nhập trong 30 ngày</span>
                </label>
              </div>

              {/* NÚT CHÍNH ĐĂNG NHẬP (FULL-PILL #00288E) */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3.5 px-6 rounded-full bg-[#00288E] hover:bg-[#001E6C] disabled:opacity-50 text-white font-bold text-sm tracking-wide shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer border-0"
                >
                  <span>{isSubmitting ? 'Đang xác thực…' : 'Đăng nhập'}</span>
                  {!isSubmitting && <ArrowRight className="w-4 h-4" />}
                </button>
              </div>
            </form>

            {/* FOOTER LIÊN KẾT ĐĂNG KÝ DOANH NGHIỆP */}
            <div className="mt-6 pt-5 border-t border-[#E2E8F0] text-center">
              <p className="text-xs text-[#444653] m-0">
                Bạn là đối tác tuyển dụng mới?{' '}
                <Link
                  to="/register-company"
                  className="font-bold text-[#006A63] hover:underline inline-flex items-center gap-1 ml-1"
                >
                  Đăng ký tài khoản Doanh nghiệp <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </p>
              <p className="text-[11px] text-gray-400 mt-2 mb-0">
                * Sinh viên và Giảng viên vui lòng đăng nhập trực tiếp bằng tài khoản định danh do Nhà trường cấp.
              </p>
            </div>
          </div>

          {/* TRỢ GIÚP DƯỚI CARD */}
          <div className="mt-6 flex items-center justify-center gap-6 text-xs text-gray-500">
            <Link to="/activate" className="hover:text-[#00288E] flex items-center gap-1.5 transition-colors">
              <HelpCircle className="w-3.5 h-3.5" /> Hướng dẫn kích hoạt tài khoản
            </Link>
            <span className="text-gray-300">•</span>
            <a href="tel:19001000" className="hover:text-[#00288E] flex items-center gap-1.5 transition-colors">
              <PhoneCall className="w-3.5 h-3.5" /> Hỗ trợ kỹ thuật Phòng Đào tạo
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
