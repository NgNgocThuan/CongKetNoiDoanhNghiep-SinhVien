import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import { studentMatchingRoutes, companyMatchingRoutes } from '@/features/matching/routes'
import { companyLiveRoutes } from '@/features/company-live/routes'
import { schoolRoutes } from '@/features/school-shared/routes'
import { administrationRoutes } from '@/features/administration/routes'
import { analyticsRoutes } from '@/features/analytics/routes'
import { studentWorkspaceRoutes } from '@/features/student-workspace/routes'
export const featureRoutes: Record<Role, RouteObject[]> = {
  STUDENT: [...studentMatchingRoutes, ...studentWorkspaceRoutes],
  COMPANY: [...companyMatchingRoutes, ...companyLiveRoutes],
  ADMIN: [...schoolRoutes, ...administrationRoutes, ...analyticsRoutes],
}
