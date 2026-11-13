import { freelancerRoutes } from '@/features/freelancer/routes'
import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import {
  studentMatchingRoutes,
  companyMatchingRoutes,
} from '@/features/matching/routes'
import { companyLiveRoutes } from '@/features/company-live/routes'
import { schoolRoutes } from '@/features/school-shared/routes'
import { administrationRoutes } from '@/features/administration/routes'
import { analyticsRoutes } from '@/features/analytics/routes'
import { studentJobRoutes } from '@/features/student-jobs/routes'
import { studentProfileRoutes } from '@/features/student-profile/routes'
import { studentCVRoutes } from '@/features/student-cvs/routes'
import { studentApplicationRoutes } from '@/features/student-applications/routes'
import { studentInvitationRoutes } from '@/features/student-invitations/routes'
export const featureRoutes: Record<Role, RouteObject[]> = {
  CLIENT: [...freelancerRoutes()],
  STUDENT: [
    ...freelancerRoutes(),
    ...studentMatchingRoutes,
    ...studentJobRoutes,
    ...studentProfileRoutes,
    ...studentCVRoutes,
    ...studentApplicationRoutes,
    ...studentInvitationRoutes,
  ],
  COMPANY: [...companyMatchingRoutes, ...companyLiveRoutes, ...freelancerRoutes()],
  ADMIN: [...schoolRoutes, ...administrationRoutes, ...analyticsRoutes, ...freelancerRoutes(true)],
}
