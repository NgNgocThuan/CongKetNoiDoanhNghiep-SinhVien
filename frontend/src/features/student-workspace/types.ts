import type { Job } from '@/features/matching/types'
export interface StudentApplication {
  id: number
  current_status: string
  applied_at: string
  job: Job
  cover_letter?: string
  status_logs?: {
    id: number
    new_status: string
    note: string | null
    changed_at: string
  }[]
}
export interface CV {
  id: number
  title: string
  type: 'ONLINE' | 'UPLOADED'
  is_default: boolean
  content_json: Record<string, unknown> | null
  parsed_json: Record<string, unknown> | null
  parsed_at: string | null
}
export interface Internship {
  id: number
  term: {
    id: number
    name: string
    semester: string
    academic_year: string
    start_date: string
    end_date: string
    status: string
  }
  lecturer: {
    full_name: string
    email: string | null
    phone: string | null
  } | null
}
