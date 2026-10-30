import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const CatalogPage = lazy(() => import('./CatalogPage'))
export const catalogRoutes: RouteObject[] = [{ path: 'catalog', element: <CatalogPage /> }]
