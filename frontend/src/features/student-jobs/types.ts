export interface Brief {
  id: number
  name: string
  logo_url?: string | null
}
export interface Job {
  id: number
  title: string
  position: string
  term_id: number | null
  location: string | null
  work_mode: string
  quantity: number
  salary_min: number | null
  salary_max: number | null
  is_salary_negotiable: boolean
  deadline: string
  status: string
  created_at: string
  company: Brief
  job_type: Brief
  description?: string
  requirements?: string | null
  benefits?: string | null
  min_gpa?: number | null
  min_experience_months?: number | null
  skills?: { skill_id: number; is_required: boolean; skill: Brief }[]
  majors?: { major_id: number; major: Brief }[]
}
export interface SavedJob {
  saved_at: string
  job: Job
}
export interface PublicCompany extends Brief {
  industry_id?: number | null
  company_size?: string | null
  address?: string | null
  website?: string | null
  description?: string | null
  tech_stack?: string | null
  benefits?: string | null
}
export type JobFilters = Record<string, string | number | string[] | undefined>
