import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  Bell,
  Briefcase,
  Building,
  Calendar,
  FileText,
  GraduationCap,
  Sparkles,
} from 'lucide-react'
import { useAuth, roleHome } from '@/features/auth'
import { toApiError } from '@/lib/api-error'
import { notificationsApi } from '../api/notifications.api'
import type { Notification } from '../api/notifications.api'
import { getNotificationTargetUrl } from '../lib/notification-navigation'

export function NotificationBell() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const client = useQueryClient()
  const [open, setOpen] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Query đếm số lượng chưa đọc
  const countQuery = useQuery({
    queryKey: ['notifications', 'count'],
    queryFn: notificationsApi.count,
    enabled: !!user,
    refetchInterval: 30_000,
  })

  // Query 5 thông báo gần nhất cho Flyout Drawer
  const listQuery = useQuery({
    queryKey: ['notifications', 'quick-list'],
    queryFn: () => notificationsApi.list(1, null),
    enabled: !!user && open,
  })

  // Mutation đánh dấu 1 thông báo đã đọc
  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationsApi.read(id),
    onSuccess: () => {
      setActionError(null)
      void client.invalidateQueries({ queryKey: ['notifications'] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message || 'Không thể đánh dấu thông báo đã đọc.')
    },
  })

  // Mutation đánh dấu tất cả đã đọc
  const markAllMutation = useMutation({
    mutationFn: () => notificationsApi.readAll(),
    onSuccess: () => {
      setActionError(null)
      void client.invalidateQueries({ queryKey: ['notifications'] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message || 'Không thể đánh dấu tất cả đã đọc.')
    },
  })

  // Đóng Drawer khi click ra ngoài
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  // Đóng Drawer khi bấm Escape
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    if (open) {
      document.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  if (!user) return null

  const unreadCount = countQuery.data?.unread_count ?? 0
  const notifications = listQuery.data?.items?.slice(0, 5) ?? []

  const handleNotificationClick = async (item: Notification) => {
    setActionError(null)
    if (!item.is_read) {
      try {
        await markReadMutation.mutateAsync(item.id)
      } catch (err: unknown) {
        setActionError(toApiError(err).message || 'Không thể đánh dấu thông báo đã đọc.')
      }
    }
    setOpen(false)
    const targetUrl = getNotificationTargetUrl(item, user.role)
    navigate(targetUrl)
  }

  const getIcon = (item: Notification) => {
    const ref = (item.ref_type || item.type || '').toUpperCase()
    if (ref.includes('APP')) return <FileText className="w-4 h-4 text-[#00288E]" />
    if (ref.includes('COMPANY') || ref.includes('ENT')) return <Building className="w-4 h-4 text-[#006A63]" />
    if (ref.includes('JOB')) return <Briefcase className="w-4 h-4 text-indigo-700" />
    if (ref.includes('INVIT') || ref.includes('INTERVIEW')) return <Calendar className="w-4 h-4 text-amber-700" />
    if (ref.includes('TERM')) return <GraduationCap className="w-4 h-4 text-teal-700" />
    return <Bell className="w-4 h-4 text-slate-600" />
  }

  return (
    <div className="relative inline-block" ref={containerRef}>
      {/* Nút Chuông thông báo */}
      <button
        type="button"
        onClick={() => {
          setOpen(!open)
          setActionError(null)
        }}
        aria-expanded={open}
        aria-haspopup="true"
        aria-label={unreadCount > 0 ? `Thông báo, ${unreadCount} chưa đọc` : 'Thông báo'}
        className={`relative p-2 rounded-xl transition-colors cursor-pointer border-0 ${
          open
            ? 'bg-blue-100 text-[#00288E]'
            : 'bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900'
        }`}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 px-1.5 min-w-[18px] h-[18px] bg-rose-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* FLYOUT NOTIFICATION DRAWER / POPOVER */}
      {open && (
        <div
          className="absolute right-0 top-12 w-[380px] max-w-[92vw] bg-white rounded-2xl shadow-xl z-50 border border-[#E2E8F0] overflow-hidden text-left animate-in fade-in zoom-in-95 duration-150"
          role="dialog"
          aria-label="Danh sách thông báo"
        >
          {/* Header Drawer */}
          <div className="px-4 py-3.5 bg-slate-50 border-b border-[#E2E8F0] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-[#131B2E] text-xs m-0">Thông báo mới nhận</h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-[#00288E]">
                {unreadCount} chưa đọc
              </span>
            </div>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
                className="text-[11px] font-semibold text-[#00288E] hover:underline bg-transparent border-0 cursor-pointer disabled:opacity-50"
              >
                {markAllMutation.isPending ? 'Đang cập nhật…' : 'Đánh dấu tất cả đã đọc'}
              </button>
            )}
          </div>

          {/* Action Error Banner nếu có lỗi thao tác */}
          {actionError && (
            <div className="px-3.5 py-2 bg-rose-50 text-rose-700 text-xs border-b border-rose-100 flex items-center justify-between">
              <span className="truncate">{actionError}</span>
              <button
                type="button"
                onClick={() => setActionError(null)}
                className="text-rose-500 hover:text-rose-700 font-bold ml-2 bg-transparent border-0 cursor-pointer"
              >
                ×
              </button>
            </div>
          )}

          {/* Quick List Body - Phân biệt rõ: Loading -> Error -> Empty -> Success */}
          <div className="divide-y divide-slate-100 max-h-[360px] overflow-y-auto">
            {listQuery.isPending ? (
              <div className="p-6 text-center text-xs text-slate-500">Đang tải thông báo…</div>
            ) : listQuery.isError ? (
              <div className="p-6 text-center text-xs text-rose-600 bg-rose-50/40">
                <AlertCircle className="w-6 h-6 text-rose-500 mx-auto mb-2" />
                <p className="font-semibold m-0">{toApiError(listQuery.error).message || 'Không thể tải thông báo'}</p>
                <button
                  type="button"
                  onClick={() => void listQuery.refetch()}
                  className="mt-2.5 px-3 py-1 bg-white border border-rose-200 text-rose-700 rounded-lg text-xs font-semibold hover:bg-rose-50 cursor-pointer shadow-2xs"
                >
                  Thử lại
                </button>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                <Sparkles className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="m-0 font-medium">Bạn đã cập nhật mọi thông tin!</p>
                <p className="text-[11px] text-slate-400 mt-1 mb-0">Không có thông báo mới nào cần xử lý.</p>
              </div>
            ) : (
              notifications.map(item => (
                <div
                  key={item.id}
                  onClick={() => void handleNotificationClick(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => {
                    if (e.key === 'Enter') void handleNotificationClick(item)
                  }}
                  className={`p-3.5 transition-colors flex items-start gap-3 cursor-pointer ${
                    item.is_read ? 'hover:bg-slate-50 bg-white' : 'bg-[#F2F3FF]/80 hover:bg-[#E9ECFF]'
                  }`}
                >
                  <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center shrink-0 mt-0.5">
                    {getIcon(item)}
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between gap-1 mb-0.5">
                      <span className="text-[11px] font-bold text-[#131B2E] truncate">
                        {item.title}
                      </span>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-[#00288E] shrink-0" title="Chưa đọc" />
                      )}
                    </div>
                    {item.content && (
                      <p className="text-xs text-[#444653] line-clamp-2 leading-snug m-0">
                        {item.content}
                      </p>
                    )}
                    <span className="text-[10px] text-slate-400 block mt-1">
                      {new Date(item.created_at).toLocaleDateString('vi-VN', {
                        hour: '2-digit',
                        minute: '2-digit',
                        day: '2-digit',
                        month: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer Drawer Link */}
          <Link
            to={`${roleHome[user.role]}/notifications`}
            onClick={() => setOpen(false)}
            className="block w-full py-2.5 px-4 text-center text-xs font-bold text-[#00288E] bg-slate-50 hover:bg-slate-100 border-t border-[#E2E8F0] transition-colors"
          >
            Xem tất cả trong Trung tâm Thông báo →
          </Link>
        </div>
      )}
    </div>
  )
}
