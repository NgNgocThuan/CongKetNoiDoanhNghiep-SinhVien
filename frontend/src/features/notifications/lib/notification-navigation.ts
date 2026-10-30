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

  // 1. Tin tuyển dụng (Job) - Kiểm tra trước để tránh nhầm JOB_APPROVED với APPLICATION
  if (refType.startsWith('JOB') || refType.includes('_JOB') || refType === 'JOB') {
    if (role === 'STUDENT') return refId ? `/student/jobs/${refId}` : '/student/jobs'
    if (role === 'COMPANY') return refId ? `/company/jobs/${refId}` : '/company/jobs'
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

  // 5. Đợt thực tập (Term / Internship)
  if (refType.includes('TERM') || refType.includes('INTERNSHIP')) {
    if (role === 'STUDENT') return '/student/internships'
    if (role === 'ADMIN') return '/admin/internships'
  }

  // Mặc định về trang thông báo của role
  return `${roleHome[role]}/notifications`
}
