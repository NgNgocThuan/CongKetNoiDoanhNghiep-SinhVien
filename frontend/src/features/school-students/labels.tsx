import { Badge } from '@/components/ui/StatusTag'
import type { AccountStatus, AchievementType, SkillLevel } from './types'

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

export const ACCOUNT_STATUS_OPTIONS: { value: AccountStatus; label: string }[] = [
  { value: 'ACTIVE', label: 'Đã kích hoạt' },
  { value: 'PENDING_ACTIVATION', label: 'Chờ kích hoạt' },
  { value: 'LOCKED', label: 'Bị khóa' },
]

export const ACHIEVEMENT_TYPE_LABEL: Record<AchievementType, string> = {
  RESEARCH: 'Nghiên cứu khoa học',
  ACHIEVEMENT: 'Thành tích',
  OTHER: 'Khác',
}

export const SKILL_LEVEL_LABEL: Record<SkillLevel, string> = {
  BEGINNER: 'Cơ bản',
  INTERMEDIATE: 'Trung bình',
  ADVANCED: 'Khá',
  EXPERT: 'Thành thạo',
}
