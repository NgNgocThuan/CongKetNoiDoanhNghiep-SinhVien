import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown, ChevronRight, LogOut, Menu, Settings2 } from 'lucide-react'
import { useAuth, roleHome, roleLabel, userDisplayName } from '@/features/auth'
import { features } from '@/config/navigation'
import { NotificationBell } from '@/features/notifications'
import { UserAvatar } from '@/components/common/UserAvatar'

export function Header({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const [signingOut, setSigningOut] = useState(false)
  if (!user) return null
  const base = roleHome[user.role]
  const current =
    features[user.role]
      .slice()
      .sort((a, b) => b.path.length - a.path.length)
      .find(
        feature =>
          pathname === base + '/' + feature.path ||
          pathname.startsWith(base + '/' + feature.path + '/')
      )?.title ||
    (pathname.endsWith('/settings')
      ? 'Tài khoản & bảo mật'
      : pathname.endsWith('/notifications')
        ? 'Thông báo'
        : 'Trang chủ')

  async function signOut() {
    setSigningOut(true)
    try {
      await logout()
    } catch {
      /* Local session is already cleared even if offline. */
    } finally {
      setSigningOut(false)
    }
  }

  return (
    <header className="app-header">
      <div className="header-breadcrumb">
        <button
          className="icon-button mobile-menu-button"
          aria-label="Mở điều hướng"
          onClick={onOpenMenu}
        >
          <Menu size={20} />
        </button>
        <span className="header-role-badge">{roleLabel[user.role]}</span>
        <ChevronRight size={14} className="header-crumb-sep" aria-hidden="true" />
        <strong className="header-current-page">{current}</strong>
      </div>
      <div className="header-tools">
        <NotificationBell />
        <span className="header-divider" />
        <details className="user-menu">
          <summary>
            <UserAvatar userId={user.id} name={userDisplayName(user)} />
            <span className="user-menu__name">
              <strong>{userDisplayName(user)}</strong>
              <span>{roleLabel[user.role]}</span>
            </span>
            <ChevronDown size={14} className="user-menu__chevron" />
          </summary>
          <div className="user-menu__panel">
            <div className="user-menu__header">
              <strong>{userDisplayName(user)}</strong>
              <p>{user.email}</p>
            </div>
            <div className="user-menu__divider" />
            <Link to={base + '/settings'}>
              <Settings2 size={16} />
              <span>Tài khoản & bảo mật</span>
            </Link>
            <button disabled={signingOut} onClick={() => void signOut()}>
              <LogOut size={16} />
              <span>{signingOut ? 'Đang đăng xuất…' : 'Đăng xuất'}</span>
            </button>
          </div>
        </details>
      </div>
    </header>
  )
}
