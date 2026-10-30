import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const FacultiesPage = lazy(() => import('./pages/FacultiesPage'))
export const catalogRoutes: RouteObject[] = [{ path: 'catalog', element: <FacultiesPage /> }]
