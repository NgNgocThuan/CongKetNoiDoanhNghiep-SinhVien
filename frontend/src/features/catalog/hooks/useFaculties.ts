import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../api/catalog.api'
export function useFaculties(params: { page: number; size: number; q: string }) {
  return useQuery({ queryKey: ['catalog', 'faculties', params], queryFn: ({ signal }) => catalogApi.faculties(params, signal) })
}
