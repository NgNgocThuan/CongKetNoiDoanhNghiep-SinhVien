import { lazy } from 'react'
const Internships = lazy(() => import('./pages/InternshipsPage'))
export const studentInternshipRoutes = [
  { path: 'internships', element: <Internships /> },
]
