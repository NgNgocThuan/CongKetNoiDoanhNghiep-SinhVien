import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Award, Download, FileSignature, FileText } from 'lucide-react'
import { http } from '@/lib/http'
import { toast } from '@/lib/toast'
import { Badge, LoadingError, Notice } from './ui'
import { errorText } from './messages'
import { DocumentPreview } from './DocumentPreview'

interface MouStatus {
  is_mou_partner: boolean
  hybrid_available: boolean
  status: string
  agreement_code?: string
  effective_until?: string
  review_note?: string
}

export function MouPartnerFlow() {
  const client = useQueryClient()
  const [method, setMethod] = useState<'paper' | 'hybrid'>('paper')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Blob | null>(null)
  const query = useQuery<MouStatus>({
    queryKey: ['freelancer', 'company-mou-status'],
    queryFn: async () => (await http.get('/company/mou/status')).data,
    refetchInterval: 12000,
  })
  const download = useMutation({
    mutationFn: async () => {
      const response = await http.get('/company/mou/template/' + (method === 'paper' ? 'paper' : 'hybrid-signed'), { responseType: 'blob' })
      const blob = new Blob([response.data], { type: 'application/pdf' })
      setPreview(blob)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url; link.download = `MOU-${method}.pdf`; link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    },
    onError: (error: unknown) => toast.error(errorText(error)),
  })
  const submit = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      if (!file) throw new Error('Vui lòng chọn tài liệu đã ký.')
      const body = new FormData(form)
      body.set(method === 'paper' ? 'mou_file' : 'signed_pdf', file)
      return http.post('/company/mou/' + (method === 'paper' ? 'submit-paper-scan' : 'upload-hybrid-signed'), body)
    },
    onSuccess: async () => { toast.success('Đã tiếp nhận thỏa thuận MOU.'); setFile(null); await client.invalidateQueries({ queryKey: ['freelancer'] }) },
    onError: (error: unknown) => toast.error(errorText(error)),
  })
  const data = query.data
  const pending = data?.status === 'PENDING_REVIEW'
  const busy = submit.isPending || download.isPending
  return <div className="fl-verification">
    <LoadingError query={query} />
    {data && <>
      <div className="fl-partner-banner"><Award size={32} /><div><h3>{data.is_mou_partner ? 'Đối tác MOU của Nhà trường' : 'Nâng cấp Đối tác MOU'}</h3><p>Hợp tác tuyển dụng và mở quyền cấp vốn Freelancer theo từng mốc.</p></div></div>
      {data.review_note && <Notice>{data.review_note}</Notice>}
      {data.is_mou_partner || pending ? <div className="fl-verification-summary">
        <Badge value={data.status} /><p>Mã thỏa thuận: {data.agreement_code}</p>
        {data.is_mou_partner && data.effective_until && <p>Hiệu lực đến {new Date(data.effective_until).toLocaleDateString('vi-VN')}</p>}
        {pending && <p>Nhà trường đang thẩm định tài liệu. Bạn sẽ nhận thông báo khi có kết quả.</p>}
      </div> : <>
        <fieldset className="fl-mou-methods" disabled={busy}>
          <legend>Chọn cách ký thỏa thuận</legend>
          <label className={method === 'paper' ? 'selected' : ''}><input type="radio" name="mou-method" checked={method === 'paper'} onChange={() => { setMethod('paper'); setFile(null); setPreview(null); submit.reset() }} /><FileText size={22} /><span><strong>Ký giấy và đóng dấu</strong><small>In mẫu, ký, scan và gửi Nhà trường duyệt.</small></span></label>
          <label className={method === 'hybrid' ? 'selected' : ''}><input type="radio" name="mou-method" checked={method === 'hybrid'} disabled={!data.hybrid_available} onChange={() => { setMethod('hybrid'); setFile(null); setPreview(null); submit.reset() }} /><FileSignature size={22} /><span><strong>Ký số điện tử</strong><small>{data.hybrid_available ? 'Ký PDF bằng chứng thư số doanh nghiệp.' : 'Chờ Nhà trường cấu hình chứng thư ký số.'}</small></span></label>
        </fieldset>
        <ol className="fl-mou-instructions"><li>Tải mẫu thỏa thuận bên dưới.</li><li>{method === 'paper' ? 'In và ký tên, đóng dấu; scan rõ tất cả các trang.' : 'Mở PDF bằng Adobe Acrobat hoặc Foxit và thêm chữ ký số doanh nghiệp; giữ nguyên nội dung.'}</li><li>Tải bản đã ký lên để kiểm tra và xét duyệt.</li></ol>
        <button type="button" className="fl-button secondary" disabled={busy} onClick={() => download.mutate()}><Download size={16} />{download.isPending ? 'Đang chuẩn bị…' : 'Tải mẫu MOU'}</button>
        {download.isError && <Notice danger>{errorText(download.error)}</Notice>}
        <DocumentPreview file={preview} />
        <form key={method} onSubmit={event => { event.preventDefault(); submit.mutate(event.currentTarget) }}>
          <fieldset className="fl-verification-fields" disabled={busy}>
            <legend>Đính kèm biên bản MOU đã ký</legend>
            {method === 'paper' && <div className="fl-form-grid"><label>Họ tên người ký<input name="signer_name" required maxLength={255} autoComplete="name" /></label><label>Chức vụ<input name="signer_position" required maxLength={255} placeholder="Ví dụ: Giám đốc" /></label></div>}
            <label className="fl-upload-area">Tài liệu đã ký<span>{method === 'paper' ? 'PDF, JPG hoặc PNG' : 'PDF có chữ ký số của hai bên'} · Tối đa 15 MB</span><input type="file" required accept={method === 'paper' ? '.pdf,.jpg,.jpeg,.png' : '.pdf'} onChange={event => {
              const next = event.target.files?.[0] ?? null
              const types = method === 'paper' ? ['application/pdf', 'image/jpeg', 'image/png'] : ['application/pdf']
              if (next && (next.size > 15 * 1024 * 1024 || !types.includes(next.type))) { toast.error('Tệp không đúng định dạng hoặc vượt quá 15 MB.'); event.target.value = ''; setFile(null); return }
              setFile(next)
            }} /></label>
            <DocumentPreview file={file} />
            {submit.isError && <Notice danger>{errorText(submit.error)}</Notice>}
            <button className="fl-button" type="submit" disabled={!file || busy}>{submit.isPending ? 'Đang kiểm tra tài liệu…' : 'Gửi thỏa thuận MOU'}</button>
          </fieldset>
        </form>
      </>}
    </>}
  </div>
}
