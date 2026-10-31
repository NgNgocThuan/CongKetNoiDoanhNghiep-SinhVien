import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Jobs = lazy(() =>
  import('./Jobs').then((module) => ({ default: module.JobsPage })),
)
const JobDetail = lazy(() =>
  import('./Jobs').then((module) => ({ default: module.JobDetailPage })),
)
const CompanyPublic = lazy(() =>
  import('./Jobs').then((module) => ({ default: module.CompanyPublicPage })),
)
const Profile = lazy(() => import('./Profile'))
const CVs = lazy(() => import('./CVs'))
const Applications = lazy(() =>
  import('./Tracking').then((module) => ({ default: module.ApplicationsPage })),
)
const ApplicationDetail = lazy(() =>
  import('./Tracking').then((module) => ({
    default: module.ApplicationDetailPage,
  })),
)
const Invitations = lazy(() =>
  import('./Tracking').then((module) => ({ default: module.InvitationsPage })),
)
const Internships = lazy(() =>
  import('./Tracking').then((module) => ({ default: module.InternshipsPage })),
)
export const studentWorkspaceRoutes: RouteObject[] = [
  { path: 'jobs', element: <Jobs /> },
  { path: 'jobs/:jobId', element: <JobDetail /> },
  { path: 'companies/:companyId', element: <CompanyPublic /> },
  { path: 'saved-jobs', element: <Jobs saved /> },
  { path: 'profile', element: <Profile /> },
  { path: 'cvs', element: <CVs /> },
  { path: 'applications', element: <Applications /> },
  { path: 'applications/:applicationId', element: <ApplicationDetail /> },
  { path: 'invitations', element: <Invitations /> },
  { path: 'internships', element: <Internships /> },
]
