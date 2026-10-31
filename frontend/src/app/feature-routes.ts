import type { RouteObject } from 'react-router-dom'
import type { Role } from '@/features/auth'
import { catalogRoutes } from '@/features/catalog/routes'
import { companyModerationRoutes } from '@/features/moderation-companies/routes'
import { jobModerationRoutes } from '@/features/moderation-jobs/routes'
import { userAdminRoutes } from '@/features/account-admin/routes'
import { reportsRoutes } from '@/features/reports/routes'
import { emailLogsRoutes } from '@/features/email-logs/routes'

// Add each feature's relative routes under its backend role.
export const featureRoutes: Record<Role, RouteObject[]> = {
  STUDENT: [],
  COMPANY: [],
  ADMIN: [
    ...catalogRoutes,
    ...companyModerationRoutes,
    ...jobModerationRoutes,
    ...userAdminRoutes,
    ...reportsRoutes,
    ...emailLogsRoutes,
  ],
}
