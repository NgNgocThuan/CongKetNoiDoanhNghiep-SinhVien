const labels: Record<string, string> = {
  ADMIN: 'Quản trị viên',
  STUDENT: 'Sinh viên',
  COMPANY: 'Doanh nghiệp',
  JOB: 'Tin tuyển dụng',
  ACTIVE: 'Hoạt động',
  LOCKED: 'Đã khóa',
  PENDING_ACTIVATION: 'Chờ kích hoạt',
  PENDING_APPROVAL: 'Chờ duyệt',
  PENDING: 'Đang chờ',
  APPROVED: 'Đã duyệt',
  REJECTED: 'Đã từ chối',
  RESOLVED: 'Đã xử lý',
  DRAFT: 'Bản nháp',
  CLOSED: 'Đã đóng',
  EXPIRED: 'Hết hạn',
  SENT: 'Đã gửi',
  FAILED: 'Thất bại',
  APPLIED: 'Đã nộp',
  SCREENING: 'Sơ loại',
  SHORTLISTED: 'Danh sách ngắn',
  INTERVIEW: 'Phỏng vấn',
  OFFER: 'Đề nghị tuyển',
  HIRED: 'Đã tuyển',
  WITHDRAWN: 'Đã rút',
  ACCEPTED: 'Đã ứng tuyển',
  DECLINED: 'Đã từ chối',
  ONGOING: 'Đang diễn ra',
  OPEN: 'Đang mở',
  PASSED: 'Đạt',
}
export function statusLabel(value: unknown): string {
  return value === null || value === undefined || value === ''
    ? '—'
    : labels[String(value)] || String(value)
}
