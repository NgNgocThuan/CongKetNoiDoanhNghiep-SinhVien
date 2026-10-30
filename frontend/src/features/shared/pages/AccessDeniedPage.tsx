import { Link } from 'react-router-dom'
import { ShieldX } from 'lucide-react'
import { useAuth, roleHome } from '@/features/auth'
export default function AccessDeniedPage() {
  const { user } = useAuth()
  return <main className="center-page"><div className="state"><ShieldX size={40} /><p className="eyebrow">403 · Giới hạn truy cập</p><h1>Bạn không có quyền truy cập</h1><p>Trang này dành cho một vai trò khác.</p><Link className="button button--primary" to={user ? roleHome[user.role] : '/login'}>Về không gian của tôi</Link></div></main>
}
