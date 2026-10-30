import { lazy } from 'react'
import { Navigate } from 'react-router-dom'
import type { RouteObject } from 'react-router-dom'
import { authRoutes } from '@/features/auth/routes'
import { useAuth, RequireAuth, RequireRole, roleHome } from '@/features/auth'
import type { Role } from '@/features/auth'
import { StudentLayout } from '@/layouts/StudentLayout'
import { CompanyLayout } from '@/layouts/CompanyLayout'
import { AdminLayout } from '@/layouts/AdminLayout'
import { features } from '@/config/navigation'
import { featureRoutes } from './feature-routes'
import { LoadingState } from '@/components/common/States'

const Workspace = lazy(() => import('@/features/shared/pages/WorkspacePage'))
const Planned = lazy(() => import('@/features/shared/pages/FeaturePlaceholder'))
const NotFound = lazy(() => import('@/features/shared/pages/NotFoundPage'))
const Forbidden = lazy(() => import('@/features/shared/pages/AccessDeniedPage'))
const Password = lazy(() => import('@/features/auth/pages/PasswordPage'))
const Notifications = lazy(() => import('@/features/notifications/pages/NotificationsPage'))
function Entry() {
  const { user, status } = useAuth()
  if (status === 'loading') return <LoadingState />
  return <Navigate to={user ? roleHome[user.role] : '/login'} replace />
}
function roleRoutes(role: Role, layout: RouteObject['element']): RouteObject {
  return { element: <RequireRole role={role} />, children: [{ path: roleHome[role], element: layout, children: [
    { index: true, element: <Workspace /> },
    { path: 'settings', element: <Password mode="change" /> },
    { path: 'notifications', element: <Notifications /> },
    ...features[role].filter(feature => !feature.ready).map(feature => ({ path: feature.path, element: <Planned feature={feature} /> })),
    ...featureRoutes[role],
  ] }] }
}
export const routes: RouteObject[] = [
  { path: '/', element: <Entry /> },
  ...authRoutes,
  { element: <RequireAuth />, children: [
    roleRoutes('STUDENT', <StudentLayout />),
    roleRoutes('COMPANY', <CompanyLayout />),
    roleRoutes('ADMIN', <AdminLayout />),
    { path: '/403', element: <Forbidden /> },
  ] },
  { path: '*', element: <NotFound /> },
]
