import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Lecturers = lazy(() => import('./LecturersPage'))
export const lecturerRoutes: RouteObject[] = [{ path: 'lecturers', element: <Lecturers /> }]
