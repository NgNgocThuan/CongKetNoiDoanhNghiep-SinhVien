import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  GraduationCap,
  Info,
  Mail,
  Shield,
} from 'lucide-react'
import { authApi } from '../api/auth.api'
import { toApiError } from '@/lib/api-error'

const schema = z.object({
  email: z.string().trim().email('Vui lòng nhập địa chỉ email hợp lệ.'),
})

type FormFields = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState('')
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormFields>({
    resolver: zodResolver(schema),
    defaultValues: { email: '' },
  })

  const onSubmit = async (values: FormFields) => {
    setError('')
    try {
      await authApi.forgotPassword(values.email)
      setSubmittedEmail(values.email)
      setSent(true)
    } catch (err: unknown) {
      // Backend luôn trả 200 message trung lập, nhưng nếu network error hoặc lỗi 429 ta bắt lại
      setError(toApiError(err).message)
    }
  }

  return (
    <div className="min-h-screen bg-[#FAF8FF] text-[#131B2E] flex flex-col justify-between">
      {/* Top Header */}
      <header className="bg-white border-b border-[#E2E8F0] sticky top-0 z-50 px-6 lg:px-12 py-3.5 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-[#00288E] flex items-center justify-center text-white shadow-sm ring-2 ring-blue-100">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight text-[#00288E]">Student Connect</span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-[#00288E] border border-blue-200">
                Cổng Bảo Mật
              </span>
            </div>
            <p className="text-xs text-[#444653] m-0">Hệ thống Quản lý Mật khẩu &amp; Kích hoạt Tài khoản Xác thực 3 Bên</p>
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

      {/* Main Content Container */}
      <main className="w-full max-w-xl mx-auto px-4 sm:px-6 py-10 flex-1 flex items-center justify-center">
        <div className="w-full bg-white rounded-2xl border border-[#E2E8F0] p-6 sm:p-8 shadow-sm">
          {/* Header Card */}
          <div className="flex items-center justify-between pb-4 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-blue-50 text-[#00288E] flex items-center justify-center font-bold text-xs">
                A03
              </span>
              <div>
                <h1 className="text-lg font-bold text-[#131B2E] m-0">Quên mật khẩu</h1>
                <p className="text-[11px] text-[#444653] m-0">Khôi phục quyền truy cập an toàn</p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#DBEAFE] text-[#1E40AF] border border-[#BFDBFE]">
              Public Self-Service
            </span>
          </div>

          {/* Description */}
          <p className="text-xs text-[#444653] mt-4 mb-4 leading-relaxed">
            Nhập địa chỉ email liên kết với tài khoản sinh viên, doanh nghiệp đối tác hoặc cán bộ nhà trường để nhận liên kết xác thực đặt lại mật khẩu.
          </p>

          {error && (
            <div className="mb-4 p-3.5 rounded-xl bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-700" role="alert">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {sent ? (
            /* Hộp thông báo trung lập màu xanh nhạt (#DBEAFE, chữ #1E40AF) sau khi gửi */
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-[#DBEAFE] border border-[#BFDBFE] text-[#1E40AF]" role="status">
                <div className="flex items-start gap-2.5">
                  <Info className="w-5 h-5 mt-0.5 shrink-0 text-[#1E40AF]" />
                  <div>
                    <p className="text-xs font-bold text-[#1E40AF] m-0">Thông báo bảo mật hệ thống:</p>
                    <p className="text-xs mt-1 leading-relaxed text-[#1E40AF] m-0">
                      "Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu đã được gửi đến hòm thư của bạn. Vui lòng kiểm tra hộp thư."
                    </p>
                    {submittedEmail && (
                      <p className="text-[11px] mt-1.5 text-[#1E40AF]/80 m-0 font-mono">
                        Email yêu cầu: {submittedEmail}
                      </p>
                    )}
                  </div>
                </div>
                <div className="mt-3 pt-2.5 border-t border-[#BFDBFE]/60 flex items-center justify-between text-[11px] text-[#1E40AF]/80">
                  <span className="inline-flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5" />
                    Cơ chế bảo mật chống rà quét danh tính
                  </span>
                  <span className="font-medium">Hiệu lực link: 15 phút</span>
                </div>
              </div>

              {/* Hướng dẫn khi không nhận được email */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-[#444653] space-y-1.5">
                <div className="flex items-center gap-1.5 text-slate-700 font-semibold">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  <span>Không nhận được thư khôi phục?</span>
                </div>
                <p className="m-0">1. Kiểm tra kỹ mục Thư rác (Spam / Junk) hoặc Hộp thư Quảng cáo.</p>
                <p className="m-0">2. Đảm bảo dùng đúng email định danh trường hoặc email đại diện công ty.</p>
                <p className="m-0">3. Liên hệ Quản trị viên Nhà trường nếu tài khoản bị khóa hành chính.</p>
              </div>

              <div className="pt-2 flex justify-center">
                <Link
                  to="/login"
                  className="px-6 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white text-xs font-semibold transition-colors"
                >
                  Quay lại trang Đăng nhập
                </Link>
              </div>
            </div>
          ) : (
            /* Form nhập email */
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              <div>
                <label htmlFor="forgot-email" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                  Địa chỉ Email đã đăng ký <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    id="forgot-email"
                    type="email"
                    autoComplete="email"
                    placeholder="name@school.edu.vn hoặc hr@partner.com"
                    className={`w-full pl-10 pr-4 py-2.5 bg-white border ${
                      errors.email ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                    } rounded-xl text-xs text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-colors`}
                    {...register('email')}
                  />
                </div>
                {errors.email ? (
                  <p className="text-[11px] text-red-600 mt-1 m-0">{errors.email.message}</p>
                ) : (
                  <p className="text-[11px] text-[#444653] mt-1.5 m-0 flex items-center gap-1">
                    <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>Hỗ trợ cả email sinh viên (@edu.vn) và email doanh nghiệp.</span>
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 bg-[#00288E] hover:bg-[#001E6C] disabled:opacity-50 text-white text-xs font-semibold rounded-full transition-all shadow-sm flex items-center justify-center gap-2 cursor-pointer border-0"
              >
                <span>{isSubmitting ? 'Đang gửi hướng dẫn…' : 'Gửi hướng dẫn đặt lại'}</span>
                {!isSubmitting && <ArrowRight className="w-3.5 h-3.5" />}
              </button>
            </form>
          )}

          {/* Hộp giải thích chính sách bảo mật chống rà quét danh tính */}
          {!sent && (
            <div className="mt-5 p-3 rounded-xl bg-blue-50/60 border border-blue-100 text-[11px] text-[#1E40AF] flex items-start gap-2">
              <Shield className="w-4 h-4 shrink-0 text-[#1E40AF] mt-0.5" />
              <div>
                <span className="font-bold block">Chính sách bảo mật NIST SP 800-63B:</span>
                Hệ thống luôn trả về thông báo trung lập để bảo vệ quyền riêng tư và chống rà quét danh tính người dùng.
              </div>
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-[#E2E8F0] text-center">
            <Link
              to="/login"
              className="text-xs font-semibold text-[#00288E] hover:underline inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Quay lại trang Đăng nhập chính
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
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
    </div>
  )
}
