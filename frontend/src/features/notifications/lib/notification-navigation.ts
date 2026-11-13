import type { Role } from '@/features/auth/types/auth.types'
import { roleHome } from '@/features/auth/types/auth.types'
import type { Notification } from '../api/notifications.api'

export function getNotificationTargetUrl(
  notification: Pick<Notification, 'ref_type' | 'ref_id'> & { type?: string },
  role?: Role | null
): string {
  if (!role) return '/login'

  const refType = (notification.ref_type || notification.type || '').toUpperCase()
  const refId = notification.ref_id
  if (refType === 'PAYOUT_BALANCE' && role === 'ADMIN') {
    return '/admin/freelancer/admin/transfers'
  }

  if (refType.includes('FREELANCE_PROJECT')) {
    if (role === 'ADMIN') return refId ? `/admin/freelancer/projects/${refId}` : '/admin/freelancer/admin/projects'
    return refId ? `${roleHome[role]}/freelancer/projects/${refId}` : `${roleHome[role]}/freelancer/projects`
  }
  if (refType.includes('FREELANCE_CONTRACT')) {
    return refId ? `${roleHome[role]}/freelancer/contracts/${refId}` : `${roleHome[role]}/freelancer/work`
  }
  if (refType.includes('FREELANCE_MILESTONE')) {
    return refId ? `${roleHome[role]}/freelancer/milestones/${refId}` : `${roleHome[role]}/freelancer/work`
  }
  if (refType.includes('FREELANCE_SETTLEMENT')) {
    return refId ? `${roleHome[role]}/freelancer/settlements/${refId}` : `${roleHome[role]}/freelancer/finance`
  }
  if (refType.includes('FREELANCE_DISPUTE')) {
    return refId ? `${roleHome[role]}/freelancer/disputes/${refId}` : `${roleHome[role]}/freelancer/work`
  }
  if (refType.includes('FREELANCE_APPLICATION')) {
    return `${roleHome[role]}/freelancer/work`
  }

  if (refType === 'BANK_DESTINATION') {
    return role === 'ADMIN'
      ? '/admin/freelancer/admin/banks'
      : `${roleHome[role]}/freelancer/banks`
  }
  if (refType === 'BUSINESS_VERIFICATION' || refType === 'MOU_AGREEMENT') {
    return role === 'ADMIN'
      ? '/admin/freelancer/admin/business'
      : `${roleHome[role]}/freelancer/onboarding`
  }

  // 1. Tin tuyển dụng (Job) - Kiểm tra trước để tránh nhầm JOB_APPROVED với APPLICATION
  if (refType.startsWith('JOB') || refType.includes('_JOB') || refType === 'JOB') {
    if (role === 'STUDENT') return refId ? `/student/jobs/${refId}` : '/student/jobs'
    if (role === 'COMPANY') return refId ? `/company/jobs/${refId}/stats` : '/company/jobs'
    if (role === 'ADMIN') return '/admin/jobs'
  }

  // 2. Đơn ứng tuyển (Application) - Tránh match nhầm APPROVED
  if (refType === 'APP' || refType.startsWith('APP_') || refType.includes('APPLICATION')) {
    if (role === 'STUDENT') return '/student/applications'
    if (role === 'COMPANY') return '/company/applications'
    if (role === 'ADMIN') return '/admin/students'
  }

  // 3. Doanh nghiệp & Hồ sơ đối tác (Company / Enterprise / MOU)
  if (refType.includes('COMPANY') || refType.includes('ENT') || refType.includes('MOU')) {
    if (role === 'ADMIN') return '/admin/companies'
    if (role === 'COMPANY') return '/company/profile'
    if (role === 'STUDENT') return refId ? `/student/companies/${refId}` : '/student'
  }

  // 4. Lời mời phỏng vấn & Lời mời ứng tuyển (Invitation / Interview)
  if (refType.includes('INVIT') || refType.includes('INTERVIEW')) {
    if (role === 'STUDENT') return '/student/invitations'
    if (role === 'COMPANY') return '/company/invitations'
  }

  // Mặc định về trang thông báo của role
  return `${roleHome[role]}/notifications`
}
