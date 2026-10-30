import { CircleAlert, Inbox, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/Button'

export function LoadingState({ label = 'Đang tải dữ liệu…' }: { label?: string }) {
  return <div className="state" role="status"><LoaderCircle className="spin" size={25} /><p>{label}</p></div>
}
export function EmptyState({ title = 'Chưa có dữ liệu', description, action }: { title?: string; description?: string; action?: ReactNode }) {
  return <div className="state"><span className="state__icon"><Inbox size={28} /></span><h3>{title}</h3>{description && <p>{description}</p>}{action}</div>
}
export function ErrorState({ title = 'Không tải được dữ liệu', message = 'Vui lòng thử lại sau.', onRetry }: { title?: string; message?: string; onRetry?: () => void }) {
  return <div className="state state--error" role="alert"><CircleAlert size={28} /><h3>{title}</h3><p>{message}</p>{onRetry && <Button variant="secondary" onClick={onRetry}>Thử lại</Button>}</div>
}
