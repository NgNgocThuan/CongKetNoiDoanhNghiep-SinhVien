import { NavLink } from 'react-router-dom'
import { ArrowUpRight, Bell, LayoutDashboard, Settings2 } from 'lucide-react'
import { Brand } from '@/components/common/Brand'
import { features, shellCopy } from '@/config/navigation'
import { roleHome } from '@/features/auth'
import type { Role } from '@/features/auth'

export function Sidebar({ role, onNavigate }: { role: Role; onNavigate?: () => void }) {
  const base = roleHome[role]
  return <div className="sidebar-content"><Brand to={base} /><p className="sidebar-caption">{shellCopy[role].subtitle}</p>
    <nav aria-label="Điều hướng chính" className="sidebar-nav">
      <NavLink to={base} end onClick={onNavigate}><LayoutDashboard size={19} /><span>Trang chủ</span></NavLink>
      {features[role].map(feature => <NavLink key={feature.id} to={base + '/' + feature.path} onClick={onNavigate}><feature.icon size={19} /><span>{feature.title}</span>{!feature.ready && <span className="nav-planned" aria-label="Đang phát triển" />}</NavLink>)}
      <div className="nav-divider" /><NavLink to={base + '/notifications'} onClick={onNavigate}><Bell size={19} /><span>Thông báo</span></NavLink>
      <NavLink to={base + '/settings'} onClick={onNavigate}><Settings2 size={19} /><span>Tài khoản & bảo mật</span></NavLink>
    </nav>
    <div className="sidebar-bottom"><div className="sidebar-note"><span className="sidebar-note__icon">↗</span><strong>Mỗi kết nối đều có giá trị.</strong><p>Chủ động hôm nay, vững bước ngày mai.</p></div><p className="sidebar-footer">STUDENT CONNECT <ArrowUpRight size={13} /></p></div>
  </div>
}
