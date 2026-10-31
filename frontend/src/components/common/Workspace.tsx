import type { ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { http } from '@/lib/http'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { LoadingState, ErrorState, EmptyState } from './States'
import type { Page } from '@/types/api'
import { getData, textValue } from './workspace-api'
import { formSchema } from './workspace-form'
import { ApiError } from '@/lib/api-error'
import './workspace.css'

export type Row = Record<string, unknown>
export type Field = {
  name: string
  label: string
  type?:
    | 'text'
    | 'email'
    | 'password'
    | 'number'
    | 'date'
    | 'url'
    | 'textarea'
    | 'checkbox'
    | 'select'
  required?: boolean
  minLength?: number
  maxLength?: number
  min?: number
  max?: number
  step?: string
  options?: { value: string | number; label: string }[]
}
export function Notice({
  error,
  success,
}: {
  error?: Error | null
  success?: string
}) {
  return (
    <>
      {error && (
        <p className="ws-error" role="alert">
          {error.message}
        </p>
      )}
      {success && (
        <p className="ws-success" role="status">
          {success}
        </p>
      )}
    </>
  )
}
export function Panel({
  title,
  children,
  actions,
}: {
  title: string
  children: ReactNode
  actions?: ReactNode
}) {
  return (
    <section className="ws-panel">
      <div className="ws-panel-heading">
        <h2>{title}</h2>
        {actions}
      </div>
      {children}
    </section>
  )
}
export function DataResult<T>({
  query,
  children,
}: {
  query: {
    isPending: boolean
    isError: boolean
    error: Error | null
    data?: T
    refetch: () => unknown
  }
  children: (data: T) => ReactNode
}) {
  return query.isPending ? (
    <LoadingState />
  ) : query.isError ? (
    <ErrorState
      message={query.error?.message}
      onRetry={() => {
        query.refetch()
      }}
    />
  ) : query.data !== undefined ? (
    children(query.data)
  ) : (
    <EmptyState title="Chưa có dữ liệu" />
  )
}
export function RecordTable<T extends object>({
  rows,
  columns,
  actions,
}: {
  rows: T[]
  columns: {
    key: string
    label: string
    render?: (row: NoInfer<T>) => ReactNode
  }[]
  actions?: (row: NoInfer<T>) => ReactNode
}) {
  return !rows.length ? (
    <EmptyState title="Chưa có dữ liệu" />
  ) : (
    <div className="ws-table">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
            {actions && <th>Thao tác</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={String((row as Row).id ?? index)}>
              {columns.map((c) => (
                <td key={c.key}>
                  {c.render ? c.render(row) : textValue((row as Row)[c.key])}
                </td>
              ))}
              {actions && (
                <td>
                  <div className="ws-actions">{actions(row)}</div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
export function FieldsForm({
  fields,
  initial = {},
  submit,
  pending,
  label = 'Lưu thay đổi',
  error,
}: {
  fields: Field[]
  initial?: Row
  submit: (values: Row) => void
  pending?: boolean
  label?: string
  error?: Error | null
}) {
  const defaults = Object.fromEntries(
    fields.map((field) => [
      field.name,
      initial[field.name] ?? (field.type === 'checkbox' ? false : ''),
    ]),
  )
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Row>({
    defaultValues: defaults,
    resolver: zodResolver(formSchema(fields)),
  })
  return (
    <form
      className="ws-form"
      onSubmit={handleSubmit((values) => {
        if (!pending) submit(values)
      })}
    >
      <fieldset disabled={pending} className="ws-form-fields">
        {fields.map((field) => (
          <label
            key={field.name}
            className={field.type === 'textarea' ? 'ws-wide' : ''}
          >
            {field.label}
            {field.required && ' *'}
            {field.type === 'textarea' ? (
              <textarea
                rows={4}
                maxLength={field.maxLength}
                {...register(field.name)}
              />
            ) : field.type === 'select' ? (
              <select {...register(field.name)}>
                <option value="">Chọn…</option>
                {field.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type || 'text'}
                step={field.step}
                min={field.min}
                max={field.max}
                minLength={field.minLength}
                maxLength={field.maxLength}
                {...register(field.name)}
              />
            )}
            {(errors[field.name] ||
              (error instanceof ApiError && error.fields[field.name])) && (
              <span className="ws-error" role="alert">
                {String(
                  errors[field.name]?.message ||
                    (error as ApiError).fields[field.name],
                )}
              </span>
            )}
          </label>
        ))}
      </fieldset>
      <div className="ws-wide">
        <Notice error={error} />
        <Button type="submit" pending={pending}>
          {label}
        </Button>
      </div>
    </form>
  )
}
export function ActionDialog({
  title,
  path,
  fields = [],
  initial,
  method = 'post',
  onClose,
  onSuccess,
  invalidate,
  transform,
}: {
  title: string
  path: string
  fields?: Field[]
  initial?: Row
  method?: 'post' | 'put' | 'delete'
  onClose: () => void
  onSuccess?: () => void
  invalidate: readonly unknown[]
  transform?: (values: Row) => Row
}) {
  const client = useQueryClient()
  const mutation = useMutation({
    mutationFn: (values: Row) =>
      http.request({
        method,
        url: path,
        data: transform ? transform(values) : values,
      }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: invalidate })
      onSuccess?.()
      onClose()
    },
  })
  return (
    <Dialog
      open
      title={title}
      onOpenChange={(open) => {
        if (!open && !mutation.isPending) onClose()
      }}
    >
      <p className="muted">Xác nhận thao tác với bản ghi này.</p>
      <FieldsForm
        fields={fields}
        initial={initial}
        submit={(values) => mutation.mutate(values)}
        pending={mutation.isPending}
        error={mutation.error}
        label="Xác nhận"
      />
    </Dialog>
  )
}
export function CatalogSelect({
  name,
  label,
  resource,
  value,
  onChange,
}: {
  name: string
  label: string
  resource: string
  value: string
  onChange: (value: string) => void
}) {
  const [search, setSearch] = useState('')
  const query = useQuery({
    queryKey: ['workspace-catalog', resource, search],
    queryFn: () =>
      getData<Page<{ id: number; name: string }>>('/catalog/' + resource, {
        size: 100,
        q: search || undefined,
      }),
  })
  return (
    <label>
      {label}
      <input
        aria-label={'Tìm ' + label.toLowerCase()}
        placeholder="Tìm trong danh mục…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <select
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Tất cả / chưa chọn</option>
        {query.data?.items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </select>
      {query.isError && <Notice error={query.error} />}
    </label>
  )
}
