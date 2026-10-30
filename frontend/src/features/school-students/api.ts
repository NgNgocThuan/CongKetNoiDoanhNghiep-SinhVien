import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { http } from '@/features/school-shared/http'
import type { Page } from '@/features/school-shared/types'
import type {
  Achievement,
  AchievementCreate,
  AdminStudent,
  Certificate,
  ImportBatch,
  ImportBatchDetail,
  ImportResult,
  ImportType,
  StudentAcademicUpdate,
  StudentDetail,
  StudentListParams,
} from './types'

export const studentKeys = {
  all: ['school-students'] as const,
  list: (params: StudentListParams) => ['school-students', 'list', params] as const,
  detail: (id: number) => ['school-students', 'detail', id] as const,
  imports: (params: object) => ['school-students', 'imports', params] as const,
  importDetail: (id: number) => ['school-students', 'imports', id] as const,
}

function clean<T extends object>(params: T) {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
}

export async function listStudents(params: StudentListParams): Promise<Page<AdminStudent>> {
  const { data } = await http.get<Page<AdminStudent>>('/admin/students', { params: clean(params) })
  return data
}

export function useStudents(params: StudentListParams) {
  return useQuery({
    queryKey: studentKeys.list(params),
    queryFn: () => listStudents(params),
    placeholderData: (previous) => previous,
  })
}

export function useStudentDetail(id: number) {
  return useQuery({
    queryKey: studentKeys.detail(id),
    queryFn: async () => (await http.get<StudentDetail>(`/admin/students/${id}`)).data,
  })
}

export function useUpdateStudent(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: StudentAcademicUpdate) => (await http.put<AdminStudent>(`/admin/students/${id}`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: studentKeys.all }),
  })
}

export function useIssueAccount(id: number) {
  return useMutation({
    mutationFn: async () => (await http.post<{ message: string }>(`/admin/students/${id}/issue-account`)).data,
  })
}

export function useAddAchievement(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: AchievementCreate) =>
      (await http.post<Achievement>(`/admin/students/${id}/achievements`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: studentKeys.detail(id) }),
  })
}

export function useDeleteAchievement(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (achievementId: number) => http.delete(`/admin/students/${id}/achievements/${achievementId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: studentKeys.detail(id) }),
  })
}

export function useVerifyCertificate(studentId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (certificateId: number) =>
      (await http.post<Certificate>(`/admin/students/certificates/${certificateId}/verify`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: studentKeys.detail(studentId) }),
  })
}

// ---- Import
export function useImportStudents() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData()
      body.append('file', file)
      return (await http.post<ImportResult>('/admin/students/import', body)).data
    },
    // Sinh viên mới xuất hiện ở danh sách và lịch sử import
    onSuccess: () => qc.invalidateQueries({ queryKey: studentKeys.all }),
  })
}

export function useImports(params: { page?: number; size?: number; type?: ImportType }) {
  return useQuery({
    queryKey: studentKeys.imports(params),
    queryFn: async () => (await http.get<Page<ImportBatch>>('/admin/students/imports', { params: clean(params) })).data,
    placeholderData: (previous) => previous,
  })
}

export function useImportDetail(id: number | null) {
  return useQuery({
    queryKey: studentKeys.importDetail(id ?? 0),
    queryFn: async () => (await http.get<ImportBatchDetail>(`/admin/students/imports/${id}`)).data,
    enabled: id !== null,
  })
}
