import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown, LogOut, Menu, Settings2 } from 'lucide-react'
import { useAuth, roleHome, roleLabel, userDisplayName } from '@/features/auth'
import { features } from '@/config/navigation'
import { NotificationBell } from '@/features/notifications'

export function Header({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { user, logout } = useAuth(), { pathname } = useLocation()
  const [signingOut, setSigningOut] = useState(false)
  if (!user) return null
  const base = roleHome[user.role]
  const current = features[user.role].find(feature => pathname === base + '/' + feature.path)?.title || (pathname.endsWith('/settings') ? 'Tài khoản & bảo mật' : pathname.endsWith('/notifications') ? 'Thông báo' : 'Trang chủ')
  async function signOut() {
    setSigningOut(true)
    try { await logout() } catch { /* Local session is already cleared even if offline. */ }
    finally { setSigningOut(false) }
  }
  return <header className="app-header"><div className="header-breadcrumb"><button className="icon-button mobile-menu-button" aria-label="Mở điều hướng" onClick={onOpenMenu}><Menu size={21} /></button><span>{roleLabel[user.role]}</span><span aria-hidden="true">/</span><strong>{current}</strong></div>
    <div className="header-tools"><NotificationBell /><span className="header-divider" /><details className="user-menu"><summary><span className="avatar">{userDisplayName(user).slice(0, 1).toUpperCase()}</span><span className="user-menu__name"><strong>{userDisplayName(user)}</strong><span>{roleLabel[user.role]}</span></span><ChevronDown size={15} /></summary>
      <div className="user-menu__panel"><p>{user.email}</p><Link to={base + '/settings'}><Settings2 size={16} />Tài khoản & bảo mật</Link><button disabled={signingOut} onClick={() => void signOut()}><LogOut size={16} />Đăng xuất</button></div>
    </details></div>
  </header>
}
