import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

const JobModerationPage = lazy(
  () => import('./pages/JobModerationPage')
)

export const jobModerationRoutes: RouteObject[] = [
  { path: 'jobs', element: <JobModerationPage /> },
]
