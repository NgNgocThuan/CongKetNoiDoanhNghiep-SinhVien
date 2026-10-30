import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
const Jobs = lazy(() => import('./pages/RecommendedJobsPage'))
const Candidates = lazy(() => import('./pages/CandidateRecommendationsPage'))
export const studentMatchingRoutes: RouteObject[] = [{ path: 'recommended', element: <Jobs /> }]
export const companyMatchingRoutes: RouteObject[] = [{ path: 'candidates', element: <Candidates /> }]
