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
  Building,
  Clock,
  Eye,
  EyeOff,
  Globe,
  GraduationCap,
  Lock,
  Mail,
  MapPin,
  Phone,
  ShieldCheck,
  User,
} from 'lucide-react'
import { authApi } from '../api/auth.api'
import { toApiError } from '@/lib/api-error'

const schema = z.object({
  email: z.string().trim().email('Vui lòng nhập địa chỉ email hợp lệ.'),
  password: z.string().min(8, 'Mật khẩu khởi tạo cần tối thiểu 8 ký tự.').max(128),
  company_name: z.string().trim().min(1, 'Vui lòng nhập tên công ty đầy đủ theo ĐKKD.').max(255),
  tax_code: z.string().trim().min(1, 'Vui lòng nhập mã số thuế doanh nghiệp.').max(20),
  industry_id: z.string().optional(),
  website: z.string().trim().url('Website phải là URL hợp lệ (ví dụ: https://company.com)').optional().or(z.literal('')),
  address: z.string().trim().max(255).optional().or(z.literal('')),
  contact_name: z.string().trim().max(100).optional().or(z.literal('')),
  contact_phone: z.string().trim().max(20).optional().or(z.literal('')),
  terms: z.boolean().refine(val => val === true, 'Bạn cần đồng ý với cam kết pháp nhân để tiếp tục.'),
})

type FormFields = z.infer<typeof schema>

