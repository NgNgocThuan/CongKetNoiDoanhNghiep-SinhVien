import { statusLabels } from '../format'
import type { ReactNode } from 'react'
import { LoadingState, ErrorState } from '@/components/common/States'
import '../student.css'
export function StudentPage({
  title,
  description,
  actions,
  children,
}: {
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="student-area">
      <header className="student-heading">
        <div>
          <p className="eyebrow">HÀNH TRÌNH NGHỀ NGHIỆP</p>
          <h1>{title}</h1>
          <p className="muted">{description}</p>
        </div>
        <div className="student-actions">{actions}</div>
      </header>
      {children}
    </section>
  )
}
export function QueryState({
  query,
}: {
  query: { isPending: boolean; error: Error | null; refetch: () => unknown }
}) {
  return query.isPending ? (
    <LoadingState />
  ) : query.error ? (
    <ErrorState
      message={query.error.message}
      onRetry={() => {
        void query.refetch()
      }}
    />
  ) : null
}
export function Feedback({ error, success }: { error?: string; success?: string }) {
  return (
    <>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {success && (
        <p role="status" className="student-notice">
          {success}
        </p>
      )}
    </>
  )
}
export function Status({ value }: { value: string }) {
  return (
    <span className={'student-tag status-' + value.toLowerCase()}>
      {statusLabels[value] || value}
    </span>
  )
}
