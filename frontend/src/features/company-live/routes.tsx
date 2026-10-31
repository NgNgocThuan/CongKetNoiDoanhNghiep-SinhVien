import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Profile = lazy(() => import('./Profile'))
const Jobs = lazy(() => import('./Jobs'))
const Applications = lazy(() => import('./Applications'))
const Invitations = lazy(() => import('./Invitations'))
const JobStats = lazy(() =>
  import('./Jobs').then((module) => ({ default: module.JobStatsPage })),
)
const Evaluation = lazy(() =>
  import('./Applications').then((module) => ({
    default: module.EvaluationPage,
  })),
)
export const companyLiveRoutes: RouteObject[] = [
  { path: 'profile', element: <Profile /> },
  { path: 'jobs', element: <Jobs /> },
  { path: 'applications', element: <Applications /> },
  { path: 'invitations', element: <Invitations /> },
  { path: 'jobs/:jobId/stats', element: <JobStats /> },
  { path: 'evaluations/:resultId', element: <Evaluation /> },
]
