import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { http } from '@/lib/http'
import { downloadFile } from '@/utils/download'
import { PageHeader } from '@/components/common/PageHeader'
import { LoadingState, ErrorState, EmptyState } from '@/components/common/States'
import { Pagination } from '@/components/common/Pagination'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { companyApi } from './api'
import type { CompanyProfile } from './api'
import './company.css'

const statuses: Record<string, string> = { DRAFT: 'Bản nháp', PENDING_APPROVAL: 'Chờ duyệt', APPROVED: 'Đã duyệt', REJECTED: 'Bị từ chối', CLOSED: 'Đã đóng', EXPIRED: 'Hết hạn', APPLIED: 'Đã nộp', SCREENING: 'Sơ loại', SHORTLISTED: 'Danh sách ngắn', INTERVIEW: 'Phỏng vấn', OFFER: 'Đề nghị tuyển', HIRED: 'Đã tuyển', WITHDRAWN: 'Đã rút', PENDING: 'Đang chờ', ACCEPTED: 'Đã ứng tuyển', DECLINED: 'Đã từ chối' }
function ErrorMessage({ error }: { error: Error | null }) { return error ? <p className="company-error" role="alert">{error.message}</p> : null }

function ProfileForm({ data }: { data: CompanyProfile }) {
  const client = useQueryClient()
  const [form, setForm] = useState({ address: data.address || '', website: data.website || '', description: data.description || '', contact_name: data.contact_name || '', contact_phone: data.contact_phone || '' })
  const save = useMutation({ mutationFn: () => companyApi.saveProfile(Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim() || null]))), onSuccess: () => { void client.invalidateQueries({ queryKey: ['company-profile'] }) } })
  return <form className="company-form" onSubmit={event => { event.preventDefault(); save.mutate() }}><div className="company-readonly"><strong>{data.name}</strong><span>Mã số thuế: {data.tax_code}</span><span>Xác thực: {data.verification_status === 'APPROVED' ? 'Đã duyệt' : data.verification_status}</span></div>{Object.entries({ address: 'Địa chỉ', website: 'Website', contact_name: 'Người liên hệ', contact_phone: 'Điện thoại' }).map(([key, label]) => <label key={key}>{label}<input type={key === 'website' ? 'url' : 'text'} value={form[key as keyof typeof form]} onChange={event => setForm({ ...form, [key]: event.target.value })} /></label>)}<label>Giới thiệu doanh nghiệp<textarea rows={6} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /></label><ErrorMessage error={save.error} />{save.isSuccess && <p role="status">Đã lưu hồ sơ.</p>}<Button type="submit" pending={save.isPending}>Lưu hồ sơ</Button></form>
}
export function CompanyProfilePage() {
  const query = useQuery({ queryKey: ['company-profile'], queryFn: companyApi.profile })
  return <section className="company-live"><PageHeader title="Hồ sơ doanh nghiệp" description="Thông tin doanh nghiệp đang đăng nhập." />{query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : <ProfileForm data={query.data} />}</section>
}
function DraftJobDialog({ onClose }: { onClose: () => void }) {
  const client = useQueryClient()
  const types = useQuery({ queryKey: ['catalog', 'company-job-types'], queryFn: async () => (await http.get<{ items: { id: number; name: string }[] }>('/catalog/job-types', { params: { size: 100 } })).data })
  const [form, setForm] = useState({ title: '', position: '', job_type_id: '', description: '', deadline: '', location: '' })
  const save = useMutation({ mutationFn: async () => http.post('/jobs', { ...form, job_type_id: Number(form.job_type_id), quantity: 1, work_mode: 'ONSITE' }), onSuccess: () => { void client.invalidateQueries({ queryKey: ['company-jobs'] }); onClose() } })
  return <Dialog open title="Tạo tin tuyển dụng" onOpenChange={open => { if (!open && !save.isPending) onClose() }}>{types.isPending ? <LoadingState /> : types.isError ? <ErrorState message={types.error.message} onRetry={() => void types.refetch()} /> : <form className="company-form" onSubmit={event => { event.preventDefault(); save.mutate() }}>{Object.entries({ title: 'Tiêu đề', position: 'Vị trí', deadline: 'Hạn nộp', location: 'Địa điểm' }).map(([key, label]) => <label key={key}>{label}<input required={key !== 'location'} maxLength={255} type={key === 'deadline' ? 'date' : 'text'} value={form[key as keyof typeof form]} onChange={event => setForm({ ...form, [key]: event.target.value })} /></label>)}<label>Loại hình công việc<select aria-label="Loại hình công việc" required value={form.job_type_id} onChange={event => setForm({ ...form, job_type_id: event.target.value })}><option value="">Chọn loại hình</option>{types.data.items.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Mô tả<textarea required rows={5} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /></label><ErrorMessage error={save.error} /><Button type="submit" pending={save.isPending}>Lưu nháp</Button></form>}</Dialog>
}
export function CompanyJobsPage() {
  const [page, setPage] = useState(1), [create, setCreate] = useState(false)
  const client = useQueryClient()
  const query = useQuery({ queryKey: ['company-jobs', page], queryFn: () => companyApi.jobs(page) })
  const mutation = useMutation({ mutationFn: async ({ id, action }: { id: number; action: string }) => http.post('/jobs/' + id + '/' + action), onSuccess: () => { void client.invalidateQueries({ queryKey: ['company-jobs'] }) } })
  return <section className="company-live"><PageHeader title="Tin tuyển dụng" description="Tin thuộc doanh nghiệp đang đăng nhập." actions={<Button onClick={() => setCreate(true)}>Tạo tin tuyển dụng</Button>} /><ErrorMessage error={mutation.error} />{query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : <>{!query.data.items.length ? <EmptyState title="Chưa có tin tuyển dụng" /> : <div className="company-table"><table><thead><tr><th>Vị trí</th><th>Trạng thái</th><th>Hạn nộp</th><th>Số đơn</th><th>Thao tác</th></tr></thead><tbody>{query.data.items.map(item => <tr key={item.id}><td><strong>{item.title}</strong><br />{item.position}</td><td>{statuses[item.status] || item.status}</td><td>{item.deadline}</td><td>{item.application_count}</td><td><div className="company-actions"><Link to={'/company/candidates?job_id=' + item.id}>Gợi ý ứng viên</Link><Link to={'/company/applications?job_id=' + item.id}>Xem đơn</Link>{['DRAFT', 'REJECTED'].includes(item.status) && <Button size="sm" pending={mutation.isPending} onClick={() => mutation.mutate({ id: item.id, action: 'submit' })}>Gửi duyệt</Button>}{item.status === 'APPROVED' && <Button size="sm" variant="secondary" disabled={mutation.isPending} onClick={() => { if (window.confirm('Đóng tin tuyển dụng này?')) mutation.mutate({ id: item.id, action: 'close' }) }}>Đóng tin</Button>}</div></td></tr>)}</tbody></table></div>}<Pagination page={page} pages={query.data.pages} total={query.data.total} onChange={setPage} /></>}{create && <DraftJobDialog onClose={() => setCreate(false)} />}</section>
}
export function CompanyInvitationsPage() {
  const [page, setPage] = useState(1)
  const query = useQuery({ queryKey: ['invitations', 'company', page], queryFn: () => companyApi.invitations(page) })
  return <section className="company-live"><PageHeader title="Lời mời đã gửi" description="Các lời mời được gửi qua chức năng gợi ý ứng viên." />{query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : <>{!query.data.items.length ? <EmptyState title="Chưa gửi lời mời" /> : <div className="company-table"><table><thead><tr><th>Mã lời mời</th><th>Tin tuyển dụng</th><th>Sinh viên</th><th>Trạng thái</th><th>Lời nhắn</th></tr></thead><tbody>{query.data.items.map(item => <tr key={item.id}><td>#{item.id}</td><td>#{item.job_id}</td><td>#{item.student_id}</td><td>{statuses[item.status] || item.status}</td><td>{item.message || '—'}</td></tr>)}</tbody></table></div>}<Pagination page={page} pages={query.data.pages} total={query.data.total} onChange={setPage} /></>}</section>
}
const transitions: Record<string, string[]> = { APPLIED: ['SCREENING', 'REJECTED'], SCREENING: ['SHORTLISTED', 'REJECTED'], SHORTLISTED: ['INTERVIEW', 'REJECTED'], INTERVIEW: ['OFFER', 'REJECTED'], OFFER: ['HIRED', 'REJECTED'] }
export function CompanyApplicationsPage() {
  const [params, setParams] = useSearchParams(), [page, setPage] = useState(1), [error, setError] = useState('')
  const jobId = Number(params.get('job_id')) || null
  const client = useQueryClient()
  const jobs = useQuery({ queryKey: ['company-jobs', 1], queryFn: () => companyApi.jobs(1) })
  const query = useQuery({ queryKey: ['company-applications', jobId, page], queryFn: () => companyApi.applications(jobId!, page), enabled: jobId !== null })
  const update = useMutation({ mutationFn: async ({ id, status }: { id: number; status: string }) => {
    const note = ['INTERVIEW', 'OFFER'].includes(status) ? window.prompt('Nhập ghi chú/lịch hẹn (tối đa 500 ký tự):') : null
    if (['INTERVIEW', 'OFFER'].includes(status) && note === null) return
    await http.put('/company/applications/' + id + '/status', { status, note })
  }, onSuccess: () => { void client.invalidateQueries({ queryKey: ['company-applications'] }) } })
  return <section className="company-live"><PageHeader title="Quản lý ứng viên" description="Chọn tin tuyển dụng để xem các đơn đã nộp." /><label className="company-picker">Tin tuyển dụng<select aria-label="Tin tuyển dụng" value={jobId ?? ''} onChange={event => { setParams(event.target.value ? { job_id: event.target.value } : {}); setPage(1) }}><option value="">Chọn tin tuyển dụng</option>{jobs.data?.items.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>{jobs.isError && <ErrorState message={jobs.error.message} onRetry={() => void jobs.refetch()} />}<ErrorMessage error={update.error} />{error && <p role="alert">{error}</p>}{!jobId ? <EmptyState title="Chưa chọn tin tuyển dụng" /> : query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : <>{!query.data.items.length ? <EmptyState title="Chưa có đơn ứng tuyển" /> : <div className="company-table"><table><thead><tr><th>Sinh viên</th><th>GPA</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>{query.data.items.map(item => <tr key={item.id}><td>{item.student.full_name}<br />{item.contact_email || 'Không chia sẻ liên hệ'}</td><td>{item.student.gpa === null ? 'Không chia sẻ' : item.student.gpa}</td><td>{statuses[item.current_status] || item.current_status}</td><td><div className="company-actions"><Button size="sm" variant="secondary" onClick={() => { setError(''); void downloadFile(item.cv_download_url, 'cv-don-' + item.id).catch((err: Error) => setError(err.message)) }}>Tải CV đã nộp</Button>{(transitions[item.current_status] || []).map(status => <Button key={status} size="sm" disabled={update.isPending} onClick={() => update.mutate({ id: item.id, status })}>{statuses[status]}</Button>)}</div></td></tr>)}</tbody></table></div>}<Pagination page={page} pages={query.data.pages} total={query.data.total} onChange={setPage} /></>}</section>
}
