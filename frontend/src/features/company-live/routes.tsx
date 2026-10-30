import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Profile = lazy(() => import('./Pages').then(module => ({ default: module.CompanyProfilePage })))
const Jobs = lazy(() => import('./Pages').then(module => ({ default: module.CompanyJobsPage })))
const Applications = lazy(() => import('./Pages').then(module => ({ default: module.CompanyApplicationsPage })))
const Invitations = lazy(() => import('./Pages').then(module => ({ default: module.CompanyInvitationsPage })))
export const companyLiveRoutes: RouteObject[] = [
  { path: 'profile', element: <Profile /> }, { path: 'jobs', element: <Jobs /> },
  { path: 'applications', element: <Applications /> }, { path: 'invitations', element: <Invitations /> },
]
