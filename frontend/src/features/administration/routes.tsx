import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Administration = lazy(() =>
  import('./pages').then((module) => ({ default: module.AdministrationPage })),
)
export const administrationRoutes: RouteObject[] = (
  ['users', 'companies', 'jobs', 'reports', 'email-logs'] as const
).map((kind) => ({ path: kind, element: <Administration kind={kind} /> }))
