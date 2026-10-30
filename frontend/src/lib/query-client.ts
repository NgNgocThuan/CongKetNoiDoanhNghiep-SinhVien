import { QueryClient } from '@tanstack/react-query'
import { ApiError } from './api-error'

export function createQueryClient() {
  return new QueryClient({ defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: false,
      retry: (count, error) => count < 1 && error instanceof ApiError && error.code !== 'REQUEST_CANCELLED' && (error.status === null || error.status >= 500) },
    mutations: { retry: false },
  } })
}
