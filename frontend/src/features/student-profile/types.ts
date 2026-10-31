export interface Profile {
  student_id: number
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
  updated_at: string
}
export interface StudentRecord {
  id: number
  [key: string]: unknown
}
export interface StudentSkill {
  skill_id: number
  name: string
  level: string
  source: string
}
export interface FullProfile {
  official: {
    id: number
    student_code: string
    full_name: string
    date_of_birth: string | null
    class_name: string | null
    cohort: string
    gpa: string | number | null
    academic_result: string | null
    phone: string | null
    faculty: { id: number; name: string }
    major: { id: number; name: string }
    certificates: StudentRecord[]
    achievements: StudentRecord[]
  }
  self_declared: {
    profile: Profile
    skills: StudentSkill[]
    experiences: StudentRecord[]
    projects: StudentRecord[]
    certificates: StudentRecord[]
  }
}
