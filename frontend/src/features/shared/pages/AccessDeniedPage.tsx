import { Link } from 'react-router-dom'
import { ArrowLeft, ShieldX } from 'lucide-react'
import { useAuth, roleHome } from '@/features/auth'

export default function AccessDeniedPage() {
  const { user } = useAuth()
  return (
    <main className="center-page">
      <div className="state state--error">
        <span className="state__icon">
          <ShieldX size={32} />
        </span>
        <p className="eyebrow">403 · Giới hạn quyền truy cập</p>
        <h1>Bạn không có quyền truy cập khu vực này</h1>
        <p>Khu vực này yêu cầu phân quyền quản trị hoặc vai trò người dùng tương ứng.</p>
        <Link className="button button--primary" to={user ? roleHome[user.role] : '/login'}>
          <ArrowLeft size={16} />
          <span>Về không gian làm việc</span>
        </Link>
      </div>
    </main>
  )
}
