import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import { catalogRoutes } from '@/features/catalog/routes'
import { studentJobRoutes } from '@/features/student-jobs/routes'
import { studentProfileRoutes } from '@/features/student-profile/routes'
import { studentCVRoutes } from '@/features/student-cvs/routes'
import { studentApplicationRoutes } from '@/features/student-applications/routes'
import { studentInvitationRoutes } from '@/features/student-invitations/routes'
import { studentInternshipRoutes } from '@/features/student-internships/routes'

// Add each feature's relative routes under its backend role.
export const featureRoutes: Record<Role, RouteObject[]> = {
  STUDENT: [...studentJobRoutes, ...studentProfileRoutes, ...studentCVRoutes, ...studentApplicationRoutes, ...studentInvitationRoutes, ...studentInternshipRoutes],
  COMPANY: [],
  ADMIN: [...catalogRoutes],
}
