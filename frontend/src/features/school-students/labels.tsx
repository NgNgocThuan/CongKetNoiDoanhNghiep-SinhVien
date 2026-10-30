import { Badge } from '@/features/school-shared/components/StatusTag'
import type { AccountStatus } from './types'

export function AccountStatusBadge({ status }: { status: AccountStatus }) {
  switch (status) {
    case 'ACTIVE':
      return <Badge tone="success">Đã kích hoạt</Badge>
    case 'PENDING_ACTIVATION':
      return <Badge tone="pending">Chờ kích hoạt</Badge>
    case 'PENDING_APPROVAL':
      return <Badge tone="pending">Chờ duyệt</Badge>
    case 'LOCKED':
      return <Badge tone="error">Bị khóa</Badge>
  }
}
