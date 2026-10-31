export type EmailStatus = 'PENDING' | 'SENT' | 'FAILED'

export interface EmailLogRead {
  id: number
  user_id?: number | null
  recipient_email: string
  type: string
  subject: string
  status: EmailStatus
  error_message?: string | null
  retry_count: number
  ref_type?: string | null
  ref_id?: number | null
  sent_at?: string | null
  created_at: string
}

export interface RetryEmailsResponse {
  retried_count: number
  message: string
}
