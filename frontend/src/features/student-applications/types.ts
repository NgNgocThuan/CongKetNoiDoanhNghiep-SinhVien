export type ApplicationStatus =
  | 'APPLIED'
  | 'SCREENING'
  | 'SHORTLISTED'
  | 'INTERVIEW'
  | 'OFFER'
  | 'HIRED'
  | 'REJECTED'
  | 'WITHDRAWN'
export interface Application {
  id: number
  job_id: number
  cv_id: number
  current_status: ApplicationStatus
  applied_at: string
  job: {
    id: number
    title: string
    position: string
    company: { id: number; name: string }
  }
}
export interface ApplicationDetail extends Application {
  cover_letter: string | null
  cv: { id: number; title: string }
  status_logs: {
    id: number
    old_status: string | null
    new_status: string
    note: string | null
    changed_at: string
  }[]
}
export const canWithdraw = (status: ApplicationStatus) =>
  ['APPLIED', 'SCREENING', 'SHORTLISTED', 'INTERVIEW'].includes(status)
