import { Suspense } from 'react'
import { useRoutes } from 'react-router-dom'
import { routes } from './router'
import { LoadingState } from '@/components/common/States'

export function App() {
  const element = useRoutes(routes)
  return <Suspense fallback={<main className="center-page"><LoadingState label="Đang mở trang…" /></main>}>{element}</Suspense>
}
