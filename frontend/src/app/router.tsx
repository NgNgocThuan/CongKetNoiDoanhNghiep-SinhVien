/**
 * Router tổng. Mỗi người khai báo route trong feature của mình, Thuận nối vào đây.
 * Hiện chỉ có các route admin của Phong.
 */
import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Result, Skeleton } from 'antd'
import AdminLayout from '@/layouts/AdminLayout'
import { RequireRole } from '@/features/auth/AuthProvider'
import LoginPage from '@/features/auth/LoginPage'

// Mỗi trang tải riêng khi vào lần đầu để bản build đầu không quá nặng
const CatalogPage = lazy(() => import('@/features/catalog/CatalogPage'))
const StudentListPage = lazy(() => import('@/features/school-students/StudentListPage'))
const StudentDetailPage = lazy(() => import('@/features/school-students/StudentDetailPage'))
const StudentImportPage = lazy(() => import('@/features/school-students/StudentImportPage'))
const LecturersPage = lazy(() => import('@/features/lecturers/LecturersPage'))
const TermListPage = lazy(() => import('@/features/internship-admin/TermListPage'))
const TermDetailPage = lazy(() => import('@/features/internship-admin/TermDetailPage'))

const page = (element: ReactNode) => <Suspense fallback={<Skeleton active paragraph={{ rows: 8 }} />}>{element}</Suspense>

export const routes = [
  { path: '/login', element: <LoginPage /> },
  {
    path: '/admin',
    element: (
      <RequireRole role="ADMIN">
        <AdminLayout />
      </RequireRole>
    ),
    children: [
      { index: true, element: <Navigate to="/admin/students" replace /> },
      { path: 'catalog', element: page(<CatalogPage />) },
      { path: 'students', element: page(<StudentListPage />) },
      { path: 'students/import', element: page(<StudentImportPage />) },
      { path: 'students/:studentId', element: page(<StudentDetailPage />) },
      { path: 'lecturers', element: page(<LecturersPage />) },
      { path: 'internship-terms', element: page(<TermListPage />) },
      { path: 'internship-terms/:termId', element: page(<TermDetailPage />) },
      { path: '*', element: <Result status="404" title="Không tìm thấy trang" /> },
    ],
  },
  { path: '/', element: <Navigate to="/admin" replace /> },
  { path: '*', element: <Result status="404" title="Không tìm thấy trang" /> },
]

export const router = createBrowserRouter(routes)
