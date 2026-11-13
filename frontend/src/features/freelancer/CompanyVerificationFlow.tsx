import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2, CheckCircle2, Mail } from 'lucide-react'
import { http, publicHttp } from '@/lib/http'
import { toast } from '@/lib/toast'
import ContactVerification from './ContactVerification'
import { Badge, LoadingError, Notice } from './ui'
import { errorText } from './messages'
import { DocumentPreview } from './DocumentPreview'

interface VerificationStatus {
  company_name?: string
  tax_code?: string
  legal_representative?: string
  business_address?: string
  email_otp_verified: boolean
  verification_status: string
  license_file_id?: number
  rejection_reason?: string
}

export function CompanyVerificationFlow({ token }: { token?: string }) {
  const client = useQueryClient()
  const query = useQuery<VerificationStatus>({
    queryKey: ['freelancer', 'company-verification-status', token ? 'onboarding' : 'workspace'],
    queryFn: async () => (await (token ? publicHttp : http).get('/company/verification/status', token ? { headers: { Authorization: `Bearer ${token}` } } : {})).data,
    refetchInterval: 10000,
  })
  return <>
    <LoadingError query={query} />
    {query.data && <VerificationForm token={token} status={query.data} refresh={() => client.invalidateQueries({ queryKey: ['freelancer'] })} />}
  </>
}

