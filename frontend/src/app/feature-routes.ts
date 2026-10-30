import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import { studentMatchingRoutes, companyMatchingRoutes } from '@/features/matching/routes'
import { catalogRoutes } from '@/features/catalog/routes'

// Add each feature's relative routes under its backend role.
export const featureRoutes: Record<Role, RouteObject[]> = {
  STUDENT: [...studentMatchingRoutes],
  COMPANY: [...companyMatchingRoutes],
  ADMIN: [...catalogRoutes],
}
