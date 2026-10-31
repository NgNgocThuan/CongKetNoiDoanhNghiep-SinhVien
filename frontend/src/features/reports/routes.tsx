import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

const ReportsPage = lazy(
  () => import('./pages/ReportsPage')
)

export const reportsRoutes: RouteObject[] = [
  { path: 'reports', element: <ReportsPage /> },
]
