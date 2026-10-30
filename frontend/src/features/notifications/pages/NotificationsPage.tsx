import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Bell,
  Building,
  Calendar,
  CheckCheck,
  CheckCircle2,
  FileText,
} from 'lucide-react'
import { useAuth } from '@/features/auth'
import { notificationsApi } from '../api/notifications.api'
import type { Notification } from '../api/notifications.api'
import { getNotificationTargetUrl } from '../lib/notification-navigation'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'

export default function NotificationsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const client = useQueryClient()

  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  // Query danh sách thông báo theo filter
  const query = useQuery({
    queryKey: ['notifications', 'list', page, filter],
    queryFn: ({ signal }) =>
      notificationsApi.list(page, filter === 'unread' ? false : null, signal),
  })

  // Query tổng số chưa đọc
  const countQuery = useQuery({
    queryKey: ['notifications', 'count'],
    queryFn: notificationsApi.count,
    enabled: !!user,
  })

  // Đánh dấu 1 hoặc tất cả đã đọc
  const readMutation = useMutation({
    mutationFn: (id: number | 'all') =>
      id === 'all' ? notificationsApi.readAll() : notificationsApi.read(id),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const unreadCount = countQuery.data?.unread_count ?? 0

  const handleAction = async (item: Notification) => {
    if (!item.is_read) {
      await readMutation.mutateAsync(item.id)
    }
    const targetUrl = getNotificationTargetUrl(item, user?.role)
    navigate(targetUrl)
  }

  const getBorderColor = (item: Notification) => {
    if (item.is_read) return 'border-l-slate-200'
    const ref = (item.ref_type || item.type || '').toUpperCase()
    if (ref.includes('APP')) return 'border-l-[#00288E]'
    if (ref.includes('COMPANY') || ref.includes('ENT')) return 'border-l-[#006A63]'
    if (ref.includes('INVIT') || ref.includes('INTERVIEW')) return 'border-l-[#D97706]'
    return 'border-l-[#6B21A8]'
  }

  const getCategoryLabel = (item: Notification) => {
    const ref = (item.ref_type || item.type || '').toUpperCase()
    if (ref.includes('APP')) return 'Ứng tuyển & Hồ sơ'
    if (ref.includes('COMPANY') || ref.includes('ENT')) return 'Hợp tác Doanh nghiệp'
    if (ref.includes('INVIT') || ref.includes('INTERVIEW')) return 'Lịch phỏng vấn & Lời mời'
    if (ref.includes('JOB')) return 'Tin tuyển dụng'
    if (ref.includes('TERM')) return 'Đợt thực tập'
    return 'Hệ thống'
  }

  const getIcon = (item: Notification) => {
    const ref = (item.ref_type || item.type || '').toUpperCase()
    if (ref.includes('APP')) {
      return (
        <div className="w-11 h-11 rounded-2xl bg-blue-100 text-[#00288E] flex items-center justify-center shrink-0">
          <FileText className="w-5 h-5" />
        </div>
      )
    }
    if (ref.includes('COMPANY') || ref.includes('ENT')) {
      return (
        <div className="w-11 h-11 rounded-2xl bg-teal-100 text-[#006A63] flex items-center justify-center shrink-0">
          <Building className="w-5 h-5" />
        </div>
      )
    }
    if (ref.includes('INVIT') || ref.includes('INTERVIEW')) {
      return (
        <div className="w-11 h-11 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
          <Calendar className="w-5 h-5" />
        </div>
      )
    }
    return (
      <div className="w-11 h-11 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
        <Bell className="w-5 h-5" />
      </div>
    )
  }

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 py-6 px-4 sm:px-6">
      {/* Hero Title & Operations Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#131B2E] tracking-tight m-0">
              Trung tâm Thông báo
            </h1>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-[#00288E]">
              <span className="w-2 h-2 rounded-full bg-[#00288E] animate-pulse" />
              {unreadCount} thông báo chưa đọc
            </span>
          </div>
          <p className="text-xs sm:text-sm text-[#444653] mt-1.5 mb-0 leading-relaxed">
            Quản lý và theo dõi các biến động xét duyệt, lời mời phỏng vấn, hồ sơ ứng tuyển và cảnh báo hệ thống theo thời gian thực.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={() => readMutation.mutate('all')}
            disabled={readMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-[#E2E8F0] rounded-xl shadow-xs hover:bg-slate-50 hover:text-[#00288E] transition-colors cursor-pointer shrink-0 disabled:opacity-50"
          >
            <CheckCheck className="w-4 h-4 text-[#00288E]" />
            <span>{readMutation.isPending ? 'Đang cập nhật…' : 'Đánh dấu tất cả đã đọc'}</span>
          </button>
        )}
      </div>

      {/* Filter Tabs Bar */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            setFilter('all')
            setPage(1)
          }}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer border-0 ${
            filter === 'all'
              ? 'bg-[#00288E] text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-[#E2E8F0]'
          }`}
        >
          Tất cả thông báo
        </button>

        <button
          type="button"
          onClick={() => {
            setFilter('unread')
            setPage(1)
          }}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors cursor-pointer flex items-center gap-1.5 border-0 ${
            filter === 'unread'
              ? 'bg-[#00288E] text-white shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-[#E2E8F0]'
          }`}
        >
          <span>Chưa đọc</span>
          {unreadCount > 0 && (
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                filter === 'unread' ? 'bg-white/20 text-white' : 'bg-blue-100 text-[#00288E]'
              }`}
            >
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Main List Container */}
      <div className="bg-white rounded-2xl border border-[#E2E8F0] shadow-xs overflow-hidden">
        {readMutation.isError && (
          <div className="p-3 bg-red-50 text-red-700 text-xs border-b border-red-100">
            {readMutation.error.message}
          </div>
        )}

        {query.isPending ? (
          <div className="py-16">
            <LoadingState label="Đang tải danh sách thông báo…" />
          </div>
        ) : query.isError ? (
          <div className="py-12">
            <ErrorState
              message={query.error.message}
              onRetry={() => void query.refetch()}
            />
          </div>
        ) : query.data.items.length === 0 ? (
          <div className="py-16 text-center">
            <EmptyState
              title={filter === 'unread' ? 'Không có thông báo chưa đọc nào' : 'Bạn đã cập nhật mọi thông tin'}
              description={
                filter === 'unread'
                  ? 'Tất cả thông báo của bạn đã được đọc.'
                  : 'Các thông báo mới về ứng tuyển, phỏng vấn và xét duyệt sẽ xuất hiện tại đây.'
              }
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {query.data.items.map(item => (
              <article
                key={item.id}
                className={`p-5 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 ${getBorderColor(
                  item
                )} ${item.is_read ? 'bg-white hover:bg-slate-50/50' : 'bg-[#F2F3FF]/70 hover:bg-[#E9ECFF]/80'}`}
              >
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  {getIcon(item)}
                  <div className="space-y-1 flex-1 min-w-0 text-left">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                        {getCategoryLabel(item)}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(item.created_at).toLocaleDateString('vi-VN', {
                          hour: '2-digit',
                          minute: '2-digit',
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                        })}
                      </span>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-[#00288E]" title="Chưa đọc" />
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-[#131B2E] leading-snug m-0">
                      {item.title}
                    </h3>
                    {item.content && (
                      <p className="text-xs text-[#444653] leading-relaxed m-0 line-clamp-2">
                        {item.content}
                      </p>
                    )}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex items-center gap-2 self-start md:self-center shrink-0 pt-2 md:pt-0">
                  <button
                    type="button"
                    onClick={() => void handleAction(item)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#00288E] text-white hover:bg-[#001E6C] transition-colors shadow-xs cursor-pointer border-0"
                  >
                    <span>Xem chi tiết</span>
                  </button>

                  {!item.is_read && (
                    <button
                      type="button"
                      title="Đánh dấu đã đọc"
                      onClick={() => readMutation.mutate(item.id)}
                      disabled={readMutation.isPending}
                      className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-full transition-colors cursor-pointer border-0 bg-transparent"
                    >
                      <CheckCircle2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}

        {/* Phân trang */}
        {query.data && query.data.pages > 1 && (
          <div className="p-4 border-t border-[#E2E8F0] flex justify-center">
            <Pagination
              page={page}
              pages={query.data.pages}
              total={query.data.total}
              onChange={setPage}
            />
          </div>
        )}
      </div>
    </div>
  )
}
