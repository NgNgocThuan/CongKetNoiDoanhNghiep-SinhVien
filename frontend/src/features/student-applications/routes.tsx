import { lazy } from 'react'
const Applications = lazy(() => import('./pages/ApplicationsPage'))
const Detail = lazy(() => import('./pages/ApplicationDetailPage'))
export const studentApplicationRoutes = [
  { path: 'applications', element: <Applications /> },
  { path: 'applications/:id', element: <Detail /> },
]
