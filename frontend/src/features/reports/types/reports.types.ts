export type ReportTargetType = 'JOB' | 'COMPANY' | 'STUDENT'
export type ReportStatus = 'PENDING' | 'RESOLVED' | 'REJECTED'

export interface ReportCreate {
  target_type: ReportTargetType
  target_id: number
  reason: string
}

export interface ReportHandle {
  status: ReportStatus
  resolution_note?: string | null
  lock_target_user?: boolean
  close_target_job?: boolean
}

export interface Report {
  id: number
  reporter_id: number
  target_type: ReportTargetType
  target_id: number
  reason: string
  status: ReportStatus
  handled_by?: number | null
  handled_at?: string | null
  resolution_note?: string | null
  created_at: string
}
