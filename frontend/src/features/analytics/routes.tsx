import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Analytics = lazy(() => import('./Page'))
export const analyticsRoutes: RouteObject[] = [
  { path: 'analytics', element: <Analytics /> },
]
