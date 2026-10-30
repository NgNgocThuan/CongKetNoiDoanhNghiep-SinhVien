import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { http } from '@/features/school-shared/http'
import type { Page } from '@/features/school-shared/types'
import type {
  AssignLecturersResult,
  InternshipResult,
  ResultListParams,
  Term,
  TermForm,
  TermImportResult,
  TermJob,
  TermListParams,
  TermStatus,
  TermStudent,
  TermStudentAddResult,
} from './types'

export const termKeys = {
  all: ['internship-terms'] as const,
  list: (p: TermListParams) => ['internship-terms', 'list', p] as const,
  detail: (id: number) => ['internship-terms', 'detail', id] as const,
  students: (id: number, p: object) => ['internship-terms', id, 'students', p] as const,
  jobs: (id: number, p: object) => ['internship-terms', id, 'jobs', p] as const,
  results: (id: number, p: object) => ['internship-terms', id, 'results', p] as const,
}

function clean<T extends object>(params: T) {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
}

// ---- Đợt
export function useTerms(params: TermListParams) {
  return useQuery({
    queryKey: termKeys.list(params),
    queryFn: async () => (await http.get<Page<Term>>('/internship-terms', { params: clean(params) })).data,
    placeholderData: (previous) => previous,
  })
}

export function useTerm(id: number) {
  return useQuery({
    queryKey: termKeys.detail(id),
    queryFn: async () => (await http.get<Term>(`/internship-terms/${id}`)).data,
  })
}

export function useSaveTerm() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, body }: { id?: number; body: Partial<TermForm> }) =>
      id === undefined
        ? (await http.post<Term>('/internship-terms', body)).data
        : (await http.put<Term>(`/internship-terms/${id}`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

export function useChangeTermStatus(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (status: TermStatus) => (await http.post<Term>(`/internship-terms/${id}/status`, { status })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

// ---- Sinh viên trong đợt
export function useTermStudents(id: number, params: { page?: number; size?: number; q?: string; lecturer_id?: number }) {
  return useQuery({
    queryKey: termKeys.students(id, params),
    queryFn: async () => (await http.get<Page<TermStudent>>(`/internship-terms/${id}/students`, { params: clean(params) })).data,
    placeholderData: (previous) => previous,
  })
}

export function useAddTermStudents(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (studentIds: number[]) =>
      (await http.post<TermStudentAddResult>(`/internship-terms/${id}/students`, { student_ids: studentIds })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

export function useImportTermStudents(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData()
      body.append('file', file)
      return (await http.post<TermImportResult>(`/internship-terms/${id}/students/import`, body)).data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

export function useRemoveTermStudent(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (studentId: number) => http.delete(`/internship-terms/${id}/students/${studentId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

export function useAssignLecturers(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { lecturer_id: number | null; student_ids: number[] }) =>
      (await http.post<AssignLecturersResult>(`/internship-terms/${id}/assign-lecturers`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

// ---- Tin thuộc đợt
export function useTermJobs(id: number, params: { page?: number; size?: number }) {
  return useQuery({
    queryKey: termKeys.jobs(id, params),
    queryFn: async () => (await http.get<Page<TermJob>>(`/internship-terms/${id}/jobs`, { params })).data,
    placeholderData: (previous) => previous,
  })
}

// ---- Kết quả thực tập
/** Đọc kết quả của cả đợt (có lọc). `id` của từng dòng chính là result_id dùng cho API đánh giá/xác nhận. */
export function useTermResults(id: number, params: ResultListParams) {
  return useQuery({
    queryKey: termKeys.results(id, params),
    queryFn: async () => (await http.get<Page<InternshipResult>>(`/internship-terms/${id}/results`, { params: clean(params) })).data,
    placeholderData: (previous) => previous,
  })
}

export function useSaveLecturerReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ resultId, comment, score }: { resultId: number; comment: string | null; score: number | null }) =>
      (
        await http.put<InternshipResult>(`/internship-terms/results/${resultId}/lecturer-review`, {
          comment,
          score: score === null ? null : score.toFixed(2),
        })
      ).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}

export function useConfirmResult() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ resultId, result }: { resultId: number; result: 'PASSED' | 'FAILED' }) =>
      (await http.post<InternshipResult>(`/internship-terms/results/${resultId}/confirm`, { result })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: termKeys.all }),
  })
}