export default function RegisterCompanyPage() {
  const [done, setDone] = useState(false)
  const [registeredEmail, setRegisteredEmail] = useState('')
  const [registeredCompanyName, setRegisteredCompanyName] = useState('')
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormFields>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: '',
      password: '',
      company_name: '',
      tax_code: '',
      industry_id: '',
      website: '',
      address: '',
      contact_name: '',
      contact_phone: '',
      terms: true,
    },
  })

  const onSubmit = async (values: FormFields) => {
    setError('')
    try {
      await authApi.registerCompany({
        email: values.email,
        password: values.password,
        company_name: values.company_name,
        tax_code: values.tax_code,
        industry_id: values.industry_id ? Number(values.industry_id) : null,
        address: values.address || null,
        website: values.website || null,
        contact_name: values.contact_name || null,
        contact_phone: values.contact_phone || null,
      })
      setRegisteredEmail(values.email)
      setRegisteredCompanyName(values.company_name)
      setDone(true)
    } catch (err: unknown) {
      setError(toApiError(err).message)
    }
  }

  return (
    <div className="min-h-screen bg-[#FAF8FF] text-[#131B2E] flex flex-col justify-between">
      {/* TOP HEADER TỐI GIẢN */}
      <header className="bg-white border-b border-[#E2E8F0] sticky top-0 z-50 px-6 lg:px-12 py-3.5 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-[#00288E] flex items-center justify-center text-white shadow-sm ring-2 ring-blue-100">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight text-[#00288E]">Student Connect</span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-[#006A63] border border-teal-200">
                Kênh Đối tác
              </span>
            </div>
            <p className="text-xs text-[#444653] m-0">Cổng kết nối Thực tập &amp; Tuyển dụng Đại học 3 Bên</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center text-xs text-[#444653] space-x-1.5 border-r border-[#E2E8F0] pr-4">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Xác thực pháp lý &amp; Ký kết hợp tác MOU</span>
          </div>
          <Link
            to="/login"
            className="inline-flex items-center space-x-2 text-sm font-medium text-[#00288E] hover:text-[#001E6C] transition-colors px-4 py-2 rounded-full hover:bg-blue-50 border border-transparent hover:border-blue-100"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Quay lại Đăng nhập</span>
          </Link>
        </div>
      </header>

      {/* NỘI DUNG CHÍNH */}
      <main className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1">
        {done ? (
          /* ============================================================ */
          /* MÀN HÌNH SAU KHI GỬI THÀNH CÔNG: CHỜ DUYỆT (PENDING_APPROVAL) */
          /* ============================================================ */
          <div className="max-w-2xl mx-auto bg-white rounded-2xl border-2 border-amber-300 p-8 shadow-sm">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8" />
              </div>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#FEF3C7] text-[#D97706] border border-amber-300 mb-2">
                <span className="w-2 h-2 rounded-full bg-amber-500 mr-2 animate-pulse" />
                PENDING_APPROVAL
              </span>
              <h2 className="text-2xl font-extrabold text-[#131B2E] tracking-tight m-0">
                Hồ sơ đang chờ Nhà trường phê duyệt
              </h2>
              <p className="text-sm text-[#444653] mt-2 mb-0">
                Cảm ơn <strong>{registeredCompanyName || 'Quý Doanh nghiệp'}</strong> đã đăng ký trở thành đối tác thực tập của Nhà trường.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-[#92400E] leading-relaxed mb-6">
              <p className="m-0 font-medium">
                Tài khoản với email <strong>{registeredEmail}</strong> đã được khởi tạo ở trạng thái{' '}
                <span className="font-bold underline">Chờ phê duyệt</span>. Bạn <strong>chưa thể đăng nhập ngay</strong> cho đến khi Ban Hợp tác Doanh nghiệp hoàn tất đối soát Mã số thuế và kích hoạt tài khoản.
              </p>
            </div>

            {/* Tiến trình 3 bước */}
            <div className="space-y-4 mb-8">
              <h4 className="text-xs font-bold text-[#131B2E] uppercase tracking-wider mb-2">
                Tiến trình xét duyệt hồ sơ:
              </h4>
              <div className="flex items-start space-x-3 text-xs">
                <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  ✓
                </div>
                <div>
                  <span className="font-semibold text-[#131B2E]">Bước 1: Tiếp nhận biểu mẫu</span>
                  <p className="text-[#444653] text-[11px] mt-0.5 mb-0">Hồ sơ đã được lưu trữ an toàn trong cơ sở dữ liệu nhà trường.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 text-xs">
                <div className="w-6 h-6 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 ring-2 ring-amber-300">
                  2
                </div>
                <div>
                  <span className="font-semibold text-amber-900">Bước 2: Đối soát MST &amp; Pháp nhân (Đang xử lý)</span>
                  <p className="text-[#444653] text-[11px] mt-0.5 mb-0">
                    Phòng Đào tạo &amp; Hợp tác Doanh nghiệp kiểm tra thông tin trên Cổng thông tin Quốc gia về ĐKKD.
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3 text-xs">
                <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  3
                </div>
                <div>
                  <span className="font-semibold text-slate-500">Bước 3: Thông báo kết quả qua email</span>
                  <p className="text-slate-400 text-[11px] mt-0.5 mb-0">
                    Khi được phê duyệt, hệ thống sẽ gửi email kích hoạt quyền đăng tin tuyển dụng và tìm kiếm sinh viên.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#E2E8F0]">
              <span className="text-xs text-[#444653]">
                Thời gian xử lý: <strong>24 - 48 giờ làm việc</strong>
              </span>
              <Link
                to="/login"
                className="w-full sm:w-auto px-6 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white text-xs font-semibold text-center transition-colors"
              >
                Quay về trang Đăng nhập
              </Link>
            </div>
          </div>
        ) : (
          /* ============================================================ */
          /* FORM ĐĂNG KÝ DOANH NGHIỆP                                    */
          /* ============================================================ */
          <div>
            {/* Tiêu đề trang */}
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-[#00288E] text-xs font-medium mb-2">
                  <span className="w-2 h-2 rounded-full bg-[#00288E]" />
                  <span>Thủ tục tiếp nhận Doanh nghiệp • Học kỳ 2025</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#00288E] tracking-tight m-0">
                  Đăng ký Tài khoản Doanh nghiệp Đối tác
                </h1>
                <p className="text-sm text-[#444653] mt-1 mb-0">
                  Thiết lập tài khoản tuyển dụng chính thức để tiếp cận nguồn sinh viên được Nhà trường chứng thực và bảo trợ.
                </p>
              </div>

              <div className="flex items-center space-x-2 text-xs text-[#444653] bg-white px-3.5 py-2 rounded-xl border border-[#E2E8F0] shadow-xs">
                <span className="font-semibold text-[#131B2E]">Mã quy trình:</span>
                <span className="font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-700">REG-ENT-2025</span>
              </div>
            </div>

            {/* Layout 2 cột: 70% Form trái - 30% Callout Card phải */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              {/* CỘT TRÁI (8 COLS ~ 70%): FORM CHÍNH */}
              <section className="lg:col-span-8 bg-white rounded-2xl border border-[#E2E8F0] p-6 sm:p-8 shadow-sm">
                {error && (
                  <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3 text-red-700 text-xs" role="alert">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-red-600" />
                    <div>
                      <span className="font-bold block">Đăng ký chưa thành công:</span>
                      {error}
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-8" noValidate>
                  {/* PHẦN 1: THÔNG TIN BẮT BUỘC & TÀI KHOẢN */}
                  <div>
                    <div className="flex items-center justify-between pb-3 mb-5 border-b border-[#E2E8F0]">
                      <div className="flex items-center space-x-2.5">
                        <span className="w-7 h-7 rounded-lg bg-blue-100 text-[#00288E] flex items-center justify-center font-bold text-xs">
                          1
                        </span>
                        <h2 className="text-base font-bold text-[#131B2E] m-0">
                          Thông tin Bắt buộc &amp; Tài khoản
                        </h2>
                      </div>
                      <span className="text-xs text-red-500 font-medium">* Các trường có dấu hoa thị là bắt buộc</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                      {/* Email Doanh nghiệp */}
                      <div>
                        <label htmlFor="company-email" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Email Doanh nghiệp tuyển dụng <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <Mail className="w-4 h-4" />
                          </div>
                          <input
                            id="company-email"
                            type="email"
                            autoComplete="username"
                            placeholder="hr@domain-company.com"
                            className={`w-full pl-10 pr-3.5 py-2.5 bg-white border ${
                              errors.email ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                            } rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all`}
                            {...register('email')}
                          />
                        </div>
                        {errors.email ? (
                          <p className="text-[11px] text-red-600 mt-1 m-0">{errors.email.message}</p>
                        ) : (
                          <p className="text-[11px] text-[#444653] mt-1 m-0">Nên sử dụng email tên miền công ty để được duyệt nhanh hơn.</p>
                        )}
                      </div>

                      {/* Mật khẩu khởi tạo */}
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <label htmlFor="company-password" className="block text-xs font-semibold text-[#131B2E]">
                            Mật khẩu khởi tạo <span className="text-red-500">*</span>
                          </label>
                          <span className="text-[11px] text-slate-400 font-normal">Tối thiểu 8 ký tự</span>
                        </div>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <Lock className="w-4 h-4" />
                          </div>
                          <input
                            id="company-password"
                            type={showPassword ? 'text' : 'password'}
                            autoComplete="new-password"
                            placeholder="Nhập mật khẩu an toàn"
                            className={`w-full pl-10 pr-10 py-2.5 bg-white border ${
                              errors.password ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                            } rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all`}
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
                        {errors.password && (
                          <p className="text-[11px] text-red-600 mt-1 m-0">{errors.password.message}</p>
                        )}
                      </div>

                      {/* Tên công ty đầy đủ */}
                      <div>
                        <label htmlFor="company-name" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Tên công ty đầy đủ (theo Giấy phép ĐKKD) <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <Building className="w-4 h-4" />
                          </div>
                          <input
                            id="company-name"
                            type="text"
                            placeholder="VD: Công ty TNHH Phần mềm FPT"
                            className={`w-full pl-10 pr-3.5 py-2.5 bg-white border ${
                              errors.company_name ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                            } rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all`}
                            {...register('company_name')}
                          />
                        </div>
                        {errors.company_name && (
                          <p className="text-[11px] text-red-600 mt-1 m-0">{errors.company_name.message}</p>
                        )}
                      </div>

                      {/* Mã số thuế (MST) */}
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <label htmlFor="tax-code" className="block text-xs font-semibold text-[#131B2E]">
                            Mã số thuế doanh nghiệp (MST) <span className="text-red-500">*</span>
                          </label>
                          <span className="text-[10px] text-[#006A63] font-medium bg-teal-50 px-2 py-0.5 rounded-full border border-teal-100">
                            Cơ sở đối soát tự động
                          </span>
                        </div>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <Building className="w-4 h-4" />
                          </div>
                          <input
                            id="tax-code"
                            type="text"
                            placeholder="VD: 0101248141"
                            className={`w-full pl-10 pr-3.5 py-2.5 bg-white border ${
                              errors.tax_code ? 'border-red-400 bg-red-50/20' : 'border-[#E2E8F0]'
                            } rounded-xl text-sm font-mono text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all`}
                            {...register('tax_code')}
                          />
                        </div>
                        {errors.tax_code ? (
                          <p className="text-[11px] text-red-600 mt-1 m-0">{errors.tax_code.message}</p>
                        ) : (
                          <p className="text-[11px] text-[#444653] mt-1 m-0">Nhà trường sẽ tra cứu MST này trên Cổng thông tin Quốc gia về ĐKKD.</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* PHẦN 2: THÔNG TIN HỒ SƠ MỞ RỘNG (TÙY CHỌN) */}
                  <div>
                    <div className="flex items-center justify-between pb-3 mb-5 border-b border-[#E2E8F0]">
                      <div className="flex items-center space-x-2.5">
                        <span className="w-7 h-7 rounded-lg bg-teal-100 text-[#006A63] flex items-center justify-center font-bold text-xs">
                          2
                        </span>
                        <h2 className="text-base font-bold text-[#131B2E] m-0">
                          Thông tin Hồ sơ Mở rộng &amp; Liên hệ
                        </h2>
                      </div>
                      <span className="text-xs text-[#444653] bg-slate-100 px-2.5 py-1 rounded-full font-medium">Tùy chọn bổ sung</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                      {/* Lĩnh vực hoạt động */}
                      <div>
                        <label htmlFor="industry-select" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Lĩnh vực hoạt động chuyên ngành
                        </label>
                        <select
                          id="industry-select"
                          className="w-full px-3.5 py-2.5 bg-white border border-[#E2E8F0] rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#006A63]/20 focus:border-[#006A63] transition-all cursor-pointer"
                          {...register('industry_id')}
                        >
                          <option value="">-- Chọn lĩnh vực (Tùy chọn) --</option>
                          <option value="1">Công nghệ thông tin &amp; Phần mềm</option>
                          <option value="2">Tài chính - Ngân hàng - Fintech</option>
                          <option value="3">Kỹ thuật Điện tử - Viễn thông</option>
                          <option value="4">Truyền thông số &amp; Marketing</option>
                          <option value="5">Lĩnh vực sản xuất / Khác</option>
                        </select>
                      </div>

                      {/* Website công ty */}
                      <div>
                        <label htmlFor="company-website" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Website chính thức của công ty
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <Globe className="w-4 h-4" />
                          </div>
                          <input
                            id="company-website"
                            type="url"
                            placeholder="https://domain-company.com"
                            className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-[#E2E8F0] rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#006A63]/20 focus:border-[#006A63] transition-all"
                            {...register('website')}
                          />
                        </div>
                        {errors.website && (
                          <p className="text-[11px] text-red-600 mt-1 m-0">{errors.website.message}</p>
                        )}
                      </div>

                      {/* Địa chỉ trụ sở chính (Full span) */}
                      <div className="sm:col-span-2">
                        <label htmlFor="company-address" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Địa chỉ trụ sở chính / Văn phòng tuyển dụng
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <MapPin className="w-4 h-4" />
                          </div>
                          <input
                            id="company-address"
                            type="text"
                            placeholder="Số nhà, tên đường, Phường/Xã, Quận/Huyện, Tỉnh/TP"
                            className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-[#E2E8F0] rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#006A63]/20 focus:border-[#006A63] transition-all"
                            {...register('address')}
                          />
                        </div>
                      </div>

                      {/* Người liên hệ phụ trách */}
                      <div>
                        <label htmlFor="contact-name" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Họ tên người phụ trách tuyển dụng (HR/Lead)
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <User className="w-4 h-4" />
                          </div>
                          <input
                            id="contact-name"
                            type="text"
                            placeholder="VD: Trần Thị Mai Lan"
                            className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-[#E2E8F0] rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#006A63]/20 focus:border-[#006A63] transition-all"
                            {...register('contact_name')}
                          />
                        </div>
                      </div>

                      {/* Số điện thoại liên hệ */}
                      <div>
                        <label htmlFor="contact-phone" className="block text-xs font-semibold text-[#131B2E] mb-1.5">
                          Số điện thoại liên hệ trực tiếp
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                            <Phone className="w-4 h-4" />
                          </div>
                          <input
                            id="contact-phone"
                            type="tel"
                            placeholder="VD: 0982 123 456"
                            className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-[#E2E8F0] rounded-xl text-sm text-[#131B2E] focus:outline-none focus:ring-2 focus:ring-[#006A63]/20 focus:border-[#006A63] transition-all"
                            {...register('contact_phone')}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* ĐIỀU KHOẢN VÀ CAM KẾT */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-[#444653] space-y-2">
                    <label className="flex items-start space-x-2.5 cursor-pointer">
                      <input
                        type="checkbox"
                        className="mt-0.5 w-4 h-4 rounded text-[#006A63] focus:ring-[#006A63] border-slate-300"
                        {...register('terms')}
                      />
                      <span className="leading-relaxed">
                        Tôi cam kết thông tin Mã số thuế và Pháp nhân đại diện là hoàn toàn chính xác. Doanh nghiệp tuân thủ đúng quy định tiếp nhận thực tập sinh và bảo mật dữ liệu sinh viên của Nhà trường.
                      </span>
                    </label>
                    {errors.terms && <p className="text-red-600 m-0">{errors.terms.message}</p>}
                  </div>

                  {/* NÚT BẤM CHÍNH: GỬI HỒ SƠ ĐĂNG KÝ */}
                  <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="text-xs text-[#444653] text-center sm:text-left">
                      Đã có tài khoản đã được phê duyệt?{' '}
                      <Link to="/login" className="font-semibold text-[#00288E] hover:underline ml-1">
                        Đăng nhập ngay
                      </Link>
                    </div>

                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-[#006A63] hover:bg-[#00544E] disabled:opacity-50 text-white font-medium text-sm transition-all duration-150 shadow-md hover:shadow-lg flex items-center justify-center space-x-2.5 border-0 cursor-pointer"
                    >
                      <span>{isSubmitting ? 'Đang gửi hồ sơ…' : 'Gửi hồ sơ đăng ký'}</span>
                      {!isSubmitting && <ArrowRight className="w-4 h-4" />}
                    </button>
                  </div>
                </form>
              </section>

              {/* CỘT PHẢI (4 COLS ~ 30%): THẺ PREVIEW TRẠNG THÁI PENDING_APPROVAL */}
              <aside className="lg:col-span-4 space-y-6">
                <div className="bg-white rounded-2xl border-2 border-amber-300/80 p-6 shadow-sm relative overflow-hidden">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-semibold text-[#444653] uppercase tracking-wider">Mô phỏng sau khi gửi</span>
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#FEF3C7] text-[#D97706] border border-amber-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5 animate-pulse" />
                      PENDING_APPROVAL
                    </span>
                  </div>

                  {/* Banner giải thích */}
                  <div className="p-4 rounded-xl bg-amber-50/90 border border-amber-200/90 mb-5">
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 rounded-full bg-amber-200 text-amber-800 flex items-center justify-center shrink-0 mt-0.5">
                        <AlertTriangle className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <h3 className="text-xs font-bold text-amber-900 leading-snug m-0">
                          Hồ sơ đang chờ Nhà trường phê duyệt
                        </h3>
                        <p className="text-xs text-amber-800 mt-1 mb-0 leading-relaxed">
                          Sau khi gửi đăng ký, tài khoản <strong>chưa thể đăng nhập ngay</strong> cho tới khi Quản trị viên Nhà trường kiểm tra Mã số thuế và phê duyệt hồ sơ. Kết quả sẽ được thông báo qua email.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Tiến trình 3 bước */}
                  <div className="pt-1">
                    <h4 className="text-xs font-bold text-[#131B2E] mb-3.5 flex items-center space-x-1.5">
                      <ShieldCheck className="w-4 h-4 text-[#006A63]" />
                      <span>Tiến trình thẩm định hồ sơ:</span>
                    </h4>

                    <ol className="space-y-3.5 text-xs p-0 m-0 list-none">
                      <li className="flex items-start space-x-3">
                        <div className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                          ✓
                        </div>
                        <div>
                          <span className="font-semibold text-[#131B2E]">Bước 1: Tiếp nhận biểu mẫu</span>
                          <p className="text-[#444653] text-[11px] mt-0.5 mb-0">Hệ thống tạo mã định danh và lưu trữ hồ sơ doanh nghiệp.</p>
                        </div>
                      </li>

                      <li className="flex items-start space-x-3">
                        <div className="w-5 h-5 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5 ring-2 ring-amber-300">
                          2
                        </div>
                        <div>
                          <span className="font-semibold text-amber-900">Bước 2: Đối soát MST &amp; Pháp nhân (Đang chờ)</span>
                          <p className="text-[#444653] text-[11px] mt-0.5 mb-0">Ban Hợp tác Doanh nghiệp tra cứu MST trên Cổng QG và kiểm tra tính hợp pháp.</p>
                        </div>
                      </li>

                      <li className="flex items-start space-x-3">
                        <div className="w-5 h-5 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                          3
                        </div>
                        <div>
                          <span className="font-semibold text-slate-500">Bước 3: Kích hoạt &amp; Ký MOU trực tuyến</span>
                          <p className="text-slate-400 text-[11px] mt-0.5 mb-0">Gửi link kích hoạt qua email, mở quyền đăng tin tuyển dụng.</p>
                        </div>
                      </li>
                    </ol>
                  </div>

                  {/* Thông tin hỗ trợ */}
                  <div className="mt-6 pt-4 border-t border-[#E2E8F0] text-xs text-[#444653] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Thời gian phản hồi:</span>
                      <span className="font-semibold text-[#00288E]">Trong vòng 24 - 48 giờ làm việc</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Kênh giải đáp:</span>
                      <span className="font-medium text-slate-700">mou.partner@edu.vn</span>
                    </div>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        )}
      </main>

      {/* FOOTER */}
      <footer className="w-full bg-white border-t border-[#E2E8F0] py-4 mt-8">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#444653]">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-[#131B2E]">Student Connect Portal</span>
            <span>© 2025. Cổng kết nối Đào tạo &amp; Tuyển dụng Đại học 3 Bên.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/login" className="hover:text-[#00288E] transition-colors">
              Chính sách bảo mật
            </Link>
            <span className="text-gray-300">•</span>
            <span>Hỗ trợ kỹ thuật: support@edu.vn</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
