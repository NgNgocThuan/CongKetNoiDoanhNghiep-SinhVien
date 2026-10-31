import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Jobs = lazy(() => import('./pages/JobsPage'))
const Detail = lazy(() => import('./pages/JobDetailPage'))
const Saved = lazy(() => import('./pages/SavedJobsPage'))
const Company = lazy(() => import('./pages/CompanyPage'))
export const studentJobRoutes: RouteObject[] = [
  { path: 'jobs', element: <Jobs /> },
  { path: 'jobs/:id', element: <Detail /> },
  { path: 'saved-jobs', element: <Saved /> },
  { path: 'companies/:id', element: <Company /> },
]
