import { lazy } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import type { RouteObject } from 'react-router-dom'
const List = lazy(() => import('./TermListPage'))
const Detail = lazy(() => import('./TermDetailPage'))
function LegacyTermRedirect() {
  const { termId } = useParams()
  return <Navigate to={'/admin/internships' + (termId ? '/' + termId : '')} replace />
}
export const internshipAdminRoutes: RouteObject[] = [
  { path: 'internships', element: <List /> },
  { path: 'internships/:termId', element: <Detail /> },
  { path: 'internship-terms', element: <LegacyTermRedirect /> },
  { path: 'internship-terms/:termId', element: <LegacyTermRedirect /> },
]
