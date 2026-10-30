import type { ImportBatchDetail } from '@/features/school-students/types'

export type TermStatus = 'DRAFT' | 'OPEN' | 'ONGOING' | 'CLOSED'
export type ResultStatus = 'PENDING' | 'PASSED' | 'FAILED'
export type JobStatus = 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'CLOSED' | 'EXPIRED'

export interface Term {
  id: number
  name: string
  semester: string
  academic_year: string
  start_date: string
  end_date: string
  status: TermStatus
  created_by: number
  created_at: string
  student_count: number
}

export interface TermForm {
  name: string
  semester: string
  academic_year: string
  start_date: string
  end_date: string
}

export interface TermListParams {
  page?: number
  size?: number
  academic_year?: string
  semester?: string
  status?: TermStatus
}

export interface TermStudent {
  term_student_id: number
  student_id: number
  student_code: string
  full_name: string
  class_name: string | null
  lecturer_id: number | null
  lecturer_name: string | null
}

export interface TermStudentAddResult {
  added: number
  already_in_term: number
  not_found_ids: number[]
}

export interface TermImportResult {
  batch: ImportBatchDetail
  added: number
}

export interface AssignLecturersResult {
  updated: number
  not_in_term_ids: number[]
}

export interface TermJob {
  id: number
  title: string
  position: string
  company_id: number
  company_name: string
  quantity: number
  deadline: string
  status: JobStatus
}

/**
 * Kết quả thực tập của một sinh viên trong đợt. Điểm là số thập phân backend trả dạng chuỗi; null = chưa có.
 * Khôi (form đánh giá của doanh nghiệp) dùng `id` làm result_id.
 */
export interface InternshipResult {
  id: number
  term_id: number
  term_student_id: number
  student_id: number
  student_code: string
  student_name: string
  lecturer_id: number | null
  lecturer_name: string | null
  company_id: number | null
  company_name: string | null
  application_id: number | null
  company_evaluation: string | null
  company_score: string | null
  evaluated_at: string | null
  lecturer_comment: string | null
  lecturer_score: string | null
  result: ResultStatus
  confirmed_by: number | null
  confirmed_at: string | null
}

export interface ResultListParams {
  page?: number
  size?: number
  result?: ResultStatus
  lecturer_id?: number
}
