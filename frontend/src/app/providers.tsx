import { useState } from 'react'
import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { createQueryClient } from '@/lib/query-client'
import { AuthProvider } from '@/features/auth'
import { AppErrorBoundary } from '@/components/common/AppErrorBoundary'

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient)
  return <AppErrorBoundary><QueryClientProvider client={queryClient}><AuthProvider>{children}</AuthProvider></QueryClientProvider></AppErrorBoundary>
}
