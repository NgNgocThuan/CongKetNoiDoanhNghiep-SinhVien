import { lazy } from 'react'
const CVs = lazy(() => import('./pages/CVsPage'))
export const studentCVRoutes = [{ path: 'cvs', element: <CVs /> }]
