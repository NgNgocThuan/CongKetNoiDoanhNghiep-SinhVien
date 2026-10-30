import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import type { Role } from '../types/auth.types'
import { ErrorState, LoadingState } from '@/components/common/States'

export function RequireAuth() {
  const auth = useAuth()
  const location = useLocation()
  if (auth.status === 'loading') return <main className="center-page"><LoadingState label="Đang kiểm tra phiên đăng nhập…" /></main>
  if (auth.status === 'error') return <main className="center-page"><ErrorState message={auth.error?.message} onRetry={() => void auth.retry()} /></main>
  if (!auth.user) return <Navigate to="/login" state={{ from: location.pathname + location.search }} replace />
  return <Outlet />
}
export function RequireRole({ role }: { role: Role }) {
  const { user } = useAuth()
  return user?.role === role ? <Outlet /> : <Navigate to="/403" replace />
}
