/** Quy tắc hiển thị/thao tác cho đợt thực tập (backend vẫn là nơi quyết định cuối cùng). */
import type { InternshipResult, ResultStatus, TermStatus } from './types'

export const TERM_STEPS: TermStatus[] = ['DRAFT', 'OPEN', 'ONGOING', 'CLOSED']

export const TERM_STATUS_LABEL: Record<TermStatus, string> = {
  DRAFT: 'Bản nháp',
  OPEN: 'Đang mở đăng ký',
  ONGOING: 'Đang diễn ra',
  CLOSED: 'Đã kết thúc',
}

export const RESULT_LABEL: Record<ResultStatus, string> = {
  PENDING: 'Chờ kết quả',
  PASSED: 'Đạt',
  FAILED: 'Không đạt',
}

/** Chỉ được chuyển tiến đúng một bước: DRAFT→OPEN→ONGOING→CLOSED. Đợt đã đóng thì không còn bước tiếp. */
export function nextStatus(status: TermStatus): TermStatus | null {
  const index = TERM_STEPS.indexOf(status)
  return index >= 0 && index < TERM_STEPS.length - 1 ? TERM_STEPS[index + 1] : null
}

/** Đợt đã đóng thì không sửa thông tin và không đổi danh sách sinh viên/phân công. */
export function isTermEditable(status: TermStatus): boolean {
  return status !== 'CLOSED'
}

/** Sau khi nhà trường xác nhận PASSED/FAILED thì khóa nhận xét, điểm và xác nhận lại. */
export function isResultLocked(result: Pick<InternshipResult, 'result'>): boolean {
  return result.result !== 'PENDING'
}

/** Nhận xét nhà trường cần ít nhất nhận xét hoặc điểm (khớp validate của backend). */
export function hasReviewContent(comment?: string | null, score?: number | null): boolean {
  return Boolean(comment && comment.trim()) || (score !== null && score !== undefined)
}
