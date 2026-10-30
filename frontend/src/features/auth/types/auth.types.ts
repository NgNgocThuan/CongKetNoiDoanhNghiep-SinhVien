import { z } from 'zod'

export const roleSchema = z.enum(['STUDENT', 'COMPANY', 'ADMIN'])
export type Role = z.infer<typeof roleSchema>
export const userSchema = z.object({
  id: z.number(),
  email: z.string(),
  role: roleSchema,
  status: z.string(),
  student: z.object({ id: z.number(), full_name: z.string() }).nullish(),
  company: z.object({ id: z.number(), name: z.string() }).nullish(),
  admin: z.object({ id: z.number(), full_name: z.string() }).nullish(),
})
export type User = z.infer<typeof userSchema>
export const tokenSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
})
export type TokenPair = z.infer<typeof tokenSchema>
export interface LoginInput {
  email: string
  password: string
}
export interface RegisterCompanyInput {
  email: string
  password: string
  company_name: string
  tax_code: string
  industry_id?: number | null
  address?: string | null
  website?: string | null
  contact_name?: string | null
  contact_phone?: string | null
}
export interface RegisterCompanyResponse {
  user_id: number
  company_id: number
  email: string
  company_name: string
  tax_code: string
  status: string
  verification_status: string
  message: string
}
export const roleHome: Record<Role, string> = {
  STUDENT: '/student',
  COMPANY: '/company',
  ADMIN: '/admin',
}
export const roleLabel: Record<Role, string> = {
  STUDENT: 'Sinh viên',
  COMPANY: 'Doanh nghiệp',
  ADMIN: 'Nhà trường',
}
export function userDisplayName(user: User) {
  return user.student?.full_name || user.company?.name || user.admin?.full_name || user.email
}
