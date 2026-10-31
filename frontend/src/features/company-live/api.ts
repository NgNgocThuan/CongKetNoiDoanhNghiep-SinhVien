import { http } from '@/lib/http'
import type { Page } from '@/types/api'
export interface CompanyProfile {
  id: number
  name: string
  tax_code: string
  address: string | null
  website: string | null
  description: string | null
  contact_name: string | null
  contact_phone: string | null
  verification_status: string
}
export interface CompanyJob {
  id: number
  title: string
  position: string
  status: string
  deadline: string
  application_count: number
  view_count: number
}
export interface Invitation {
  id: number
  job_id: number
  student_id: number
  status: string
  message: string | null
  created_at: string
}
export interface Application {
  id: number
  job_id: number
  current_status: string
  contact_email: string | null
  student: { full_name: string; gpa: number | null; skills: string[] }
  cv_download_url: string
}
export const companyApi = {
  profile: async () => (await http.get<CompanyProfile>('/companies/me')).data,
  saveProfile: async (data: Partial<CompanyProfile>) =>
    (await http.put('/companies/me', data)).data,
  jobs: async (page: number) =>
    (
      await http.get<Page<CompanyJob>>('/jobs/me', {
        params: { page, size: 20 },
      })
    ).data,
  invitations: async (page: number) =>
    (
      await http.get<Page<Invitation>>('/invitations/company', {
        params: { page, size: 20 },
      })
    ).data,
  applications: async (jobId: number, page: number) =>
    (
      await http.get<Page<Application>>('/company/applications', {
        params: { job_id: jobId, page, size: 20 },
      })
    ).data,
}
