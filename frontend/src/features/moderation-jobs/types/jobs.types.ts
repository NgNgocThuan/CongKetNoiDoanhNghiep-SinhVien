export type JobStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'CLOSED'

export type WorkMode = 'ONSITE' | 'HYBRID' | 'REMOTE'

export interface AdminJobRead {
  id: number
  company_id: number
  term_id?: number | null
  title: string
  position: string
  job_type_id: number
  industry_id?: number | null
  quantity: number
  salary_min?: number | null
  salary_max?: number | null
  is_salary_negotiable: boolean
  location?: string | null
  work_mode: WorkMode
  min_gpa?: number | null
  min_experience_months?: number | null
  deadline: string
  status: JobStatus
  approved_by?: number | null
  approved_at?: string | null
  reject_reason?: string | null
  view_count: number
  created_at: string
  updated_at: string
}

export interface AdminJobDetailRead extends AdminJobRead {
  description: string
  requirements?: string | null
  benefits?: string | null
  parsed_json?: Record<string, unknown> | null
  parsed_at?: string | null
}

export interface JobRejectRequest {
  reject_reason: string
}

export interface JobCloseRequest {
  reason?: string | null
}
