import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import { studentMatchingRoutes, companyMatchingRoutes } from '@/features/matching/routes'
import { schoolRoutes } from '@/features/school-shared/routes'
export const featureRoutes: Record<Role, RouteObject[]> = {
  STUDENT: [...studentMatchingRoutes],
  COMPANY: [...companyMatchingRoutes],
  ADMIN: [...schoolRoutes],
}
