import { lazy } from 'react'
const Invitations = lazy(() => import('./pages/InvitationsPage'))
export const studentInvitationRoutes = [
  { path: 'invitations', element: <Invitations /> },
]
