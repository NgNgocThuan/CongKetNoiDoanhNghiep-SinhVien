import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/common/PageHeader'
import {
  ActionDialog,
  DataResult,
  FieldsForm,
  Notice,
  Panel,
  RecordTable,
} from '@/components/common/Workspace'
import { getData } from '@/components/common/workspace-api'
import type { Field, Row } from '@/components/common/Workspace'
import { Button } from '@/components/ui/Button'
import { LoadingState, ErrorState } from '@/components/common/States'
import { http } from '@/lib/http'
import { statusLabel } from '@/features/administration/status'
import type { Page } from '@/types/api'

function Editor({ data }: { data: Row }) {
  const client = useQueryClient()
  const industries = useQuery({
    queryKey: ['company-industries'],
    queryFn: () =>
      getData<Page<{ id: number; name: string }>>('/catalog/industries', {
        size: 100,
      }),
  })
  const fields: Field[] = [
    {
      name: 'industry_id',
      label: 'Lĩnh vực',
      type: 'select',
      options: industries.data?.items.map((i) => ({
        value: i.id,
        label: i.name,
      })),
    },
    {
      name: 'company_size',
      label: 'Quy mô',
      type: 'select',
      options: ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'].map(
        (value) => ({ value, label: value + ' nhân viên' }),
      ),
    },
    { name: 'address', label: 'Địa chỉ', maxLength: 500 },
    { name: 'website', label: 'Website', type: 'url', maxLength: 255 },
    { name: 'logo_url', label: 'URL logo', type: 'url', maxLength: 500 },
    { name: 'contact_name', label: 'Người liên hệ', maxLength: 255 },
    { name: 'contact_phone', label: 'Điện thoại', maxLength: 20 },
    { name: 'tech_stack', label: 'Công nghệ sử dụng', maxLength: 500 },
    { name: 'description', label: 'Giới thiệu doanh nghiệp', type: 'textarea' },
    { name: 'benefits', label: 'Phúc lợi', type: 'textarea' },
  ]
  const mutation = useMutation({
    mutationFn: (values: Row) =>
      http.put(
        '/companies/me',
        Object.fromEntries(
          fields.map((f) => [
            f.name,
            values[f.name] === '' ||
            values[f.name] === null ||
            values[f.name] === undefined
              ? null
              : f.name === 'industry_id'
                ? Number(values[f.name])
                : values[f.name],
          ]),
        ),
      ),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ['company-profile'] }),
  })
  if (industries.isPending) return <LoadingState />
  if (industries.isError)
    return (
      <ErrorState
        message={industries.error.message}
        onRetry={() => void industries.refetch()}
      />
    )
  return (
    <>
      <Notice error={industries.error} />
      <FieldsForm
        fields={fields}
        initial={Object.fromEntries(
          fields.map((f) => [f.name, data[f.name] ?? '']),
        )}
        submit={(v) => mutation.mutate(v)}
        pending={mutation.isPending}
        error={mutation.error}
      />
      <Notice success={mutation.isSuccess ? 'Đã lưu hồ sơ.' : undefined} />
    </>
  )
}
function Documents({ documents }: { documents: Row[] }) {
  const [file, setFile] = useState<File | null>(null),
    [type, setType] = useState('BUSINESS_LICENSE'),
    [remove, setRemove] = useState<Row | null>(null)
  const client = useQueryClient()
  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Chọn tệp giấy tờ.')
      const form = new FormData()
      form.append('doc_type', type)
      form.append('file', file)
      return http.post('/companies/me/documents', form)
    },
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ['company-profile'] }),
  })
  return (
    <Panel title="Giấy tờ xác thực">
      <form
        className="ws-filters"
        onSubmit={(e) => {
          e.preventDefault()
          upload.mutate()
        }}
      >
        <label>
          Loại giấy tờ
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {[
              ['BUSINESS_LICENSE', 'Đăng ký kinh doanh'],
              ['TAX_CERTIFICATE', 'Chứng nhận thuế'],
              ['AUTHORIZATION_LETTER', 'Giấy ủy quyền'],
              ['OTHER', 'Khác'],
            ].map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label>
          Tệp PDF/JPG/PNG
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            required
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>
        <Button type="submit" pending={upload.isPending}>
          Tải giấy tờ
        </Button>
      </form>
      <Notice
        error={upload.error}
        success={upload.isSuccess ? 'Đã tải giấy tờ.' : undefined}
      />
      <RecordTable
        rows={documents}
        columns={[
          { key: 'doc_type', label: 'Loại giấy tờ' },
          { key: 'uploaded_at', label: 'Ngày tải lên' },
          { key: 'file_url', label: 'Tham chiếu tệp' },
        ]}
        actions={(r) => (
          <Button size="sm" variant="danger" onClick={() => setRemove(r)}>
            Xóa
          </Button>
        )}
      />
      <p className="muted">
        Chưa có endpoint tải giấy tờ được bảo vệ nên giao diện chỉ hiển thị tham
        chiếu tệp đã lưu.
      </p>
      {remove && (
        <ActionDialog
          title="Xóa giấy tờ"
          path={'/companies/me/documents/' + remove.id}
          method="delete"
          invalidate={['company-profile']}
          onClose={() => setRemove(null)}
        />
      )}
    </Panel>
  )
}
export default function CompanyProfilePage() {
  const query = useQuery({
    queryKey: ['company-profile'],
    queryFn: () => getData<Row>('/companies/me'),
  })
  return (
    <div className="workspace">
      <PageHeader
        title="Hồ sơ doanh nghiệp"
        description="Giới thiệu môi trường làm việc và hoàn thiện thông tin xác thực."
      />
      <DataResult query={query}>
        {(data) => (
          <>
            <Panel title={String(data.name)}>
              <p>
                Mã số thuế: {String(data.tax_code)} ·{' '}
                {statusLabel(data.verification_status)}
              </p>
              {Boolean(data.reject_reason) && (
                <p className="ws-error">{String(data.reject_reason)}</p>
              )}
              <p className="muted">
                Tên doanh nghiệp và mã số thuế được giữ theo hồ sơ đăng ký.
              </p>
              <Editor data={data} />
            </Panel>
            <Documents documents={(data.documents || []) as Row[]} />
          </>
        )}
      </DataResult>
    </div>
  )
}
