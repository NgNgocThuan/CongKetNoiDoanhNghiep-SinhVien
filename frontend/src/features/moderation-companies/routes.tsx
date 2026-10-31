import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

const CompanyModerationPage = lazy(
  () => import('./pages/CompanyModerationPage')
)

export const companyModerationRoutes: RouteObject[] = [
  { path: 'companies', element: <CompanyModerationPage /> },
]
