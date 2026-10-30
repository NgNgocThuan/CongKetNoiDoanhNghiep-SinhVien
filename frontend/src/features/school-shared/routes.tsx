import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
import { catalogRoutes } from '@/features/catalog/routes'
import { schoolStudentRoutes } from '@/features/school-students/routes'
import { lecturerRoutes } from '@/features/lecturers/routes'
import { internshipAdminRoutes } from '@/features/internship-admin/routes'
const SchoolWorkspace = lazy(() => import('./SchoolWorkspace'))
export const schoolRoutes: RouteObject[] = [{
  element: <SchoolWorkspace />,
  children: [...catalogRoutes, ...schoolStudentRoutes, ...lecturerRoutes, ...internshipAdminRoutes],
}]
