import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Phone,
  Search,
  ShieldAlert,
  User,
  X,
  XCircle,
} from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Card } from '@/components/ui/Card'
import { companiesApi } from '../api/companies.api'
import type {
  AdminCompanyDetailRead,
  AdminCompanyRead,
  CompanyDocType,
  VerificationStatus,
} from '../types/companies.types'
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

const DOC_TYPE_LABELS: Record<CompanyDocType, string> = {
  BUSINESS_LICENSE: 'Giấy phép ĐKKD',
  TAX_CERTIFICATE: 'Chứng nhận Mã số thuế',
  AUTHORIZATION_LETTER: 'Giấy ủy quyền',
  OTHER: 'Tài liệu khác',
}

const COMPANY_SIZE_LABELS: Record<string, string> = {
  '1-10': '1 - 10 nhân sự',
  '11-50': '11 - 50 nhân sự',
  '51-200': '51 - 200 nhân sự',
  '201-500': '201 - 500 nhân sự',
  '501-1000': '501 - 1,000 nhân sự',
  '1000+': 'Trên 1,000 nhân sự',
}

function formatCompanySize(size?: string | null) {
  if (!size) return 'Chưa cập nhật'
  return COMPANY_SIZE_LABELS[size] || size
}

export default function CompanyModerationPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<VerificationStatus | 'ALL'>('PENDING')
  const [searchQuery, setSearchQuery] = useState('')

  // Drawer detail state
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [actionError, setActionError] = useState('')

  // Query list
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['admin-companies', page, statusFilter, searchQuery],
    queryFn: () =>
      companiesApi.list({
        page,
        size: 10,
        verification_status: statusFilter === 'ALL' ? undefined : statusFilter,
        q: searchQuery,
      }),
  })

  // Summary counts query
  const pendingCountQuery = useQuery({
    queryKey: ['admin-companies', 'count', 'PENDING'],
    queryFn: () => companiesApi.list({ verification_status: 'PENDING', size: 1 }),
  })
  const approvedCountQuery = useQuery({
    queryKey: ['admin-companies', 'count', 'APPROVED'],
    queryFn: () => companiesApi.list({ verification_status: 'APPROVED', size: 1 }),
  })
  const rejectedCountQuery = useQuery({
    queryKey: ['admin-companies', 'count', 'REJECTED'],
    queryFn: () => companiesApi.list({ verification_status: 'REJECTED', size: 1 }),
  })

  // Query single company detail for Drawer
  const detailQuery = useQuery({
    queryKey: ['admin-company-detail', selectedCompanyId],
    queryFn: () => (selectedCompanyId ? companiesApi.get(selectedCompanyId) : null),
    enabled: !!selectedCompanyId,
  })

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (id: number) => companiesApi.approve(id),
    onSuccess: (updated: AdminCompanyDetailRead) => {
      setActionError('')
      setShowRejectForm(false)
      setRejectReason('')
      void queryClient.invalidateQueries({ queryKey: ['admin-companies'] })
      void queryClient.invalidateQueries({ queryKey: ['admin-company-detail', updated.id] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message)
    },
  })

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (payload: { id: number; reason: string }) =>
      companiesApi.reject(payload.id, { reject_reason: payload.reason }),
    onSuccess: (updated: AdminCompanyDetailRead) => {
      setActionError('')
      setShowRejectForm(false)
      setRejectReason('')
      void queryClient.invalidateQueries({ queryKey: ['admin-companies'] })
      void queryClient.invalidateQueries({ queryKey: ['admin-company-detail', updated.id] })
    },
    onError: (err: unknown) => {
      setActionError(toApiError(err).message)
    },
  })

  const handleOpenDrawer = (company: AdminCompanyRead) => {
    setSelectedCompanyId(company.id)
    setShowRejectForm(false)
    setRejectReason('')
    setActionError('')
  }

  const handleCloseDrawer = () => {
    setSelectedCompanyId(null)
    setShowRejectForm(false)
    setRejectReason('')
    setActionError('')
  }

  const handleApprove = () => {
    if (!selectedCompanyId) return
    approveMutation.mutate(selectedCompanyId)
  }

  const handleRejectSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCompanyId) return
    if (!rejectReason.trim()) {
      setActionError('Vui lòng nhập lý do từ chối hồ sơ doanh nghiệp.')
      return
    }
    rejectMutation.mutate({ id: selectedCompanyId, reason: rejectReason.trim() })
  }

  const pendingCount = pendingCountQuery.data?.total ?? 0
  const approvedCount = approvedCountQuery.data?.total ?? 0
  const rejectedCount = rejectedCountQuery.data?.total ?? 0

  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3" /> Chờ phê duyệt
          </span>
        )
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" /> Đã phê duyệt
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3 h-3" /> Đã từ chối
          </span>
        )
    }
  }

  const activeDetail = detailQuery.data

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="QUẢN TRỊ NHÀ TRƯỜNG"
        title="Kiểm duyệt Hồ sơ Doanh nghiệp"
        description="Xem xét pháp nhân, mã số thuế và hồ sơ năng lực của các đối tác doanh nghiệp đăng ký tham gia mạng lưới đào tạo."
      />

      {/* 3 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
            <span>CHỜ PHÊ DUYỆT</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-800">{pendingCount}</div>
          <p className="text-[11px] text-amber-600/80 mt-1 mb-0">Hồ sơ đối tác mới đăng ký</p>
        </div>

        <div
          onClick={() => {
            setStatusFilter('APPROVED')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            statusFilter === 'APPROVED'
              ? 'bg-emerald-50/80 border-emerald-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-emerald-700 font-semibold mb-2">
            <span>ĐÃ PHÊ DUYỆT</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-800">{approvedCount}</div>
          <p className="text-[11px] text-emerald-600/80 mt-1 mb-0">Đối tác đủ điều kiện tuyển dụng</p>
        </div>

        <div
          onClick={() => {
            setStatusFilter('REJECTED')
            setPage(1)
          }}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            statusFilter === 'REJECTED'
              ? 'bg-rose-50/80 border-rose-500 shadow-xs'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-rose-700 font-semibold mb-2">
            <span>ĐÃ TỪ CHỐI</span>
            <XCircle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-800">{rejectedCount}</div>
          <p className="text-[11px] text-rose-600/80 mt-1 mb-0">Hồ sơ không đáp ứng tiêu chuẩn</p>
        </div>
      </div>

      {/* Main Table Card */}
      <Card className="table-card overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {/* Toolbar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-slate-50/40">
          {/* Tabs */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-200/60 rounded-xl self-start text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setStatusFilter('PENDING')
                setPage(1)
              }}
              className={`px-3 py-1.5 rounded-lg border-0 transition-all cursor-pointer flex items-center gap-1.5 ${
                statusFilter === 'PENDING'
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
              Đã duyệt
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
              Từ chối
            </button>
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
              Tất cả
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
              placeholder="Tìm theo tên công ty hoặc MST…"
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-[#00288E]/20 focus:border-[#00288E]"
            />
          </div>
        </div>

        {/* Table Content */}
        {isPending ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState message={error.message} onRetry={() => void refetch()} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="Không có doanh nghiệp nào"
            description="Không tìm thấy hồ sơ doanh nghiệp nào phù hợp với bộ lọc hiện tại."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Tên Doanh nghiệp & MST</th>
                    <th className="py-3 px-4">Quy mô / Lĩnh vực</th>
                    <th className="py-3 px-4">Người liên hệ</th>
                    <th className="py-3 px-4">Ngày đăng ký</th>
                    <th className="py-3 px-4">Trạng thái</th>
                    <th className="py-3 px-4 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {data.items.map(company => (
                    <tr
                      key={company.id}
                      className="hover:bg-blue-50/30 transition-colors cursor-pointer"
                      onClick={() => handleOpenDrawer(company)}
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#131B2E] text-sm">{company.name}</div>
                        <div className="flex items-center gap-2 mt-0.5 text-slate-500 text-[11px]">
                          <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                            MST: {company.tax_code}
                          </span>
                          {company.website && (
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={e => e.stopPropagation()}
                              className="text-[#00288E] hover:underline flex items-center gap-0.5"
                            >
                              <span>Website</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        <span>{formatCompanySize(company.company_size)}</span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        {company.contact_name ? (
                          <div>
                            <div className="font-medium text-slate-800">{company.contact_name}</div>
                            {company.contact_phone && (
                              <div className="text-[11px] text-slate-500 font-mono">
                                {company.contact_phone}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 text-[11px] whitespace-nowrap">
                        {formatDate(company.created_at)}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {getStatusBadge(company.verification_status)}
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={e => {
                            e.stopPropagation()
                            handleOpenDrawer(company)
                          }}
                          className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border-0 cursor-pointer ${
                            company.verification_status === 'PENDING'
                              ? 'bg-[#00288E] hover:bg-[#001E6C] text-white shadow-xs'
                              : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                          }`}
                        >
                          {company.verification_status === 'PENDING' ? (
                            <>
                              <FileCheck className="w-3.5 h-3.5" /> Xét duyệt
                            </>
                          ) : (
                            <>
                              <Eye className="w-3.5 h-3.5" /> Hồ sơ
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

      {/* Slide-over Drawer Xem chi tiết & Xét duyệt Doanh nghiệp (D04) */}
      {selectedCompanyId && (
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
                    HỒ SƠ DOANH NGHIỆP #{selectedCompanyId}
                  </span>
                  {activeDetail && getStatusBadge(activeDetail.verification_status)}
                </div>
                <h3 className="font-bold text-lg text-[#131B2E] m-0">
                  {activeDetail ? activeDetail.name : 'Đang tải hồ sơ…'}
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
              ) : activeDetail ? (
                <>
                  {/* Alert Error if action failed */}
                  {actionError && (
                    <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
                      <span>{actionError}</span>
                    </div>
                  )}

                  {/* Thông tin pháp lý & Liên hệ */}
                  <div className="space-y-3">
                    <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider m-0">
                      Thông tin Pháp nhân & Liên hệ
                    </h4>
                    <div className="grid grid-cols-2 gap-3 text-slate-700">
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                        <span className="block text-slate-400 text-[10px] uppercase font-bold">
                          Mã số thuế (MST)
                        </span>
                        <strong className="text-slate-800 font-mono text-sm">
                          {activeDetail.tax_code}
                        </strong>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                        <span className="block text-slate-400 text-[10px] uppercase font-bold">
                          Quy mô nhân sự
                        </span>
                        <strong className="text-slate-800">
                          {formatCompanySize(activeDetail.company_size)}
                        </strong>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                      <div>
                        <span className="block text-slate-400 text-[10px] uppercase font-bold">
                          Địa chỉ trụ sở
                        </span>
                        <span className="text-slate-800 font-medium">
                          {activeDetail.address || 'Chưa khai báo địa chỉ'}
                        </span>
                      </div>
                      {activeDetail.website && (
                        <div>
                          <span className="block text-slate-400 text-[10px] uppercase font-bold">
                            Website chính thức
                          </span>
                          <a
                            href={activeDetail.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[#00288E] hover:underline flex items-center gap-1 font-medium"
                          >
                            <span>{activeDetail.website}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>

                    {(activeDetail.contact_name || activeDetail.contact_phone) && (
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-slate-400" />
                          <span className="font-semibold text-slate-800">
                            {activeDetail.contact_name || 'Người liên hệ'}
                          </span>
                        </div>
                        {activeDetail.contact_phone && (
                          <div className="flex items-center gap-1 font-mono text-slate-600">
                            <Phone className="w-3.5 h-3.5 text-slate-400" />
                            <span>{activeDetail.contact_phone}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Giới thiệu & Phúc lợi */}
                  {(activeDetail.description || activeDetail.benefits) && (
                    <div className="space-y-3">
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider m-0">
                        Mô tả & Chế độ Đãi ngộ
                      </h4>
                      {activeDetail.description && (
                        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                          <p className="text-slate-700 m-0 leading-relaxed whitespace-pre-wrap">
                            {activeDetail.description}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Giấy tờ xác thực doanh nghiệp (Verification Documents) */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider m-0">
                        Giấy tờ Xác thực Doanh nghiệp ({activeDetail.documents.length})
                      </h4>
                    </div>

                    {activeDetail.documents.length === 0 ? (
                      <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-800 flex items-start gap-2.5">
                        <ShieldAlert className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                        <div>
                          <strong className="block font-bold">Chưa đính kèm tài liệu số hóa</strong>
                          <span className="text-[11px] text-amber-700">
                            Doanh nghiệp chưa tải lên bản quét Giấy phép ĐKKD hoặc Mã số thuế. Vui lòng cân nhắc kỹ trước khi phê duyệt.
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {activeDetail.documents.map(doc => (
                          <div
                            key={doc.id}
                            className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-[#00288E]/40 flex items-center justify-between transition-colors shadow-2xs"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 rounded-xl bg-blue-50 text-[#00288E] flex items-center justify-center shrink-0">
                                <FileText className="w-4 h-4" />
                              </div>
                              <div>
                                <div className="font-bold text-slate-800 text-xs">
                                  {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type}
                                </div>
                                <div className="text-[10px] text-slate-400 mt-0.5">
                                  Tải lên: {formatDate(doc.uploaded_at)}
                                </div>
                              </div>
                            </div>
                            <a
                              href={doc.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1.5 rounded-full bg-slate-100 hover:bg-[#00288E] text-slate-700 hover:text-white font-semibold text-[11px] flex items-center gap-1 transition-colors"
                            >
                              <span>Mở kiểm tra</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Lịch sử trạng thái */}
                  {activeDetail.verification_status === 'APPROVED' && (
                    <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <strong className="block font-bold text-sm">Doanh nghiệp đã được phê duyệt</strong>
                        <span className="text-[11px] text-emerald-700">
                          Phê duyệt ngày {formatDate(activeDetail.verified_at)} bởi Quản trị viên #{activeDetail.verified_by || 'Admin'}. Doanh nghiệp có toàn quyền đăng tin tuyển dụng.
                        </span>
                      </div>
                    </div>
                  )}

                  {activeDetail.verification_status === 'REJECTED' && (
                    <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3">
                      <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                      <div className="space-y-1">
                        <strong className="block font-bold text-sm">Hồ sơ đã bị từ chối</strong>
                        {activeDetail.reject_reason && (
                          <p className="text-xs text-rose-700 m-0 font-medium">
                            Lý do: &ldquo;{activeDetail.reject_reason}&rdquo;
                          </p>
                        )}
                        <span className="text-[10px] text-rose-500 block">
                          Thời gian từ chối: {formatDate(activeDetail.verified_at)}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Hành động phê duyệt / từ chối khi PENDING */}
                  {activeDetail.verification_status === 'PENDING' && (
                    <div className="p-5 rounded-2xl border-2 border-slate-200 bg-slate-50/60 space-y-4">
                      <div className="flex items-center gap-2 font-bold text-sm text-[#131B2E]">
                        <Building2 className="w-4 h-4 text-[#00288E]" />
                        <span>Quyết định Kiểm duyệt Đối tác</span>
                      </div>

                      {showRejectForm ? (
                        <form onSubmit={handleRejectSubmit} className="space-y-3">
                          <div>
                            <label className="block font-bold text-slate-700 mb-1">
                              Lý do từ chối hồ sơ <span className="text-red-500">*</span>
                            </label>
                            <textarea
                              rows={3}
                              maxLength={500}
                              value={rejectReason}
                              onChange={e => setRejectReason(e.target.value)}
                              placeholder="Nêu rõ lý do (Mã số thuế không tồn tại, thiếu giấy phép kinh doanh, thông tin liên hệ không chính xác...)"
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
                            <span>Từ chối hồ sơ</span>
                          </button>

                          <button
                            type="button"
                            onClick={handleApprove}
                            disabled={approveMutation.isPending}
                            className="px-5 py-2.5 rounded-full bg-[#00288E] hover:bg-[#001E6C] text-white font-semibold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer border-0 disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                            <span>{approveMutation.isPending ? 'Đang phê duyệt…' : 'Phê duyệt Doanh nghiệp'}</span>
                          </button>
                        </div>
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
