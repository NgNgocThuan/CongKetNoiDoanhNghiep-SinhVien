import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import { catalogRoutes } from '@/features/catalog/routes'

// Add each feature's relative routes under its backend role.
export const featureRoutes: Record<Role, RouteObject[]> = {
  STUDENT: [],
  COMPANY: [],
  ADMIN: [...catalogRoutes],
}
