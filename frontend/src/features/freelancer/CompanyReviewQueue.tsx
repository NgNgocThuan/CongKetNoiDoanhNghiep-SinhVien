import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { http } from '@/lib/http'
import { toast } from '@/lib/toast'
import { Badge, LoadingError, Notice, Panel } from './ui'
import { DocumentPreview } from './DocumentPreview'
import { errorText } from './messages'

interface Review {
  applicant_email?: string
  authority_data?: { applicant_name?: string; applicant_position?: string; applicant_phone?: string; applicant_capacity?: string; authority_file_id?: number }
  id: number
  company_name: string
  tax_code: string
  legal_representative?: string
  business_address?: string
  verification_status?: string
  status?: string
  license_file_id?: number
  document_file_id?: number
  registry_lookup_url?: string
  mou_type?: string
}

export default function CompanyReviewQueue() {
  const [kind, setKind] = useState<'business' | 'mou'>('business')
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<Review | null>(null)
  const query = useQuery<Review[]>({
    queryKey: ['freelancer', 'company-review', kind, offset],
    queryFn: async () => (await http.get(kind === 'business' ? '/admin/verifications' : '/admin/mou/agreements', { params: { status: kind === 'business' ? 'PENDING' : 'PENDING_REVIEW', limit: 20, offset } })).data,
    refetchInterval: 10000,
  })
  return <Panel title="Xác minh doanh nghiệp & quyền đại diện">
    <Notice>Tra cứu MST chỉ xác nhận doanh nghiệp tồn tại. Cần xác minh người đăng ký được phép tuyển dụng. MOU là thỏa thuận hợp tác riêng, không bắt buộc để duyệt doanh nghiệp. Hồ sơ cũ thiếu bằng chứng phải được yêu cầu bổ sung.</Notice>
    <div className="fl-tabs">{(['business', 'mou'] as const).map(value => <button key={value} type="button" className={kind === value ? 'active' : ''} onClick={() => { setKind(value); setOffset(0); setSelected(null) }}>{value === 'business' ? 'Giấy phép kinh doanh' : 'MOU ký giấy / ký số'}</button>)}</div>
    <LoadingError query={query} />
    {query.data && <>
      {query.data.length === 0 && <Notice>Không có hồ sơ chờ duyệt.</Notice>}
      <div className="fl-review-list">{query.data.map(row => <button type="button" className="fl-review-row" key={row.id} onClick={() => setSelected(row)}><span><strong>{row.company_name}</strong><small>MST {row.tax_code}</small></span><Badge value={row.verification_status ?? row.status} /><span>Xem hồ sơ →</span></button>)}</div>
      <div className="fl-actions"><button className="fl-button secondary" disabled={!offset} onClick={() => { setOffset(offset - 20); setSelected(null) }}>Trang trước</button><button className="fl-button secondary" disabled={query.data.length < 20} onClick={() => { setOffset(offset + 20); setSelected(null) }}>Trang sau</button></div>
      {selected && <ReviewForm key={`${kind}:${selected.id}`} row={selected} kind={kind} onDone={() => setSelected(null)} />}
    </>}
  </Panel>
}

