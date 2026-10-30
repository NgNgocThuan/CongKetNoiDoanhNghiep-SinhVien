export type AccountStatus = 'PENDING_ACTIVATION' | 'PENDING_APPROVAL' | 'ACTIVE' | 'LOCKED'
export type AchievementType = 'RESEARCH' | 'ACHIEVEMENT' | 'OTHER'
export type SkillLevel = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXPERT'
export type SkillSource = 'SELF' | 'CV_AI' | 'SCHOOL'
export type CertificateSource = 'SCHOOL' | 'SELF'
export type ImportType = 'STUDENTS' | 'TERM_STUDENTS' | 'SYNC'

/** Dòng danh sách + dữ liệu học thuật chính thức. Số thập phân (GPA) backend trả dạng chuỗi. */
export interface AdminStudent {
  id: number
  user_id: number
  student_code: string
  full_name: string
  email: string
  account_status: AccountStatus
  date_of_birth: string | null
  class_name: string | null
  faculty_id: number
  faculty_name: string
  major_id: number
  major_name: string
  cohort: string
  gpa: string | null
  academic_result: string | null
  phone: string | null
  synced_at: string | null
}

export interface Achievement {
  id: number
  student_id: number
  type: AchievementType
  title: string
  description: string | null
  achieved_at: string | null
}

export interface Certificate {
  id: number
  student_id: number
  name: string
  issuer: string | null
  issued_at: string | null
  expires_at: string | null
  credential_url: string | null
  source: CertificateSource
  is_verified: boolean
  verified_by: number | null
  verified_at: string | null
}

export interface SelfSkill {
  skill_id: number
  name: string
  level: SkillLevel
  source: SkillSource
}

export interface SelfProfile {
  avatar_url: string | null
  bio: string | null
  career_goal: string | null
  contact_email: string | null
  contact_phone: string | null
  address: string | null
  linkedin_url: string | null
  github_url: string | null
  is_open_to_work: boolean
  show_gpa: boolean
  show_contact: boolean
  show_achievements: boolean
}

export interface SelfExperience {
  id: number
  company_name: string
  position: string
  start_date: string | null
  end_date: string | null
  description: string | null
}

export interface SelfProject {
  id: number
  name: string
  role: string | null
  description: string | null
  tech_stack: string | null
  project_url: string | null
  start_date: string | null
  end_date: string | null
}

export interface StudentDetail {
  official: {
    academic: AdminStudent
    achievements: Achievement[]
    school_certificates: Certificate[]
  }
  self_declared: {
    profile: SelfProfile | null
    skills: SelfSkill[]
    experiences: SelfExperience[]
    projects: SelfProject[]
    certificates: Certificate[]
  }
}

export interface StudentListParams {
  page?: number
  size?: number
  q?: string
  faculty_id?: number
  major_id?: number
  cohort?: string
  account_status?: AccountStatus
}

/** Bản cập nhật dữ liệu học thuật; trường nào không gửi thì backend giữ nguyên. */
export interface StudentAcademicUpdate {
  full_name?: string
  date_of_birth?: string | null
  class_name?: string | null
  faculty_id?: number
  major_id?: number
  cohort?: string
  gpa?: string | null
  academic_result?: string | null
  phone?: string | null
}

export interface AchievementCreate {
  type: AchievementType
  title: string
  description?: string | null
  achieved_at?: string | null
}

// ---- Import
export interface ImportRowError {
  /** Số dòng trong file (dòng 1 là tiêu đề) */
  row: number
  key: string | null
  message: string
}

export interface ImportBatch {
  id: number
  type: ImportType
  file_name: string | null
  total_rows: number
  success_rows: number
  failed_rows: number
  imported_by: number
  created_at: string
}

export interface ImportBatchDetail extends ImportBatch {
  errors: ImportRowError[]
}

export interface ImportResult {
  batch: ImportBatchDetail
  activation_emails_queued: number
}
