import { useState } from 'react'
import type { ReactNode } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  CheckCircle2,
  Flag,
  Send,
  X,
} from 'lucide-react'
import { reportsApi } from '../api/reports.api'
import type { ReportTargetType } from '../types/reports.types'
import { toApiError } from '@/lib/api-error'

export interface ReportDialogProps {
  targetType: ReportTargetType
  targetId: number
  targetTitle?: string
  trigger?: ReactNode
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

const CATEGORY_PRESETS: Record<ReportTargetType, string[]> = {
  JOB: [
    'Thu phí thực tập / Đặt cọc giữ chỗ sai quy định',
    'Mô tả công việc sai lệch / Ép làm việc trái chuyên ngành',
    'Nghi vấn lừa đảo / Mô hình đa cấp biến tướng',
    'Nội dung tuyển dụng phản cảm hoặc phân biệt đối xử',
    'Lý do vi phạm khác',
  ],
  COMPANY: [
    'Doanh nghiệp không có thật / Giả mạo pháp nhân',
    'Mã số thuế không hợp lệ hoặc đã ngừng hoạt động',
    'Vi phạm hợp đồng MOU / Chậm trả lương, phụ cấp',
    'Môi trường làm việc không an toàn hoặc quấy rối',
    'Lý do vi phạm khác',
  ],
  STUDENT: [
    'Làm giả chứng chỉ ngoại ngữ hoặc bảng điểm học thuật',
    'Gian lận hồ sơ năng lực và kinh nghiệm làm việc',
    'Bỏ thực tập không báo trước / Vi phạm kỷ luật',
    'Lý do vi phạm khác',
  ],
}

export function ReportDialog({
  targetType,
  targetId,
  targetTitle,
  trigger,
  open: controlledOpen,
  onOpenChange,
}: ReportDialogProps) {
  const queryClient = useQueryClient()
  const [internalOpen, setInternalOpen] = useState(false)
  const isControlled = controlledOpen !== undefined
  const isOpen = isControlled ? controlledOpen : internalOpen

  const setIsOpen = (next: boolean) => {
    if (!isControlled) setInternalOpen(next)
    onOpenChange?.(next)
  }

  const [category, setCategory] = useState(CATEGORY_PRESETS[targetType][0])
  const [details, setDetails] = useState('')
  const [terms, setTerms] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const mutation = useMutation({
    mutationFn: () => {
      const fullReason = details.trim()
        ? `[${category}] ${details.trim()}`
        : category
      return reportsApi.create({
        target_type: targetType,
        target_id: targetId,
        reason: fullReason.slice(0, 500),
      })
    },
    onSuccess: () => {
      setSuccess(true)
      void queryClient.invalidateQueries({ queryKey: ['reports'] })
      setTimeout(() => {
        setSuccess(false)
        setDetails('')
        setError('')
        setIsOpen(false)
      }, 1500)
    },
    onError: (err: unknown) => {
      setError(toApiError(err).message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!terms) {
      setError('Vui lòng đồng ý với cam kết tính trung thực để tiếp tục.')
      return
    }
    mutation.mutate()
  }

  const typeLabel =
    targetType === 'JOB'
      ? 'TIN TUYỂN DỤNG'
      : targetType === 'COMPANY'
        ? 'DOANH NGHIỆP'
        : 'SINH VIÊN'

  return (
    <>
      {trigger && (
        <span
          onClick={() => {
            setSuccess(false)
            setError('')
            setIsOpen(true)
          }}
          className="inline-block cursor-pointer"
        >
          {trigger}
        </span>
      )}

      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 text-left">
            {/* Header Modal */}
            <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/50">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-100 text-red-600 flex items-center justify-center shrink-0 mt-0.5">
                  <Flag className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-[#131B2E] m-0">
                    Báo cáo nội dung hoặc hành vi vi phạm
                  </h3>
                  <p className="text-xs text-[#444653] mt-1 mb-0 leading-relaxed">
                    Báo cáo của bạn sẽ được gửi trực tiếp đến Ban Quản trị Nhà trường để xác minh bảo mật danh tính tuyệt đối.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 rounded-full hover:bg-slate-200/60 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors border-0 bg-transparent cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Context Box */}
            <div className="px-6 pt-4">
              <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 truncate">
                  <span className="px-2 py-0.5 rounded-full bg-blue-100 text-[#00288E] font-bold text-[10px]">
                    {typeLabel}
                  </span>
                  <span className="font-semibold text-slate-800 truncate">
                    {targetTitle || `#ID-${targetId}`}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400 shrink-0">
                  ID: #{targetId}
                </span>
              </div>
            </div>

            {/* Body Form */}
            {success ? (
              <div className="p-8 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h4 className="font-bold text-sm text-[#131B2E] m-0">
                  Gửi báo cáo thành công!
                </h4>
                <p className="text-xs text-[#444653] m-0">
                  Cảm ơn bạn đã phản ánh. Ban Quản trị sẽ kiểm tra và phản hồi sớm nhất.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
                {error && (
                  <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Chọn phân loại vi phạm */}
                <div>
                  <label className="block font-semibold text-slate-800 mb-1.5">
                    Phân loại hành vi vi phạm <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={category}
                    onChange={e => setCategory(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all cursor-pointer"
                  >
                    {CATEGORY_PRESETS[targetType].map(item => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Mô tả chi tiết */}
                <div>
                  <label className="block font-semibold text-slate-800 mb-1.5">
                    Lý do và mô tả chi tiết hành vi vi phạm
                  </label>
                  <textarea
                    rows={3}
                    maxLength={420}
                    value={details}
                    onChange={e => setDetails(e.target.value)}
                    placeholder="Nêu rõ tình huống: thời gian trao đổi, nội dung yêu cầu thu tiền, người liên hệ qua Zalo/Email..."
                    className="w-full p-3 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] transition-all placeholder:text-slate-400"
                  />
                  <span className="text-[10px] text-slate-400 block text-right mt-1">
                    {details.length}/420 ký tự
                  </span>
                </div>

                {/* Cam kết tính trung thực */}
                <label className="flex items-start gap-2.5 cursor-pointer pt-1 text-slate-600 leading-relaxed select-none">
                  <input
                    type="checkbox"
                    checked={terms}
                    onChange={e => setTerms(e.target.checked)}
                    className="mt-0.5 w-4 h-4 rounded text-[#00288E] focus:ring-[#00288E] border-slate-300"
                  />
                  <span className="text-[11px]">
                    Tôi cam kết các thông tin phản ánh trên là hoàn toàn trung thực, có căn cứ và sẵn sàng chịu trách nhiệm trước Nhà trường về tính chính xác.
                  </span>
                </label>

                {/* Footer Buttons */}
                <div className="pt-2 flex items-center justify-end gap-2.5 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="px-4 py-2 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold transition-colors border-0 bg-transparent cursor-pointer"
                  >
                    Hủy bỏ
                  </button>
                  <button
                    type="submit"
                    disabled={mutation.isPending}
                    className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{mutation.isPending ? 'Đang gửi…' : 'Gửi báo cáo vi phạm'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  )
}