function VerificationForm({ status, refresh, token }: { token?: string; status: VerificationStatus; refresh: () => Promise<unknown> }) {
  const [file, setFile] = useState<File | null>(null)
  const verified = status.verification_status === 'VERIFIED'
  const pending = status.verification_status === 'PENDING' && Boolean(status.license_file_id)
  const submit = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      if (!file) throw new Error('Vui lòng chọn giấy phép kinh doanh.')
      const body = new FormData(form)
      body.set('license_file', file)
      return (token ? publicHttp : http).post('/company/verification/submit-legal-docs', body, token ? { headers: { Authorization: `Bearer ${token}` } } : {})
    },
    onSuccess: async () => { toast.success('Đã gửi hồ sơ. Bạn sẽ nhận được thông báo khi có kết quả.'); await refresh() },
    onError: (error: unknown) => toast.error(errorText(error)),
  })
  return <div className="fl-verification">
    <Notice>Xác minh gồm pháp nhân và quyền đại diện tuyển dụng. Không bắt buộc ký MOU. Email Gmail vẫn được chấp nhận; tên miền riêng không tự động được duyệt. Trước khi được xác minh, bạn chỉ hoàn thiện hồ sơ và soạn tin nháp.</Notice>
    <ol className="fl-verification-steps" aria-label="Tiến trình xác minh doanh nghiệp">
      <li aria-current={!status.email_otp_verified ? 'step' : undefined} className={status.email_otp_verified ? 'done' : ''}>
        {status.email_otp_verified ? <CheckCircle2 size={22} /> : <Mail size={22} />}<div><strong>1. Xác minh email</strong><span>{status.email_otp_verified ? 'Đã hoàn tất' : 'Xác nhận hộp thư liên hệ'}</span></div>
      </li>
      <li aria-current={status.email_otp_verified && !verified ? 'step' : undefined} className={verified ? 'done' : ''}>
        {verified ? <CheckCircle2 size={22} /> : <Building2 size={22} />}<div><strong>2. Hồ sơ doanh nghiệp</strong><span>{verified ? 'Đã được duyệt' : pending ? 'Đang chờ thẩm định' : 'Mã số thuế và giấy phép kinh doanh'}</span></div>
      </li>
    </ol>
    <ContactVerification token={token} />
    {status.rejection_reason && <Notice danger>Lý do cần bổ sung: {status.rejection_reason}</Notice>}
    {verified || pending ? <section className="fl-verification-summary">
      <Badge value={verified ? 'VERIFIED' : 'PENDING_REVIEW'} />
      <h3>{verified ? 'Doanh nghiệp đã được xác minh' : 'Hồ sơ đã được tiếp nhận'}</h3>
      <p>{status.company_name} · MST {status.tax_code}</p>
      <p>{verified ? 'Bạn có thể đăng tin tuyển dụng và tạo dự án trong hạn mức được cấp.' : 'Nhà trường đang đối chiếu giấy phép kinh doanh. Kết quả sẽ hiển thị tại đây; bạn không cần nộp lại.'}</p>
    </section> : <form onSubmit={event => { event.preventDefault(); submit.mutate(event.currentTarget) }}>
      {!status.email_otp_verified && <Notice>Hoàn tất xác minh email ở bước 1 để nộp hồ sơ.</Notice>}
      <fieldset disabled={!status.email_otp_verified || submit.isPending} className="fl-verification-fields">
        <legend>Thông tin trên giấy phép kinh doanh</legend>
        <label>Tư cách đăng ký<select name="applicant_capacity" required><option value="LEGAL_REPRESENTATIVE">Người đại diện pháp luật</option><option value="AUTHORIZED_RECRUITER">Người được ủy quyền tuyển dụng</option></select></label>
        <div className="fl-form-grid">
          <label>Họ tên người đăng ký<input name="applicant_name" required minLength={2} maxLength={100} /></label>
          <label>Chức vụ<input name="applicant_position" required minLength={2} maxLength={100} /></label>
          <label>Số điện thoại liên hệ<input name="applicant_phone" required minLength={8} maxLength={20} type="tel" /></label>
        </div>
        <Notice>Nếu là người đại diện pháp luật: cung cấp bằng chứng để nhà trường đối chiếu danh tính với người đại diện trên đăng ký doanh nghiệp. Nếu được ủy quyền: giấy giới thiệu/ủy quyền cần ghi tên, email và phạm vi tuyển dụng. Nhà trường sẽ xác nhận qua đầu mối độc lập; giấy tờ hoặc email tên miền riêng không phải căn cứ duy nhất. Chỉ người nộp và admin có thẩm quyền được truy cập tài liệu.</Notice>
        <label className="fl-upload-area">Bằng chứng danh tính / quyền đại diện tuyển dụng<input name="authority_file" type="file" required accept=".pdf,.jpg,.jpeg,.png" /><span>Chọn tệp PDF, JPG hoặc PNG, tối đa 10 MB. Có thể được yêu cầu bổ sung hoặc xác nhận trực tiếp.</span></label>
        <div className="fl-form-grid">
          <label>Mã số thuế<input name="tax_code" required pattern="[0-9]{10}(-?[0-9]{3})?" maxLength={14} defaultValue={status.tax_code} placeholder="10 số hoặc mã chi nhánh 13 số" /></label>
          <label>Người đại diện pháp luật<input name="legal_representative" required maxLength={100} defaultValue={status.legal_representative} autoComplete="name" /></label>
          <label className="fl-wide">Tên doanh nghiệp<input name="company_name" required maxLength={255} defaultValue={status.company_name} autoComplete="organization" /></label>
          <label className="fl-wide">Địa chỉ trụ sở<input name="business_address" required maxLength={255} defaultValue={status.business_address} autoComplete="street-address" /></label>
        </div>
        <label className="fl-upload-area">Giấy phép kinh doanh
          <span>PDF, JPG hoặc PNG · Tối đa 10 MB · Chụp rõ toàn bộ nội dung</span>
          <input type="file" name="license_file" required accept=".pdf,.jpg,.jpeg,.png" onChange={event => {
            const selected = event.target.files?.[0] ?? null
            if (selected && (selected.size > 10 * 1024 * 1024 || !['application/pdf', 'image/jpeg', 'image/png'].includes(selected.type))) {
              toast.error('Chọn tệp PDF, JPG hoặc PNG không quá 10 MB.'); event.target.value = ''; setFile(null); return
            }
            setFile(selected)
          }} />
        </label>
        <DocumentPreview file={file} />
        {submit.isError && <Notice danger>{errorText(submit.error)}</Notice>}
        <div className="fl-actions"><button type="submit" className="fl-button" disabled={!file || submit.isPending}>{submit.isPending ? 'Đang gửi hồ sơ…' : 'Gửi hồ sơ để xét duyệt'}</button></div>
      </fieldset>
    </form>}
  </div>
}
