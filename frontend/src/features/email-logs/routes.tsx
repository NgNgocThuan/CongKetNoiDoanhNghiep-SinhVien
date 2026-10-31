import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'

const EmailLogsPage = lazy(
  () => import('./pages/EmailLogsPage')
)

export const emailLogsRoutes: RouteObject[] = [
  { path: 'email-logs', element: <EmailLogsPage /> },
]
