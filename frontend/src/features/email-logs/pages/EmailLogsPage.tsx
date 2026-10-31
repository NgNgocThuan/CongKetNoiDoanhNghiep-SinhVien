import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  Clock,
  Filter,
  Mail,
  MailCheck,
  MailX,
  RotateCcw,
  XCircle,
} from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Card } from '@/components/ui/Card'
import { emailLogsApi } from '../api/email-logs.api'
import type { EmailStatus } from '../types/email-logs.types'
import { toApiError } from '@/lib/api-error'

function formatDate(isoString?: string | null) {
  if (!isoString) return '—'
  const date = new Date(isoString)
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const TEMPLATE_TYPE_LABELS: Record<string, string> = {
  ACCOUNT_ACTIVATION: 'Kích hoạt tài khoản',
  PASSWORD_RESET: 'Đặt lại mật khẩu',
  COMPANY_APPROVED: 'Phê duyệt doanh nghiệp',
  COMPANY_REJECTED: 'Từ chối doanh nghiệp',
  JOB_APPROVED: 'Phê duyệt tin tuyển dụng',
  JOB_REJECTED: 'Từ chối tin tuyển dụng',
  ACCOUNT_LOCKED: 'Khóa tài khoản',
  ACCOUNT_UNLOCKED: 'Mở khóa tài khoản',
  REPORT_HANDLED: 'Xử lý báo cáo vi phạm',
}

export default function EmailLogsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<EmailStatus | 'ALL'>('ALL')
  const [typeFilter, setTypeFilter] = useState<string>('ALL')
  const [feedbackMessage, setFeedbackMessage] = useState('')

  // Query list
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['admin-email-logs', page, statusFilter, typeFilter],
    queryFn: () =>
      emailLogsApi.list({
        page,
        size: 10,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        type: typeFilter === 'ALL' ? undefined : typeFilter,
      }),
  })

  // Summary counts
  const sentCountQuery = useQuery({
    queryKey: ['admin-email-logs', 'count', 'SENT'],
    queryFn: () => emailLogsApi.list({ status: 'SENT', size: 1 }),
  })
  const failedCountQuery = useQuery({
    queryKey: ['admin-email-logs', 'count', 'FAILED'],
    queryFn: () => emailLogsApi.list({ status: 'FAILED', size: 1 }),
  })
  const pendingCountQuery = useQuery({
    queryKey: ['admin-email-logs', 'count', 'PENDING'],
    queryFn: () => emailLogsApi.list({ status: 'PENDING', size: 1 }),
  })

  // Bulk retry mutation
  const retryMutation = useMutation({
    mutationFn: () => emailLogsApi.retry(),
    onSuccess: res => {
      setFeedbackMessage(res.message)
      void queryClient.invalidateQueries({ queryKey: ['admin-email-logs'] })
      setTimeout(() => setFeedbackMessage(''), 5000)
    },
    onError: (err: unknown) => {
      setFeedbackMessage(`Thử lại thất bại: ${toApiError(err).message}`)
    },
  })

  const sentCount = sentCountQuery.data?.total ?? 0
  const failedCount = failedCountQuery.data?.total ?? 0
  const pendingCount = pendingCountQuery.data?.total ?? 0
  const totalCount = sentCount + failedCount + pendingCount

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <PageHeader
          eyebrow="QUẢN TRỊ NHÀ TRƯỜNG"
          title="Nhật ký Gửi Email Hệ thống"
          description="Theo dõi lịch sử email kích hoạt, đặt lại mật khẩu và thông báo tự động đến người dùng."
        />

        <button
          type="button"
          disabled={retryMutation.isPending || failedCount === 0}
          onClick={() => retryMutation.mutate()}
          className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold text-xs flex items-center gap-2 shadow-xs transition-colors cursor-pointer border-0 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RotateCcw className={`w-4 h-4 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
          <span>
            {retryMutation.isPending
              ? 'Đang xếp hàng…'
              : failedCount > 0
                ? `Xếp hàng gửi lại ${failedCount} email lỗi`
                : 'Xếp hàng gửi lại toàn bộ email lỗi'}
          </span>
        </button>
      </div>

      {/* Banner thông báo kết quả Retry */}
      {feedbackMessage && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-[#00288E] flex items-center justify-between text-xs font-semibold animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#00288E]" />
            <span>{feedbackMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setFeedbackMessage('')}
            className="text-slate-400 hover:text-slate-700 bg-transparent border-0 cursor-pointer"
          >
            Đóng
          </button>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div
          onClick={() => {
            setStatusFilter('ALL')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            statusFilter === 'ALL'
              ? 'bg-blue-50/70 border-[#00288E] shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-2">
            <span>TỔNG EMAIL ĐÃ PHÁT</span>
            <Mail className="w-4 h-4 text-[#00288E]" />
          </div>
          <div className="text-2xl font-bold text-[#131B2E]">{totalCount}</div>
          <p className="text-[11px] text-slate-400 mt-1 mb-0">Tất cả thông báo qua SMTP</p>
        </div>

        <div
          onClick={() => {
            setStatusFilter('SENT')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            statusFilter === 'SENT'
              ? 'bg-emerald-50/80 border-emerald-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-emerald-700 font-semibold mb-2">
            <span>GỬI THÀNH CÔNG (SENT)</span>
            <MailCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-800">{sentCount}</div>
          <p className="text-[11px] text-emerald-600/80 mt-1 mb-0">Đã chuyển tới hòm thư</p>
        </div>

        <div
          onClick={() => {
            setStatusFilter('FAILED')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            statusFilter === 'FAILED'
              ? 'bg-rose-50/80 border-rose-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-rose-700 font-semibold mb-2">
            <span>GỬI THẤT BẠI (FAILED)</span>
            <MailX className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-800">{failedCount}</div>
          <p className="text-[11px] text-rose-600/80 mt-1 mb-0">Cần xếp hàng thử lại</p>
        </div>

        <div
          onClick={() => {
            setStatusFilter('PENDING')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            statusFilter === 'PENDING'
              ? 'bg-amber-50/80 border-amber-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-amber-700 font-semibold mb-2">
            <span>ĐANG CHỜ GỬI (PENDING)</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-800">{pendingCount}</div>
          <p className="text-[11px] text-amber-600/80 mt-1 mb-0">Đang xếp hàng trong queue</p>
        </div>
      </div>

      {/* Main Table Card */}
      <Card className="table-card overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {/* Toolbar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-slate-50/40">
          {/* Tabs Filter */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl self-start text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setStatusFilter('ALL')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                statusFilter === 'ALL'
                  ? 'bg-white text-[#00288E] shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Tất cả ({totalCount})
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('SENT')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                statusFilter === 'SENT'
                  ? 'bg-white text-emerald-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Đã gửi ({sentCount})
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('FAILED')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer flex items-center gap-1.5 ${
                statusFilter === 'FAILED'
                  ? 'bg-white text-rose-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>Thất bại ({failedCount})</span>
              {failedCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" />
              )}
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('PENDING')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                statusFilter === 'PENDING'
                  ? 'bg-white text-amber-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Đang chờ ({pendingCount})
            </button>
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={typeFilter}
              onChange={e => {
                setTypeFilter(e.target.value)
                setPage(1)
              }}
              className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] cursor-pointer"
            >
              <option value="ALL">Tất cả loại email</option>
              <option value="ACCOUNT_ACTIVATION">Kích hoạt tài khoản</option>
              <option value="PASSWORD_RESET">Đặt lại mật khẩu</option>
              <option value="COMPANY_APPROVED">Phê duyệt doanh nghiệp</option>
              <option value="COMPANY_REJECTED">Từ chối doanh nghiệp</option>
              <option value="JOB_APPROVED">Phê duyệt tin tuyển dụng</option>
              <option value="JOB_REJECTED">Từ chối tin tuyển dụng</option>
              <option value="ACCOUNT_LOCKED">Khóa tài khoản</option>
              <option value="ACCOUNT_UNLOCKED">Mở khóa tài khoản</option>
              <option value="REPORT_HANDLED">Xử lý báo cáo vi phạm</option>
            </select>
          </div>
        </div>

        {/* Content list */}
        {isPending ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState message={error.message} onRetry={() => void refetch()} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="Không có nhật ký email nào"
            description="Chưa có bản ghi email nào khớp với bộ lọc đã chọn."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Email Người nhận</th>
                    <th className="py-3 px-4">Tiêu đề email</th>
                    <th className="py-3 px-4">Loại email</th>
                    <th className="py-3 px-4">Trạng thái</th>
                    <th className="py-3 px-4 text-center">Thử lại</th>
                    <th className="py-3 px-4">Thời gian</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {data.items.map(log => (
                    <tr key={log.id} className="hover:bg-blue-50/20 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-slate-800">
                        <div className="font-mono text-slate-800">{log.recipient_email}</div>
                        {log.user_id && (
                          <span className="text-[10px] text-slate-400 font-mono">
                            User ID: #{log.user_id}
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 max-w-sm">
                        <div className="font-semibold text-[#131B2E]">{log.subject}</div>
                        {log.status === 'FAILED' && log.error_message && (
                          <div className="text-[11px] font-mono text-rose-600 bg-rose-50 border border-rose-100 p-1.5 rounded mt-1 leading-tight">
                            Lỗi: {log.error_message}
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">
                          {TEMPLATE_TYPE_LABELS[log.type] || log.type}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {log.status === 'SENT' ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3" /> Đã gửi (SENT)
                          </span>
                        ) : log.status === 'PENDING' ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            <Clock className="w-3 h-3" /> Đang chờ gửi (PENDING)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            <XCircle className="w-3 h-3" /> Thất bại (FAILED)
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-center whitespace-nowrap">
                        <span
                          className={`font-mono text-xs font-semibold ${
                            log.retry_count > 0 ? 'text-amber-700' : 'text-slate-400'
                          }`}
                        >
                          {log.retry_count} lần
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px] whitespace-nowrap">
                        <div>Gửi: {formatDate(log.sent_at)}</div>
                        <div className="text-[10px] text-slate-400">Tạo: {formatDate(log.created_at)}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Pagination
              page={page}
              pages={data.pages}
              total={data.total}
              onChange={next => setPage(next)}
            />
          </>
        )}
      </Card>
    </div>
  )
}
