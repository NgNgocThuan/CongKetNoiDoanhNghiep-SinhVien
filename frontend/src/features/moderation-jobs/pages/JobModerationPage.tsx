import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  Archive,
  Ban,
  Briefcase,
  Building,
  Calendar,
  CheckCircle2,
  Clock,
  Coins,
  Eye,
  FileCheck2,
  GraduationCap,
  MapPin,
  Search,
  Sparkles,
  Users,
  X,
  XCircle,
} from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Card } from '@/components/ui/Card'
import { jobsApi } from '../api/jobs.api'
import type {
  AdminJobDetailRead,
  AdminJobRead,
  JobStatus,
  WorkMode,
} from '../types/jobs.types'
import { toApiError } from '@/lib/api-error'

function formatDate(isoString?: string | null) {
  if (!isoString) return '—'
  const date = new Date(isoString)
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

function formatSalary(
  isNegotiable: boolean,
  min?: number | null,
  max?: number | null
) {
  if (isNegotiable) return 'Thỏa thuận'
  if (min && max) return `${(min / 1_000_000).toFixed(0)} - ${(max / 1_000_000).toFixed(0)} tr VNĐ`
  if (min) return `Từ ${(min / 1_000_000).toFixed(0)} tr VNĐ`
  if (max) return `Tối đa ${(max / 1_000_000).toFixed(0)} tr VNĐ`
  return 'Thỏa thuận'
}

const WORK_MODE_LABELS: Record<WorkMode, string> = {
  ONSITE: 'Tại văn phòng (Onsite)',
  HYBRID: 'Linh hoạt (Hybrid)',
  REMOTE: 'Từ xa (Remote)',
}

export default function JobModerationPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<JobStatus>('PENDING_APPROVAL')
  const [searchQuery, setSearchQuery] = useState('')

  // Drawer detail state
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [showCloseForm, setShowCloseForm] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [closeReason, setCloseReason] = useState('')
  const [actionError, setActionError] = useState('')

  // Query jobs
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['admin-jobs', page, statusFilter, searchQuery],
    queryFn: () =>
      jobsApi.list({
        page,
        size: 10,
        status: statusFilter,
        q: searchQuery,
      }),
  })

  // Summary counts
  const pendingCountQuery = useQuery({
    queryKey: ['admin-jobs', 'count', 'PENDING_APPROVAL'],
    queryFn: () => jobsApi.list({ status: 'PENDING_APPROVAL', size: 1 }),
  })
  const approvedCountQuery = useQuery({
    queryKey: ['admin-jobs', 'count', 'APPROVED'],
    queryFn: () => jobsApi.list({ status: 'APPROVED', size: 1 }),
  })
  const rejectedCountQuery = useQuery({
    queryKey: ['admin-jobs', 'count', 'REJECTED'],
    queryFn: () => jobsApi.list({ status: 'REJECTED', size: 1 }),
  })
  const closedCountQuery = useQuery({
    queryKey: ['admin-jobs', 'count', 'CLOSED'],
    queryFn: () => jobsApi.list({ status: 'CLOSED', size: 1 }),
  })

  // Detail query
  const detailQuery = useQuery({
    queryKey: ['admin-job-detail', selectedJobId],
    queryFn: () => (selectedJobId ? jobsApi.get(selectedJobId) : null),
    enabled: !!selectedJobId,
  })

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id: number) => jobsApi.approve(id),
    onSuccess: (updated: AdminJobDetailRead) => {
      setActionError('')
      setShowRejectForm(false)
      setShowCloseForm(false)
      void queryClient.invalidateQueries({ queryKey: ['admin-jobs'] })
      void queryClient.invalidateQueries({ queryKey: ['admin-job-detail', updated.id] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (payload: { id: number; reason: string }) =>
      jobsApi.reject(payload.id, { reject_reason: payload.reason }),
    onSuccess: (updated: AdminJobDetailRead) => {
      setActionError('')
      setShowRejectForm(false)
      setRejectReason('')
      void queryClient.invalidateQueries({ queryKey: ['admin-jobs'] })
      void queryClient.invalidateQueries({ queryKey: ['admin-job-detail', updated.id] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message)
    },
  })

  const closeMutation = useMutation({
    mutationFn: (payload: { id: number; reason: string }) =>
      jobsApi.close(payload.id, { reason: payload.reason }),
    onSuccess: (updated: AdminJobDetailRead) => {
      setActionError('')
      setShowCloseForm(false)
      setCloseReason('')
      void queryClient.invalidateQueries({ queryKey: ['admin-jobs'] })
      void queryClient.invalidateQueries({ queryKey: ['admin-job-detail', updated.id] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message)
    },
  })

  const handleOpenDrawer = (job: AdminJobRead) => {
    setSelectedJobId(job.id)
    setShowRejectForm(false)
    setShowCloseForm(false)
    setRejectReason('')
    setCloseReason('')
    setActionError('')
  }

  const handleCloseDrawer = () => {
    setSelectedJobId(null)
    setShowRejectForm(false)
    setShowCloseForm(false)
    setRejectReason('')
    setCloseReason('')
    setActionError('')
  }

  const handleApprove = () => {
    if (!selectedJobId) return
    approveMutation.mutate(selectedJobId)
  }

  const handleRejectSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedJobId) return
    if (!rejectReason.trim()) {
      setActionError('Vui lòng nhập lý do từ chối tin tuyển dụng.')
      return
    }
    rejectMutation.mutate({ id: selectedJobId, reason: rejectReason.trim() })
  }

  const handleCloseSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedJobId) return
    closeMutation.mutate({ id: selectedJobId, reason: closeReason.trim() || '' })
  }

  const pendingCount = pendingCountQuery.data?.total ?? 0
  const approvedCount = approvedCountQuery.data?.total ?? 0
  const rejectedCount = rejectedCountQuery.data?.total ?? 0
  const closedCount = closedCountQuery.data?.total ?? 0

  const getStatusBadge = (status: JobStatus) => {
    switch (status) {
      case 'PENDING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3" /> Chờ duyệt
          </span>
        )
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" /> Đã duyệt
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3 h-3" /> Bị từ chối
          </span>
        )
      case 'CLOSED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
            <Archive className="w-3 h-3" /> Đã đóng
          </span>
        )
      case 'DRAFT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-50 text-slate-500 border border-slate-200">
            Bản nháp
          </span>
        )
      case 'EXPIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200">
            Hết hạn
          </span>
        )
    }
  }

  const activeJob = detailQuery.data

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="QUẢN TRỊ NHÀ TRƯỜNG"
        title="Kiểm duyệt Tin tuyển dụng Thực tập"
        description="Tin sau khi được duyệt sẽ hiển thị công khai cho sinh viên và xếp hàng phân tích độ phù hợp AI chạy nền."
      />

      {/* Main Table Card */}
      <Card className="table-card overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {/* Toolbar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-slate-50/40">
          {/* Tabs Filter */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl self-start text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setStatusFilter('PENDING_APPROVAL')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer flex items-center gap-1.5 ${
                statusFilter === 'PENDING_APPROVAL'
                  ? 'bg-white text-amber-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>Chờ duyệt</span>
              {pendingCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
              )}
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('APPROVED')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                statusFilter === 'APPROVED'
                  ? 'bg-white text-emerald-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>Đã duyệt ({approvedCount})</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('REJECTED')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                statusFilter === 'REJECTED'
                  ? 'bg-white text-rose-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>Từ chối ({rejectedCount})</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setStatusFilter('CLOSED')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                statusFilter === 'CLOSED'
                  ? 'bg-white text-slate-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>Đã đóng ({closedCount})</span>
            </button>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => {
                setSearchQuery(e.target.value)
                setPage(1)
              }}
              placeholder="Tìm theo tiêu đề hoặc vị trí…"
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
            title="Không có tin tuyển dụng nào"
            description="Không tìm thấy cơ hội thực tập nào khớp với trạng thái hoặc từ khóa tìm kiếm."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Tiêu đề & Vị trí</th>
                    <th className="py-3 px-4">Doanh nghiệp</th>
                    <th className="py-3 px-4">Số lượng / Hình thức</th>
                    <th className="py-3 px-4">Phụ cấp / Lương</th>
                    <th className="py-3 px-4">Hạn nộp</th>
                    <th className="py-3 px-4">Trạng thái</th>
                    <th className="py-3 px-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {data.items.map(job => (
                    <tr
                      key={job.id}
                      className="hover:bg-blue-50/30 transition-colors cursor-pointer"
                      onClick={() => handleOpenDrawer(job)}
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#131B2E] text-sm">{job.title}</div>
                        <div className="text-slate-500 text-[11px] mt-0.5 flex items-center gap-1.5">
                          <Briefcase className="w-3 h-3 text-slate-400" />
                          <span>{job.position}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-slate-700 flex items-center gap-1">
                          <Building className="w-3.5 h-3.5 text-slate-400" />
                          Doanh nghiệp #{job.company_id}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        <div className="font-medium text-slate-800">{job.quantity} chỉ tiêu</div>
                        <div className="text-[11px] text-slate-500">{WORK_MODE_LABELS[job.work_mode]}</div>
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className="font-semibold text-[#006A63]">
                          {formatSalary(job.is_salary_negotiable, job.salary_min, job.salary_max)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px] whitespace-nowrap">
                        {formatDate(job.deadline)}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={e => {
                            e.stopPropagation()
                            handleOpenDrawer(job)
                          }}
                          className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border-0 cursor-pointer ${
                            job.status === 'PENDING_APPROVAL'
                              ? 'bg-[#00288E] hover:bg-[#001E6C] text-white shadow-xs'
                              : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                          }`}
                        >
                          {job.status === 'PENDING_APPROVAL' ? (
                            <>
                              <FileCheck2 className="w-3.5 h-3.5" /> Kiểm duyệt
                            </>
                          ) : (
                            <>
                              <Eye className="w-3.5 h-3.5" /> Chi tiết
                            </>
                          )}
                        </button>
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

      {/* Slide-over Drawer Xem tin & Phê duyệt (D05) */}
      {selectedJobId && (
        <div
          className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
            {/* Header Drawer */}
            <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/70">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-slate-400">
                    TIN TUYỂN DỤNG #{selectedJobId}
                  </span>
                  {activeJob && getStatusBadge(activeJob.status)}
                </div>
                <h3 className="font-bold text-lg text-[#131B2E] m-0">
                  {activeJob ? activeJob.title : 'Đang tải tin tuyển dụng…'}
                </h3>
              </div>
              <button
                type="button"
                onClick={handleCloseDrawer}
                className="w-8 h-8 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors border-0 bg-transparent cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body Drawer */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
              {detailQuery.isPending ? (
                <LoadingState />
              ) : detailQuery.isError ? (
                <ErrorState
                  message={detailQuery.error.message}
                  onRetry={() => void detailQuery.refetch()}
                />
              ) : activeJob ? (
                <>
                  {/* Alert Error */}
                  {actionError && (
                    <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                      <span>{actionError}</span>
                    </div>
                  )}

                  {/* Thông số cốt lõi */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="block text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1">
                        <Users className="w-3 h-3" /> Số lượng tuyển
                      </span>
                      <strong className="text-slate-800 text-sm mt-0.5 block">
                        {activeJob.quantity} sinh viên
                      </strong>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="block text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1">
                        <Coins className="w-3 h-3" /> Phụ cấp / Lương
                      </span>
                      <strong className="text-[#006A63] text-sm mt-0.5 block truncate">
                        {formatSalary(
                          activeJob.is_salary_negotiable,
                          activeJob.salary_min,
                          activeJob.salary_max
                        )}
                      </strong>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="block text-slate-400 text-[10px] uppercase font-bold flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Hạn ứng tuyển
                      </span>
                      <strong className="text-slate-800 text-sm mt-0.5 block">
                        {formatDate(activeJob.deadline)}
                      </strong>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Hình thức làm việc:</span>
                      <strong className="text-slate-800">{WORK_MODE_LABELS[activeJob.work_mode]}</strong>
                    </div>
                    {activeJob.location && (
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-slate-500 font-medium flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" /> Địa điểm:
                        </span>
                        <span className="text-slate-800 text-right">{activeJob.location}</span>
                      </div>
                    )}
                    {activeJob.min_gpa && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500 font-medium flex items-center gap-1">
                          <GraduationCap className="w-3.5 h-3.5 text-slate-400" /> Điểm GPA yêu cầu:
                        </span>
                        <strong className="text-[#00288E]">Từ {activeJob.min_gpa} / 4.0</strong>
                      </div>
                    )}
                  </div>

                  {/* Nội dung tin tuyển dụng */}
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider m-0">
                        Mô tả công việc & Nhiệm vụ
                      </h4>
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-slate-700 leading-relaxed whitespace-pre-wrap">
                        {activeJob.description}
                      </div>
                    </div>

                    {activeJob.requirements && (
                      <div className="space-y-1.5">
                        <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider m-0">
                          Yêu cầu ứng viên
                        </h4>
                        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {activeJob.requirements}
                        </div>
                      </div>
                    )}

                    {activeJob.benefits && (
                      <div className="space-y-1.5">
                        <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider m-0">
                          Quyền lợi & Đãi ngộ
                        </h4>
                        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {activeJob.benefits}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* AI Parser Chips nếu có */}
                  {activeJob.parsed_json && (
                    <div className="p-4 rounded-xl bg-teal-50/70 border border-teal-200 space-y-2">
                      <div className="flex items-center gap-1.5 font-bold text-xs text-[#006A63]">
                        <Sparkles className="w-4 h-4 text-[#006A63]" />
                        <span>Kỹ năng & Từ khóa bóc tách bởi AI</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {Object.entries(activeJob.parsed_json).map(([k, v]) => (
                          <span
                            key={k}
                            className="px-2.5 py-1 rounded-full bg-white border border-teal-200 text-[#006A63] font-semibold text-[11px]"
                          >
                            {k}: {String(v)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Thông tin lịch sử kiểm duyệt */}
                  {activeJob.status === 'APPROVED' && (
                    <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 space-y-2">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Tin tuyển dụng đang mở công khai</span>
                      </div>
                      <span className="text-[11px] text-emerald-700 block">
                        Đã được phê duyệt lúc {formatDate(activeJob.approved_at)} bởi Quản trị viên #{activeJob.approved_by || 'Admin'}.
                      </span>
                    </div>
                  )}

                  {activeJob.status === 'REJECTED' && (
                    <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 space-y-2">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <XCircle className="w-4 h-4 text-rose-600" />
                        <span>Tin tuyển dụng đã bị từ chối</span>
                      </div>
                      {activeJob.reject_reason && (
                        <p className="text-xs text-rose-700 m-0 font-medium">
                          Lý do: &ldquo;{activeJob.reject_reason}&rdquo;
                        </p>
                      )}
                    </div>
                  )}

                  {activeJob.status === 'CLOSED' && (
                    <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-700 space-y-1">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <Archive className="w-4 h-4 text-slate-500" />
                        <span>Tin tuyển dụng đã đóng</span>
                      </div>
                      <span className="text-[11px] text-slate-500 block">
                        Tin không còn nhận đơn ứng tuyển và đã được lưu trữ.
                      </span>
                    </div>
                  )}

                  {/* Thao tác kiểm duyệt */}
                  {activeJob.status === 'PENDING_APPROVAL' && (
                    <div className="p-5 rounded-2xl border-2 border-slate-200 bg-slate-50/60 space-y-4">
                      <div className="flex items-center gap-2 font-bold text-sm text-[#131B2E]">
                        <FileCheck2 className="w-4 h-4 text-[#00288E]" />
                        <span>Quyết định Kiểm duyệt Tin</span>
                      </div>

                      {showRejectForm ? (
                        <form onSubmit={handleRejectSubmit} className="space-y-3">
                          <div>
                            <label className="block font-bold text-slate-700 mb-1">
                              Lý do từ chối tin tuyển dụng <span className="text-red-500">*</span>
                            </label>
                            <textarea
                              rows={3}
                              maxLength={500}
                              value={rejectReason}
                              onChange={e => setRejectReason(e.target.value)}
                              placeholder="Nêu rõ lý do (Mô tả công việc không phù hợp với chuẩn ngành, yêu cầu thu phí, thiếu thông tin đãi ngộ...)"
                              className="w-full p-3 bg-white border border-rose-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                            />
                            <span className="text-[10px] text-slate-400 block text-right mt-1">
                              {rejectReason.length}/500 ký tự
                            </span>
                          </div>

                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setShowRejectForm(false)
                                setRejectReason('')
                                setActionError('')
                              }}
                              className="px-4 py-2 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold transition-colors border-0 bg-transparent cursor-pointer"
                            >
                              Hủy bỏ
                            </button>
                            <button
                              type="submit"
                              disabled={rejectMutation.isPending}
                              className="px-5 py-2.5 rounded-full bg-rose-600 hover:bg-rose-700 text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                            >
                              <XCircle className="w-4 h-4" />
                              <span>{rejectMutation.isPending ? 'Đang xử lý…' : 'Xác nhận Từ chối'}</span>
                            </button>
                          </div>
                        </form>
                      ) : (
                        <div className="flex items-center justify-end gap-3 pt-2">
                          <button
                            type="button"
                            onClick={() => {
                              setShowRejectForm(true)
                              setActionError('')
                            }}
                            className="px-4 py-2.5 rounded-full border border-rose-300 text-rose-700 hover:bg-rose-50 font-semibold transition-colors border-0 bg-transparent cursor-pointer flex items-center gap-1.5"
                          >
                            <XCircle className="w-4 h-4 text-rose-600" />
                            <span>Từ chối tin</span>
                          </button>

                          <button
                            type="button"
                            onClick={handleApprove}
                            disabled={approveMutation.isPending}
                            className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                            <span>{approveMutation.isPending ? 'Đang duyệt…' : 'Phê duyệt tin'}</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Thao tác Đóng tin vi phạm nếu đang APPROVED */}
                  {activeJob.status === 'APPROVED' && (
                    <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/40 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-rose-800">
                          <Ban className="w-4 h-4 text-rose-600" />
                          <span>Đóng tin khẩn cấp (Phát hiện vi phạm)</span>
                        </div>
                      </div>

                      {showCloseForm ? (
                        <form onSubmit={handleCloseSubmit} className="space-y-3 pt-1">
                          <div>
                            <label className="block font-bold text-slate-700 mb-1">
                              Lý do đóng tin tuyển dụng
                            </label>
                            <textarea
                              rows={2}
                              maxLength={500}
                              value={closeReason}
                              onChange={e => setCloseReason(e.target.value)}
                              placeholder="Ghi rõ vi phạm (ví dụ: bị sinh viên khiếu nại quấy rối, công ty giải thể...)"
                              className="w-full p-2.5 bg-white border border-rose-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                            />
                          </div>
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setShowCloseForm(false)
                                setCloseReason('')
                              }}
                              className="px-3.5 py-1.5 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold transition-colors border-0 bg-transparent cursor-pointer"
                            >
                              Hủy
                            </button>
                            <button
                              type="submit"
                              disabled={closeMutation.isPending}
                              className="px-4 py-1.5 rounded-full bg-rose-600 hover:bg-rose-700 text-white font-semibold flex items-center gap-1 shadow-xs cursor-pointer border-0 disabled:opacity-50"
                            >
                              <Archive className="w-3.5 h-3.5" />
                              <span>{closeMutation.isPending ? 'Đang đóng…' : 'Đóng tin ngay'}</span>
                            </button>
                          </div>
                        </form>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setShowCloseForm(true)}
                          className="px-4 py-2 rounded-full border border-rose-300 text-rose-700 hover:bg-rose-100/70 font-semibold text-xs flex items-center gap-1.5 transition-colors cursor-pointer border-0 bg-white"
                        >
                          <Archive className="w-3.5 h-3.5 text-rose-600" />
                          <span>Đóng tin vi phạm này</span>
                        </button>
                      )}
                    </div>
                  )}
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
