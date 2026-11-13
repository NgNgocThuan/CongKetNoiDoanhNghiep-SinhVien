import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from './api-error'
import { toast } from './toast'

export function createQueryClient() {
  const notify = (error: Error) => {
    if (error instanceof ApiError && error.code === 'REQUEST_CANCELLED') return
    toast.error(error.message)
  }
  return new QueryClient({
    queryCache: new QueryCache({ onError: notify }),
    mutationCache: new MutationCache({ onError: (error, _variables, _context, mutation) => {
      if (!mutation.options.onError) notify(error)
    } }),
    defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: false,
      retry: (count, error) => count < 1 && error instanceof ApiError && error.code !== 'REQUEST_CANCELLED' && (error.status === null || error.status >= 500) },
    mutations: { retry: false },
  } })
}
