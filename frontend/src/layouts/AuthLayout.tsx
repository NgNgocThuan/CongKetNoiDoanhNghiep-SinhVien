import { Outlet } from 'react-router-dom'

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-[#FAF8FF] font-sans text-[#131B2E]">
      <Outlet />
    </div>
  )
}
