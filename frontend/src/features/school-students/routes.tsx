import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const List = lazy(() => import('./StudentListPage'))
const Detail = lazy(() => import('./StudentDetailPage'))
const Import = lazy(() => import('./StudentImportPage'))
export const schoolStudentRoutes: RouteObject[] = [
  { path: 'students', element: <List /> },
  { path: 'students/import', element: <Import /> },
  { path: 'students/:studentId', element: <Detail /> },
]
