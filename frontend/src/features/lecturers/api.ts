import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { http } from '@/features/school-shared/http'
import type { Page } from '@/features/school-shared/types'

export interface Lecturer {
  id: number
  code: string | null
  full_name: string
  faculty_id: number
  email: string | null
  phone: string | null
  is_active: boolean
}

export interface LecturerListParams {
  page?: number
  size?: number
  q?: string
  faculty_id?: number
  include_inactive?: boolean
}

export type LecturerBody = Partial<Omit<Lecturer, 'id'>>

const keys = { all: ['lecturers'] as const }

function clean<T extends object>(params: T) {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
}

export async function listLecturers(params: LecturerListParams): Promise<Page<Lecturer>> {
  const { data } = await http.get<Page<Lecturer>>('/admin/lecturers', { params: clean(params) })
  return data
}

export function useLecturers(params: LecturerListParams) {
  return useQuery({
    queryKey: [...keys.all, 'list', params],
    queryFn: () => listLecturers(params),
    placeholderData: (previous) => previous,
  })
}

export function useSaveLecturer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, body }: { id?: number; body: LecturerBody }) => {
      const { data } =
        id === undefined
          ? await http.post<Lecturer>('/admin/lecturers', body)
          : await http.put<Lecturer>(`/admin/lecturers/${id}`, body)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  })
}

export function useDeactivateLecturer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => http.delete(`/admin/lecturers/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.all }),
  })
}
