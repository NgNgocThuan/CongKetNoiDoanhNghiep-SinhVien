import { Badge } from '@/components/ui/StatusTag'
import { RESULT_LABEL, TERM_STATUS_LABEL } from './rules'
import type { JobStatus, ResultStatus, TermStatus } from './types'

export function TermStatusBadge({ status }: { status: TermStatus }) {
  const tone = status === 'OPEN' ? 'info' : status === 'ONGOING' ? 'success' : status === 'DRAFT' ? 'pending' : 'neutral'
  return <Badge tone={tone}>{TERM_STATUS_LABEL[status]}</Badge>
}

export function ResultBadge({ result }: { result: ResultStatus }) {
  const tone = result === 'PASSED' ? 'success' : result === 'FAILED' ? 'error' : 'pending'
  return <Badge tone={tone}>{RESULT_LABEL[result]}</Badge>
}

const JOB_STATUS: Record<JobStatus, { label: string; tone: 'success' | 'pending' | 'error' | 'neutral' }> = {
  DRAFT: { label: 'Nháp', tone: 'neutral' },
  PENDING_APPROVAL: { label: 'Chờ duyệt', tone: 'pending' },
  APPROVED: { label: 'Đã duyệt', tone: 'success' },
  REJECTED: { label: 'Bị từ chối', tone: 'error' },
  CLOSED: { label: 'Đã đóng', tone: 'neutral' },
  EXPIRED: { label: 'Hết hạn', tone: 'neutral' },
}

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const { label, tone } = JOB_STATUS[status]
  return <Badge tone={tone}>{label}</Badge>
}
