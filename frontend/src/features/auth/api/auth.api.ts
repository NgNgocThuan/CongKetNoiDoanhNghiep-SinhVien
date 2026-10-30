import { http, publicHttp } from '@/lib/http'
import { tokenSchema, userSchema } from '../types/auth.types'
import type { LoginInput, RegisterCompanyInput, RegisterCompanyResponse } from '../types/auth.types'

export const authApi = {
  login: async (data: LoginInput) => tokenSchema.parse((await publicHttp.post('/auth/login', data)).data),
  me: async () => userSchema.parse((await http.get('/auth/me')).data),
  logout: (access: string | null, refresh: string | null) =>
    publicHttp.post('/auth/logout', { refresh_token: refresh }, { headers: access ? { Authorization: 'Bearer ' + access } : {} }),
  forgotPassword: (email: string) => publicHttp.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, password: string) =>
    publicHttp.post('/auth/reset-password', { token, new_password: password }),
  activate: (token: string, password: string) =>
    publicHttp.post('/auth/activate', { token, new_password: password }),
  changePassword: (oldPassword: string, newPassword: string) =>
    http.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
  registerCompany: async (data: RegisterCompanyInput): Promise<RegisterCompanyResponse> =>
    (await publicHttp.post('/auth/register-company', data)).data,
}
