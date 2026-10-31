import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  GraduationCap,
  Lock,
  Plus,
  Search,
  Shield,
  ShieldAlert,
  Unlock,
  UserCheck,
  UserX,
  X,
} from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Card } from '@/components/ui/Card'
import { usersApi } from '../api/users.api'
import type {
  AdminCreate,
  UserRead,
  UserRole,
  UserStatus,
} from '../types/users.types'
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

export default function UserAdminPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [roleFilter, setRoleFilter] = useState<UserRole | 'ALL'>('ALL')
  const [statusFilter, setStatusFilter] = useState<UserStatus | 'ALL'>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Modal 1: Create Admin
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [adminForm, setAdminForm] = useState<AdminCreate>({
    email: '',
    password: '',
    full_name: '',
    faculty_id: undefined,
    position: '',
    phone: '',
  })
  const [createError, setCreateError] = useState('')

  // Modal 2: Lock User
  const [targetLockUser, setTargetLockUser] = useState<UserRead | null>(null)
  const [lockReason, setLockReason] = useState('')
  const [lockError, setLockError] = useState('')

  // Query list
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['admin-users', page, roleFilter, statusFilter, searchQuery],
    queryFn: () =>
      usersApi.list({
        page,
        size: 10,
        role: roleFilter === 'ALL' ? undefined : roleFilter,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        q: searchQuery,
      }),
  })

  // Create admin mutation
  const createAdminMutation = useMutation({
    mutationFn: (payload: AdminCreate) => usersApi.createAdmin(payload),
    onSuccess: () => {
      setShowCreateModal(false)
      setAdminForm({
        email: '',
        password: '',
        full_name: '',
        faculty_id: undefined,
        position: '',
        phone: '',
      })
      setCreateError('')
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (err: unknown) => {
      setCreateError(toApiError(err).message)
    },
  })

  // Lock user mutation
  const lockMutation = useMutation({
    mutationFn: (payload: { id: number; reason: string }) =>
      usersApi.lock(payload.id, { reason: payload.reason }),
    onSuccess: () => {
      setTargetLockUser(null)
      setLockReason('')
      setLockError('')
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (err: unknown) => {
      setLockError(toApiError(err).message)
    },
  })

  // Unlock user mutation
  const unlockMutation = useMutation({
    mutationFn: (id: number) => usersApi.unlock(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (err: unknown) => {
      alert(`Mở khóa thất bại: ${toApiError(err).message}`)
    },
  })

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError('')
    if (!adminForm.email.trim() || !adminForm.password.trim() || !adminForm.full_name.trim()) {
      setCreateError('Vui lòng điền đầy đủ Email, Mật khẩu và Họ tên.')
      return
    }
    if (adminForm.password.length < 8) {
      setCreateError('Mật khẩu quản trị viên phải từ 8 ký tự trở lên.')
      return
    }
    createAdminMutation.mutate({
      ...adminForm,
      faculty_id: adminForm.faculty_id ? Number(adminForm.faculty_id) : undefined,
      position: adminForm.position?.trim() || undefined,
      phone: adminForm.phone?.trim() || undefined,
    })
  }

  const handleLockSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLockError('')
    if (!targetLockUser) return
    if (!lockReason.trim()) {
      setLockError('Vui lòng nhập lý do khóa tài khoản.')
      return
    }
    lockMutation.mutate({ id: targetLockUser.id, reason: lockReason.trim() })
  }

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'STUDENT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-[#00288E] border border-blue-200">
            <GraduationCap className="w-3.5 h-3.5" /> Sinh viên
          </span>
        )
      case 'COMPANY':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-[#006A63] border border-teal-200">
            <Building2 className="w-3.5 h-3.5" /> Doanh nghiệp
          </span>
        )
      case 'ADMIN':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <Shield className="w-3.5 h-3.5" /> Quản trị viên
          </span>
        )
    }
  }

  const getStatusBadge = (user: UserRead) => {
    switch (user.status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <UserCheck className="w-3 h-3" /> Đang hoạt động
          </span>
        )
      case 'LOCKED':
        return (
          <span
            title={user.locked_reason ? `Lý do: ${user.locked_reason}` : 'Tài khoản bị khóa'}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 cursor-help"
          >
            <UserX className="w-3 h-3" /> Đã khóa
          </span>
        )
      case 'PENDING_ACTIVATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Chờ kích hoạt
          </span>
        )
      case 'PENDING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Chờ phê duyệt
          </span>
        )
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <PageHeader
          eyebrow="QUẢN TRỊ NHÀ TRƯỜNG"
          title="Quản lý Tài khoản Hệ thống"
          description="Quản lý quyền truy cập, kiểm soát an toàn danh tính và trạng thái tài khoản người dùng 3 bên."
        />
        <button
          type="button"
          onClick={() => {
            setShowCreateModal(true)
            setCreateError('')
          }}
          className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold text-xs flex items-center gap-2 shadow-xs transition-colors cursor-pointer border-0 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo tài khoản Admin mới</span>
        </button>
      </div>

      {/* Main Table Card */}
      <Card className="table-card overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {/* Toolbar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-slate-50/40">
          <div className="flex flex-wrap items-center gap-3">
            {/* Role Filter */}
            <select
              value={roleFilter}
              onChange={e => {
                setRoleFilter(e.target.value as UserRole | 'ALL')
                setPage(1)
              }}
              className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] cursor-pointer"
            >
              <option value="ALL">Mọi vai trò</option>
              <option value="STUDENT">Sinh viên (STUDENT)</option>
              <option value="COMPANY">Doanh nghiệp (COMPANY)</option>
              <option value="ADMIN">Quản trị viên (ADMIN)</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={e => {
                setStatusFilter(e.target.value as UserStatus | 'ALL')
                setPage(1)
              }}
              className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] cursor-pointer"
            >
              <option value="ALL">Mọi trạng thái</option>
              <option value="ACTIVE">Đang hoạt động (ACTIVE)</option>
              <option value="PENDING_ACTIVATION">Chờ kích hoạt (PENDING_ACTIVATION)</option>
              <option value="PENDING_APPROVAL">Chờ phê duyệt (PENDING_APPROVAL)</option>
              <option value="LOCKED">Đã khóa (LOCKED)</option>
            </select>
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
              placeholder="Tìm kiếm theo địa chỉ email..."
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
            />
          </div>
        </div>

        {/* Content list */}
        {isPending ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState message={error.message} onRetry={() => void refetch()} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="Không tìm thấy tài khoản nào"
            description="Không có tài khoản nào phù hợp với bộ lọc hoặc từ khóa tìm kiếm."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Tài khoản & Email</th>
                    <th className="py-3 px-4">Vai trò</th>
                    <th className="py-3 px-4">Trạng thái</th>
                    <th className="py-3 px-4">Đăng nhập cuối</th>
                    <th className="py-3 px-4">Ngày tạo</th>
                    <th className="py-3 px-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {data.items.map(user => (
                    <tr key={user.id} className="hover:bg-blue-50/20 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#131B2E] text-sm">
                          {user.admin?.full_name || user.email}
                        </div>
                        {user.admin?.full_name && (
                          <div className="text-slate-500 text-[11px] font-mono mt-0.5">
                            {user.email}
                          </div>
                        )}
                        {user.admin?.position && (
                          <span className="text-[10px] text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded mt-0.5 inline-block">
                            {user.admin.position}
                          </span>
                        )}
                        {user.status === 'LOCKED' && user.locked_reason && (
                          <div className="text-[11px] text-rose-600 mt-1 flex items-start gap-1">
                            <span className="font-bold">Lý do khóa:</span>
                            <span>{user.locked_reason}</span>
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getRoleBadge(user.role)}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getStatusBadge(user)}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px] whitespace-nowrap">
                        {formatDate(user.last_login_at)}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px] whitespace-nowrap">
                        {formatDate(user.created_at)}
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        {user.status === 'LOCKED' ? (
                          <button
                            type="button"
                            disabled={unlockMutation.isPending}
                            onClick={() => unlockMutation.mutate(user.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors border border-emerald-200 cursor-pointer disabled:opacity-50"
                          >
                            <Unlock className="w-3.5 h-3.5" />
                            <span>Mở khóa</span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
                              setTargetLockUser(user)
                              setLockReason('')
                              setLockError('')
                            }}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors border border-rose-200 cursor-pointer"
                          >
                            <Lock className="w-3.5 h-3.5" />
                            <span>Khóa tài khoản</span>
                          </button>
                        )}
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

      {/* Modal 1: Tạo Admin mới (D08) */}
      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 text-left">
            <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/70">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-[#131B2E] m-0">
                    Tạo tài khoản Quản trị viên mới
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 mb-0">
                    Cấp quyền quản trị Nhà trường cho cán bộ hoặc giảng viên phụ trách.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="w-8 h-8 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors border-0 bg-transparent cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
              {createError && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                  <span>{createError}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="block font-semibold text-slate-800">
                  Email nhà trường <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={adminForm.email}
                  onChange={e => setAdminForm({ ...adminForm, email: e.target.value })}
                  placeholder="admin.cntt@university.edu.vn"
                  className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
                />
              </div>

              <div className="space-y-1">
                <label className="block font-semibold text-slate-800">
                  Mật khẩu khởi tạo <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={adminForm.password}
                  onChange={e => setAdminForm({ ...adminForm, password: e.target.value })}
                  placeholder="Tối thiểu 8 ký tự an toàn"
                  className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
                />
              </div>

              <div className="space-y-1">
                <label className="block font-semibold text-slate-800">
                  Họ và tên cán bộ <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={adminForm.full_name}
                  onChange={e => setAdminForm({ ...adminForm, full_name: e.target.value })}
                  placeholder="Nguyễn Văn A"
                  className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block font-semibold text-slate-800">Chức vụ / Vị trí</label>
                  <input
                    type="text"
                    value={adminForm.position || ''}
                    onChange={e => setAdminForm({ ...adminForm, position: e.target.value })}
                    placeholder="Chuyên viên phòng CTSV"
                    className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="block font-semibold text-slate-800">Số điện thoại</label>
                  <input
                    type="tel"
                    value={adminForm.phone || ''}
                    onChange={e => setAdminForm({ ...adminForm, phone: e.target.value })}
                    placeholder="0912345678"
                    className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold transition-colors border-0 bg-transparent cursor-pointer"
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  disabled={createAdminMutation.isPending}
                  className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{createAdminMutation.isPending ? 'Đang tạo…' : 'Tạo tài khoản'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Khóa tài khoản (D08) */}
      {targetLockUser && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 text-left">
            <div className="p-6 border-b border-rose-100 bg-rose-50/50 flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-base text-rose-900 m-0">
                  Xác nhận Khóa tài khoản
                </h3>
                <p className="text-xs text-rose-700 mt-1 mb-0 leading-relaxed">
                  Tài khoản bị khóa sẽ ngay lập tức bị thu hồi quyền truy cập và bị từ chối ở mọi lượt đăng nhập tiếp theo.
                </p>
              </div>
            </div>

            <form onSubmit={handleLockSubmit} className="p-6 space-y-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="block text-slate-400 text-[10px] uppercase font-bold">
                    Tài khoản đối tượng
                  </span>
                  <strong className="text-slate-800">{targetLockUser.email}</strong>
                </div>
                {getRoleBadge(targetLockUser.role)}
              </div>

              {lockError && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                  <span>{lockError}</span>
                </div>
              )}

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Lý do khóa tài khoản <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  maxLength={500}
                  required
                  value={lockReason}
                  onChange={e => setLockReason(e.target.value)}
                  placeholder="Ghi rõ hành vi vi phạm (ví dụ: cung cấp hồ sơ giả mạo, spam tuyển dụng, thu tiền trái phép...)"
                  className="w-full p-2.5 bg-white border border-rose-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setTargetLockUser(null)}
                  className="px-4 py-2 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold transition-colors border-0 bg-transparent cursor-pointer"
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  disabled={lockMutation.isPending}
                  className="px-5 py-2.5 rounded-full bg-rose-600 hover:bg-rose-700 text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                >
                  <Lock className="w-4 h-4" />
                  <span>{lockMutation.isPending ? 'Đang khóa…' : 'Xác nhận Khóa tài khoản'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
