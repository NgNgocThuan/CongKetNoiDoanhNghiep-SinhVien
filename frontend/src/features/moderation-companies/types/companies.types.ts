export type CompanyDocType =
  | 'BUSINESS_LICENSE'
  | 'TAX_CERTIFICATE'
  | 'AUTHORIZATION_LETTER'
  | 'OTHER'

export type CompanySize =
  | '1-10'
  | '11-50'
  | '51-200'
  | '201-500'
  | '501-1000'
  | '1000+'

export type VerificationStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface CompanyDocumentAdminRead {
  id: number
  doc_type: CompanyDocType
  file_url: string
  uploaded_at: string
}

export interface AdminCompanyRead {
  id: number
  user_id: number
  name: string
  tax_code: string
  industry_id?: number | null
  company_size?: CompanySize | string | null
  address?: string | null
  website?: string | null
  logo_url?: string | null
  contact_name?: string | null
  contact_phone?: string | null
  verification_status: VerificationStatus
  verified_by?: number | null
  verified_at?: string | null
  reject_reason?: string | null
  created_at: string
  updated_at: string
}

export interface AdminCompanyDetailRead extends AdminCompanyRead {
  description?: string | null
  tech_stack?: string | null
  benefits?: string | null
  documents: CompanyDocumentAdminRead[]
}

export interface CompanyRejectRequest {
  reject_reason: string
}
