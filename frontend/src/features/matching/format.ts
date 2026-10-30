import type { Job, Numeric } from './types'
export function positiveId(value: string | null): number | null {
  if (!value || !/^\d+$/.test(value)) return null
  const number = Number(value)
  return Number.isSafeInteger(number) && number > 0 ? number : null
}
export function scoreValue(value: Numeric | null): number | null {
  if (value === null || value === '' || !Number.isFinite(Number(value))) return null
  return Math.min(100, Math.max(0, Number(value)))
}
export function scoreLabel(value: Numeric | null): string {
  const score = scoreValue(value)
  return score === null ? '—' : score.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) + '%'
}
// Backend stores and returns naive UTC datetimes; respect explicit offsets too.
export function computedAtLabel(value: string): string {
  const date = new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : value + 'Z')
  return Number.isNaN(date.getTime()) ? 'Chưa có thông tin' : date.toLocaleString('vi-VN')
}
export function salaryLabel(job: Pick<Job, 'salary_min' | 'salary_max' | 'is_salary_negotiable'>): string {
  const money = (value: number) => value.toLocaleString('vi-VN') + ' đ'
  if (job.is_salary_negotiable) return 'Lương thỏa thuận'
  if (job.salary_min !== null && job.salary_max !== null) return money(job.salary_min) + ' – ' + money(job.salary_max)
  if (job.salary_min !== null) return 'Từ ' + money(job.salary_min)
  if (job.salary_max !== null) return 'Đến ' + money(job.salary_max)
  return 'Chưa cung cấp mức lương'
}
export const workModes: Record<Job['work_mode'], string> = { ONSITE: 'Tại văn phòng', REMOTE: 'Từ xa', HYBRID: 'Kết hợp' }
export const jobStatuses: Record<string, string> = { DRAFT: 'Bản nháp', PENDING: 'Chờ duyệt', PENDING_APPROVAL: 'Chờ duyệt', APPROVED: 'Đã duyệt', REJECTED: 'Bị từ chối', CLOSED: 'Đã đóng', EXPIRED: 'Hết hạn' }
