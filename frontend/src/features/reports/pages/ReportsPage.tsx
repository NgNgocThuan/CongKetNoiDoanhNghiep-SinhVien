import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  AlertTriangle,
  Building2,
  CheckCircle2,
  Clock,
  Eye,
  FileCheck,
  FileText,
  Filter,
  GraduationCap,
  Lock,
  ShieldAlert,
  X,
  XCircle,
} from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Card } from '@/components/ui/Card'
import { reportsApi } from '../api/reports.api'
import type { Report, ReportHandle, ReportStatus, ReportTargetType } from '../types/reports.types'
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

export default function ReportsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [selectedStatus, setSelectedStatus] = useState<ReportStatus | 'ALL'>('ALL')
  const [selectedTargetType, setSelectedTargetType] = useState<ReportTargetType | 'ALL'>('ALL')

  // Selected report for slide-over drawer
  const [activeReport, setActiveReport] = useState<Report | null>(null)

  // Drawer form state
  const [verdictStatus, setVerdictStatus] = useState<ReportStatus>('RESOLVED')
  const [resolutionNote, setResolutionNote] = useState('')
  const [lockTargetUser, setLockTargetUser] = useState(false)
  const [closeTargetJob, setCloseTargetJob] = useState(false)
  const [formError, setFormError] = useState('')

  // Query list
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['reports', page, selectedStatus, selectedTargetType],
    queryFn: () =>
      reportsApi.list({
        page,
        size: 10,
        status: selectedStatus === 'ALL' ? undefined : selectedStatus,
        target_type: selectedTargetType === 'ALL' ? undefined : selectedTargetType,
      }),
  })

  // Summary counts query
  const pendingCountQuery = useQuery({
    queryKey: ['reports', 'count', 'PENDING'],
    queryFn: () => reportsApi.list({ status: 'PENDING', size: 1 }),
  })
  const resolvedCountQuery = useQuery({
    queryKey: ['reports', 'count', 'RESOLVED'],
    queryFn: () => reportsApi.list({ status: 'RESOLVED', size: 1 }),
  })
  const rejectedCountQuery = useQuery({
    queryKey: ['reports', 'count', 'REJECTED'],
    queryFn: () => reportsApi.list({ status: 'REJECTED', size: 1 }),
  })

  // Mutation for handling report
  const handleMutation = useMutation({
    mutationFn: (payload: { id: number; data: ReportHandle }) =>
      reportsApi.handle(payload.id, payload.data),
    onSuccess: updated => {
      setActiveReport(updated)
      setFormError('')
      void queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (err: unknown) => {
      setFormError(toApiError(err).message)
    },
  })

  const openDrawer = (report: Report) => {
    setActiveReport(report)
    setVerdictStatus('RESOLVED')
    setResolutionNote('')
    setLockTargetUser(report.target_type === 'COMPANY' || report.target_type === 'STUDENT')
    setCloseTargetJob(report.target_type === 'JOB')
    setFormError('')
  }

  const closeDrawer = () => {
    setActiveReport(null)
    setFormError('')
  }

  const handleSubmitVerdict = (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeReport) return
    handleMutation.mutate({
      id: activeReport.id,
      data: {
        status: verdictStatus,
        resolution_note: resolutionNote.trim() || null,
        lock_target_user: verdictStatus === 'RESOLVED' ? lockTargetUser : false,
        close_target_job: verdictStatus === 'RESOLVED' ? closeTargetJob : false,
      },
    })
  }

  const pendingCount = pendingCountQuery.data?.total ?? 0
  const resolvedCount = resolvedCountQuery.data?.total ?? 0
  const rejectedCount = rejectedCountQuery.data?.total ?? 0
  const totalCount = pendingCount + resolvedCount + rejectedCount

  const getTargetBadge = (type: ReportTargetType, targetId: number) => {
    switch (type) {
      case 'JOB':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-[#00288E] border border-blue-200">
            <FileText className="w-3.5 h-3.5" /> Tin tuyển dụng #{targetId}
          </span>
        )
      case 'COMPANY':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-[#006A63] border border-teal-200">
            <Building2 className="w-3.5 h-3.5" /> Doanh nghiệp #{targetId}
          </span>
        )
      case 'STUDENT':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            <GraduationCap className="w-3.5 h-3.5" /> Sinh viên #{targetId}
          </span>
        )
    }
  }

  const getStatusBadge = (status: ReportStatus) => {
    switch (status) {
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3" /> Chờ xử lý
          </span>
        )
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" /> Đã xử lý
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3 h-3" /> Đã bác bỏ
          </span>
        )
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="QUẢN TRỊ VIÊN HỆ THỐNG"
        title="Quản trị Báo cáo Vi phạm"
        description="Xem xét phản ánh vi phạm từ sinh viên và doanh nghiệp, ra phán quyết xử lý và bảo vệ an toàn cho hệ thống."
      />

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => {
            setSelectedStatus('ALL')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            selectedStatus === 'ALL'
              ? 'bg-blue-50/70 border-[#00288E] shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-2">
            <span>TỔNG BÁO CÁO</span>
            <ShieldAlert className="w-4 h-4 text-[#00288E]" />
          </div>
          <div className="text-2xl font-bold text-[#131B2E]">{totalCount}</div>
          <p className="text-[11px] text-slate-400 mt-1 mb-0">Tất cả phản ánh đã gửi</p>
        </div>

        <div
          onClick={() => {
            setSelectedStatus('PENDING')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            selectedStatus === 'PENDING'
              ? 'bg-amber-50/80 border-amber-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-amber-700 font-semibold mb-2">
            <span>CHỜ XỬ LÝ</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-800">{pendingCount}</div>
          <p className="text-[11px] text-amber-600/80 mt-1 mb-0">Cần thẩm định & giải quyết</p>
        </div>

        <div
          onClick={() => {
            setSelectedStatus('RESOLVED')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            selectedStatus === 'RESOLVED'
              ? 'bg-emerald-50/80 border-emerald-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-emerald-700 font-semibold mb-2">
            <span>ĐÃ XỬ LÝ (RESOLVED)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-800">{resolvedCount}</div>
          <p className="text-[11px] text-emerald-600/80 mt-1 mb-0">Đã khóa hoặc đóng tin</p>
        </div>

        <div
          onClick={() => {
            setSelectedStatus('REJECTED')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            selectedStatus === 'REJECTED'
              ? 'bg-rose-50/80 border-rose-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-rose-700 font-semibold mb-2">
            <span>ĐÃ BÁC BỎ (REJECTED)</span>
            <XCircle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-800">{rejectedCount}</div>
          <p className="text-[11px] text-rose-600/80 mt-1 mb-0">Không đủ căn cứ vi phạm</p>
        </div>
      </div>

      {/* Main Table Card */}
      <Card className="table-card overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {/* Filter bar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-slate-50/40">
          {/* Tabs Trạng thái */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl self-start text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setSelectedStatus('ALL')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                selectedStatus === 'ALL'
                  ? 'bg-white text-[#00288E] shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Tất cả
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedStatus('PENDING')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer flex items-center gap-1.5 ${
                selectedStatus === 'PENDING'
                  ? 'bg-white text-amber-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>Chờ xử lý</span>
              {pendingCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
              )}
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedStatus('RESOLVED')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                selectedStatus === 'RESOLVED'
                  ? 'bg-white text-emerald-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Đã xử lý
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedStatus('REJECTED')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer ${
                selectedStatus === 'REJECTED'
                  ? 'bg-white text-rose-700 shadow-xs'
                  : 'bg-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              Đã bác bỏ
            </button>
          </div>

          {/* Target Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedTargetType}
              onChange={e => {
                setSelectedTargetType(e.target.value as ReportTargetType | 'ALL')
                setPage(1)
              }}
              className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E] cursor-pointer"
            >
              <option value="ALL">Mọi đối tượng vi phạm</option>
              <option value="JOB">Tin tuyển dụng (JOB)</option>
              <option value="COMPANY">Doanh nghiệp (COMPANY)</option>
              <option value="STUDENT">Sinh viên (STUDENT)</option>
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
            title="Không có báo cáo nào"
            description="Hiện không có phản ánh vi phạm nào khớp với điều kiện lọc đã chọn."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Mã</th>
                    <th className="py-3 px-4">Đối tượng bị phản ánh</th>
                    <th className="py-3 px-4">Lý do vi phạm</th>
                    <th className="py-3 px-4">Người gửi</th>
                    <th className="py-3 px-4">Thời gian</th>
                    <th className="py-3 px-4">Trạng thái</th>
                    <th className="py-3 px-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {data.items.map(report => (
                    <tr
                      key={report.id}
                      className="hover:bg-blue-50/30 transition-colors cursor-pointer"
                      onClick={() => openDrawer(report)}
                    >
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-700">
                        #{report.id}
                      </td>
                      <td className="py-3.5 px-4">
                        {getTargetBadge(report.target_type, report.target_id)}
                      </td>
                      <td className="py-3.5 px-4 max-w-xs">
                        <p className="font-medium text-slate-800 line-clamp-2 m-0 leading-relaxed">
                          {report.reason}
                        </p>
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        <span className="font-mono text-[11px] bg-slate-100 px-2 py-0.5 rounded">
                          User #{report.reporter_id}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px] whitespace-nowrap">
                        {formatDate(report.created_at)}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getStatusBadge(report.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={e => {
                            e.stopPropagation()
                            openDrawer(report)
                          }}
                          className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border-0 cursor-pointer ${
                            report.status === 'PENDING'
                              ? 'bg-[#00288E] hover:bg-[#001E6C] text-white shadow-xs'
                              : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                          }`}
                        >
                          {report.status === 'PENDING' ? (
                            <>
                              <FileCheck className="w-3.5 h-3.5" /> Xét xử lý
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

      {/* Slide-over Drawer Xử lý Báo cáo (D09) */}
      {activeReport && (
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
                    BÁO CÁO #{activeReport.id}
                  </span>
                  {getStatusBadge(activeReport.status)}
                </div>
                <h3 className="font-bold text-lg text-[#131B2E] m-0">
                  Chi tiết Phản ánh & Phán quyết
                </h3>
              </div>
              <button
                type="button"
                onClick={closeDrawer}
                className="w-8 h-8 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors border-0 bg-transparent cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body Drawer */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs">
              {/* Thẻ đối tượng bị phản ánh */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Đối tượng bị báo cáo vi phạm
                </div>
                <div className="flex items-center justify-between">
                  <div>{getTargetBadge(activeReport.target_type, activeReport.target_id)}</div>
                  <span className="text-slate-500 font-mono text-[11px]">
                    ID: #{activeReport.target_id}
                  </span>
                </div>
              </div>

              {/* Thông tin báo cáo */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-slate-600">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="block text-slate-400 text-[10px] uppercase font-bold">
                      Người gửi phản ánh
                    </span>
                    <strong className="text-slate-800 font-mono">
                      User #{activeReport.reporter_id}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="block text-slate-400 text-[10px] uppercase font-bold">
                      Thời gian phản ánh
                    </span>
                    <strong className="text-slate-800">
                      {formatDate(activeReport.created_at)}
                    </strong>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                  <span className="block text-slate-400 text-[10px] uppercase font-bold">
                    Nội dung tố cáo chi tiết
                  </span>
                  <p className="text-slate-800 text-xs leading-relaxed whitespace-pre-wrap m-0 font-medium">
                    {activeReport.reason}
                  </p>
                </div>
              </div>

              {/* Nếu đã xử lý xong */}
              {activeReport.status !== 'PENDING' ? (
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 space-y-3">
                  <div className="flex items-center gap-2 font-bold text-slate-700">
                    <FileCheck className="w-4 h-4 text-[#00288E]" />
                    <span>Kết quả thẩm định của Ban Quản trị</span>
                  </div>
                  <div className="space-y-2 text-slate-600">
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase block font-bold">
                        Quản trị viên xử lý:
                      </span>
                      <span className="font-semibold text-slate-800 font-mono">
                        Admin #{activeReport.handled_by || 'Hệ thống'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase block font-bold">
                        Thời gian phán quyết:
                      </span>
                      <span className="text-slate-800">
                        {formatDate(activeReport.handled_at)}
                      </span>
                    </div>
                    {activeReport.resolution_note && (
                      <div className="pt-2 border-t border-slate-200/60">
                        <span className="text-slate-400 text-[10px] uppercase block font-bold">
                          Ghi chú giải quyết:
                        </span>
                        <p className="text-slate-800 font-medium mt-1 mb-0 leading-relaxed">
                          {activeReport.resolution_note}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                /* Form phán quyết kiểm duyệt (Admin D09) */
                <form
                  onSubmit={handleSubmitVerdict}
                  className="p-5 rounded-2xl border-2 border-blue-200 bg-blue-50/20 space-y-4"
                >
                  <div className="flex items-center gap-2 font-bold text-sm text-[#00288E]">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Ra phán quyết xử lý (Admin Action)</span>
                  </div>

                  {formError && (
                    <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                      <span>{formError}</span>
                    </div>
                  )}

                  {/* Lựa chọn phán quyết */}
                  <div className="space-y-2">
                    <label className="block font-bold text-slate-700">
                      Phán quyết kiểm duyệt <span className="text-red-500">*</span>
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <label
                        className={`p-3 rounded-xl border-2 flex items-center gap-2.5 cursor-pointer transition-all ${
                          verdictStatus === 'RESOLVED'
                            ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="verdict"
                          checked={verdictStatus === 'RESOLVED'}
                          onChange={() => setVerdictStatus('RESOLVED')}
                          className="w-4 h-4 text-emerald-600 border-slate-300 focus:ring-emerald-500"
                        />
                        <span>Xác nhận vi phạm (RESOLVED)</span>
                      </label>

                      <label
                        className={`p-3 rounded-xl border-2 flex items-center gap-2.5 cursor-pointer transition-all ${
                          verdictStatus === 'REJECTED'
                            ? 'bg-rose-50 border-rose-500 text-rose-800 font-bold'
                            : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                      >
                        <input
                          type="radio"
                          name="verdict"
                          checked={verdictStatus === 'REJECTED'}
                          onChange={() => setVerdictStatus('REJECTED')}
                          className="w-4 h-4 text-rose-600 border-slate-300 focus:ring-rose-500"
                        />
                        <span>Bác bỏ tố cáo (REJECTED)</span>
                      </label>
                    </div>
                  </div>

                  {/* Hành động liên đới khi RESOLVED */}
                  {verdictStatus === 'RESOLVED' && (
                    <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl space-y-2.5">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-amber-800">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span>Hành động liên đới tự động (Cascade Actions)</span>
                      </div>

                      {activeReport.target_type === 'JOB' && (
                        <label className="flex items-start gap-2.5 cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={closeTargetJob}
                            onChange={e => setCloseTargetJob(e.target.checked)}
                            className="mt-0.5 w-4 h-4 rounded text-rose-600 border-slate-300 focus:ring-rose-500"
                          />
                          <span className="text-slate-700 font-medium">
                            Tự động <strong>đóng tin tuyển dụng</strong> vi phạm này ngay lập tức
                          </span>
                        </label>
                      )}

                      {(activeReport.target_type === 'COMPANY' ||
                        activeReport.target_type === 'STUDENT') && (
                        <label className="flex items-start gap-2.5 cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={lockTargetUser}
                            onChange={e => setLockTargetUser(e.target.checked)}
                            className="mt-0.5 w-4 h-4 rounded text-rose-600 border-slate-300 focus:ring-rose-500"
                          />
                          <span className="text-slate-700 font-medium flex items-center gap-1">
                            <Lock className="w-3.5 h-3.5 text-rose-600 inline" />
                            Tự động <strong>khóa tài khoản</strong> của đối tượng vi phạm này
                          </span>
                        </label>
                      )}
                    </div>
                  )}

                  {/* Ghi chú giải quyết */}
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">
                      Ghi chú giải quyết của Quản trị viên (resolution_note)
                    </label>
                    <textarea
                      rows={3}
                      maxLength={500}
                      value={resolutionNote}
                      onChange={e => setResolutionNote(e.target.value)}
                      placeholder="Ghi rõ căn cứ xử lý hoặc lý do bác bỏ để lưu hồ sơ thanh tra..."
                      className="w-full p-3 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={closeDrawer}
                      className="px-4 py-2 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-100 font-semibold transition-colors border-0 bg-transparent cursor-pointer"
                    >
                      Hủy bỏ
                    </button>
                    <button
                      type="submit"
                      disabled={handleMutation.isPending}
                      className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>
                        {handleMutation.isPending ? 'Đang lưu…' : 'Xác nhận & Lưu phán quyết'}
                      </span>
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
