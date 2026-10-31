import type { Page } from '@/types/api'
export type Numeric = number | string
export interface MatchResult {
  id: number; student_id: number; job_id: number; cv_id: number | null
  passed_rules: boolean; score: Numeric; skill_score: Numeric | null
  experience_score: Numeric | null; semantic_score: Numeric | null
  matched_skills: string[]; missing_skills: string[]; explanation: string; computed_at: string
}
export interface JobRecommendation { job_id: number; title: string; company_id: number; match: MatchResult }
export interface CandidateRecommendation {
  student_id: number; full_name: string; major_id: number; gpa: Numeric | null
  contact_email: string | null; contact_phone: string | null
  achievements: { title: string; description: string | null }[]; match: MatchResult
}
export interface Job {
  id: number; title: string; position: string; location: string | null
  work_mode: 'ONSITE' | 'REMOTE' | 'HYBRID'; quantity: number
  salary_min: number | null; salary_max: number | null; is_salary_negotiable: boolean
  deadline: string; status: string; term_id: number | null
  company: { id: number; name: string; logo_url: string | null }
  job_type: { id: number; name: string; code: string }
}
export interface JobDetail extends Job {
  description: string; requirements: string | null; benefits: string | null
  min_gpa: number | null; min_experience_months: number | null
  skills: { skill_id: number; is_required: boolean; skill: { id: number; name: string } }[]
}
export interface CVChoice { id: number; title: string; is_default: boolean; type: 'ONLINE' | 'UPLOADED' }
export interface SavedJob { job: Job; saved_at: string }
export type { Page }
