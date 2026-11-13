import { RegisterClientPage } from '@/features/freelancer/routes'
import { lazy } from 'react'
import type { RouteObject } from 'react-router-dom'
import { AuthLayout } from '@/layouts/AuthLayout'

const Onboarding = lazy(() => import('@/features/freelancer/LimitedOnboarding'))
const Login = lazy(() => import('./pages/LoginPage'))
const Forgot = lazy(() => import('./pages/ForgotPasswordPage'))
const Password = lazy(() => import('./pages/PasswordPage'))
const Register = lazy(() => import('./pages/RegisterCompanyPage'))
export const authRoutes: RouteObject[] = [{
  element: <AuthLayout />, children: [
    { path: '/login', element: <Login /> },
    { path: '/forgot-password', element: <Forgot /> },
    { path: '/reset-password', element: <Password mode="reset" /> },
    { path: '/activate', element: <Password mode="activate" /> },
    { path: '/onboarding', element: <Onboarding /> },
    { path: '/register-client', element: <RegisterClientPage /> },
    { path: '/register-company', element: <Register /> },
  ],
}]
