import type { Job } from './types'
export const dateText = (s?: string | null) =>
  s
    ? new Intl.DateTimeFormat('vi-VN').format(
        new Date(
          s.length === 10 ? s + 'T00:00:00' : s.endsWith('Z') ? s : s + 'Z',
        ),
      )
    : 'Chưa cập nhật'
export const statusLabels: Record<string, string> = {
  APPLIED: 'Đã ứng tuyển',
  SCREENING: 'Sàng lọc',
  SHORTLISTED: 'Danh sách ngắn',
  INTERVIEW: 'Phỏng vấn',
  OFFER: 'Đề nghị tuyển dụng',
  HIRED: 'Đã tuyển',
  REJECTED: 'Bị từ chối',
  WITHDRAWN: 'Đã rút',
  PENDING: 'Chờ phản hồi',
  ACCEPTED: 'Đã ứng tuyển',
  DECLINED: 'Đã từ chối',
  EXPIRED: 'Hết hạn',
  DRAFT: 'Nháp',
  OPEN: 'Đang mở',
  ONGOING: 'Đang diễn ra',
  CLOSED: 'Đã đóng',
}
export function salaryText(
  job: Pick<Job, 'is_salary_negotiable' | 'salary_min' | 'salary_max'>,
) {
  if (job.is_salary_negotiable) return 'Lương thỏa thuận'
  const money = (n: number) => new Intl.NumberFormat('vi-VN').format(n) + 'đ'
  if (job.salary_min != null && job.salary_max != null)
    return money(job.salary_min) + ' – ' + money(job.salary_max)
  return job.salary_min != null
    ? 'Từ ' + money(job.salary_min)
    : job.salary_max != null
      ? 'Đến ' + money(job.salary_max)
      : 'Chưa công bố'
}
