import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

const UserAdminPage = lazy(
  () => import('./pages/UserAdminPage')
)

export const userAdminRoutes: RouteObject[] = [
  { path: 'users', element: <UserAdminPage /> },
]