function ReviewForm({ row, kind, onDone }: { row: Review; kind: 'business' | 'mou'; onDone: () => void }) {
  const client = useQueryClient()
  const [preview, setPreview] = useState<Blob | null>(null)
  const [decision, setDecision] = useState('APPROVE')
  const fileId = row.license_file_id ?? row.document_file_id
  const view = useMutation({
    mutationFn: async (id: number = Number(fileId)) => {
      const res = await http.get(`/files/${id}/download`, { responseType: 'blob' })
      setPreview(res.data)
    },
    onError: (error: unknown) => toast.error(errorText(error)),
  })
  const review = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const reason = String(new FormData(form).get('reason') ?? '').trim()
      const data = new FormData(form)
      const body = kind === 'business' ? { status: decision === 'APPROVE' ? 'VERIFIED' : decision, reason,
        legal_identity_checked: data.get('legal_identity_checked') === 'on',
        representative_authority_checked: data.get('representative_authority_checked') === 'on',
        verification_method: data.get('verification_method'), independent_source: data.get('independent_source'), confirmation_reference: data.get('confirmation_reference'),
      } : { action: decision, note: reason }
      return http.post(kind === 'business' ? `/admin/verifications/${row.id}/review` : `/admin/mou/agreements/${row.id}/review`, body)
    },
    onSuccess: async () => { toast.success('Đã lưu kết quả thẩm định.'); await client.invalidateQueries({ queryKey: ['freelancer'] }); onDone() },
    onError: (error: unknown) => toast.error(errorText(error)),
  })
  return <section className="fl-verification fl-verification-summary" aria-label="Chi tiết hồ sơ thẩm định">
    <h3>{row.company_name} · {row.tax_code}</h3>
    {kind === 'business' && <>
      <p>Người đăng ký: {row.authority_data?.applicant_name ?? 'Chưa bổ sung'} · {row.authority_data?.applicant_position} · {row.applicant_email} · {row.authority_data?.applicant_phone}</p>
      <p>Tư cách: {row.authority_data?.applicant_capacity === 'LEGAL_REPRESENTATIVE' ? 'Người đại diện pháp luật' : 'Người được ủy quyền tuyển dụng'}</p>
      <Notice>Chủ động tìm đầu mối từ nguồn độc lập. Không dùng riêng website, số điện thoại hoặc giấy tờ do người nộp tự khai để kết luận. Xác nhận cụ thể người mang tên/email trên có quyền tuyển dụng. Nếu chưa đủ căn cứ, chọn Yêu cầu bổ sung; không bắt doanh nghiệp ký MOU.</Notice>
      {row.authority_data?.authority_file_id && <button className="fl-button secondary" type="button" onClick={() => view.mutate(Number(row.authority_data!.authority_file_id))}>Xem bằng chứng quyền đại diện</button>}
    </>}
    {row.legal_representative && <p>Đại diện: {row.legal_representative} · {row.business_address}</p>}
    <div className="fl-actions"><button type="button" className="fl-button secondary" onClick={() => view.mutate(Number(fileId))} disabled={!fileId || view.isPending}>{view.isPending ? 'Đang tải…' : 'Xem giấy phép / tài liệu MOU'}</button>{kind === 'business' && <a className="fl-button secondary" href="https://dangkykinhdoanh.gov.vn/vn/Pages/Trangchu.aspx" target="_blank" rel="noreferrer">Tra cứu cổng quốc gia</a>}</div>
    {view.isError && <Notice danger>{errorText(view.error)}</Notice>}
    <DocumentPreview file={preview} />
    <form onSubmit={event => { event.preventDefault(); review.mutate(event.currentTarget) }}>
      <fieldset className="fl-verification-fields" disabled={review.isPending}>
        <legend>Kết quả thẩm định</legend>
        <label>Quyết định<select value={decision} onChange={event => setDecision(event.target.value)}><option value="APPROVE">Phê duyệt</option><option value="REJECTED" hidden={kind === 'mou'}>Từ chối</option>{kind === 'mou' && <option value="REJECT">Từ chối MOU</option>}{kind === 'business' && <option value="NEEDS_REVISION">Yêu cầu bổ sung</option>}</select></label>
        <label>Lý do / ghi chú<textarea name="reason" required={decision !== 'APPROVE'} maxLength={1000} /></label>
        {decision === 'APPROVE' && kind === 'business' && <>
          <label><input name="legal_identity_checked" type="checkbox" required />Đã đối chiếu pháp nhân, MST, tình trạng hoạt động và người đại diện với nguồn chính thức.</label>
          <label><input name="representative_authority_checked" type="checkbox" required />Đã xác minh danh tính / quyền đại diện tuyển dụng của người đăng ký.</label>
          <label>Phương thức xác minh<select name="verification_method" required><option value="">Chọn phương thức</option><option value="IDENTITY_MATCH">Đối chiếu danh tính người đại diện pháp luật</option><option value="OFFICIAL_EMAIL">Xác nhận qua email chính thức đã đối chiếu độc lập</option><option value="INDEPENDENT_CALLBACK">Gọi lại đầu mối doanh nghiệp độc lập</option><option value="IN_PERSON">Xác nhận trực tiếp với người đại diện</option></select></label>
          <label>Nguồn đối chiếu độc lập<input name="independent_source" required maxLength={1000} placeholder="Nguồn tìm đầu mối hoặc phương thức đối chiếu danh tính" /></label>
          <label>Thông tin xác nhận<input name="confirmation_reference" required maxLength={1000} placeholder="Đầu mối, thời điểm, mã tham chiếu hoặc biên bản xác nhận" /></label>
          <small>Đây là bằng chứng thẩm định, không phải lý do phê duyệt. Không ghi số CCCD đầy đủ hoặc dữ liệu nhạy cảm không cần thiết.</small>
        </>}
        {review.isError && <Notice danger>{errorText(review.error)}</Notice>}
        <button className="fl-button" type="submit" disabled={!fileId || (decision === 'APPROVE' && !preview)}>{review.isPending ? 'Đang lưu…' : 'Lưu kết quả'}</button>
      </fieldset>
    </form>
  </section>
}
