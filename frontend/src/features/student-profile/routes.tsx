import { lazy } from 'react'
const Profile=lazy(()=>import('./pages/ProfilePage'))
export const studentProfileRoutes=[{path:'profile',element:<Profile/>}]

