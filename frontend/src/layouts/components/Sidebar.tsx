import { NavLink, useLocation } from 'react-router-dom'
import {
  ArrowUpRight,
  Bell,
  LayoutDashboard,
  Settings2,
  ChevronDown,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Brand } from '@/components/common/Brand'
import { navigationGroups, shellCopy } from '@/config/navigation'
import { roleHome } from '@/features/auth'
import type { Role } from '@/features/auth'

export function Sidebar({ role, onNavigate }: { role: Role; onNavigate?: () => void }) {
  const base = roleHome[role]
  const { pathname } = useLocation()
  const groups = navigationGroups(role)
  const activeGroup = groups.find(group =>
    group.items.some(
      f =>
        pathname === `${base}/${f.path}` ||
        pathname.startsWith(`${base}/${f.path}/`) ||
        isFreelancerContextActive(role, f.path, pathname, base)
    )
  )?.id

  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    recruitment: true,
    freelancer: true,
    management: true,
  })

  useEffect(() => {
    if (activeGroup) setExpanded(previous => ({ ...previous, [activeGroup]: true }))
  }, [activeGroup, pathname])

  return (
    <div className="sidebar-content">
      <div className="sidebar-header">
        <Brand to={base} />
        <p className="sidebar-caption">{shellCopy[role].subtitle}</p>
      </div>

      <nav aria-label="Điều hướng chính" className="sidebar-nav">
        <NavLink to={base} end onClick={onNavigate}>
          <LayoutDashboard size={18} />
          <span>Trang chủ</span>
        </NavLink>

        {groups.map(group => (
          <section className="sidebar-group" key={group.id}>
            <button
              className={'sidebar-group-title' + (activeGroup === group.id ? ' is-active' : '')}
              aria-expanded={Boolean(expanded[group.id])}
              aria-controls={`nav-${group.id}`}
              onClick={() =>
                setExpanded(previous => ({ ...previous, [group.id]: !previous[group.id] }))
              }
            >
              <span>{group.title}</span>
              {expanded[group.id] ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </button>
            <div id={`nav-${group.id}`} className="sidebar-children" hidden={!expanded[group.id]}>
              {group.items.map(feature => (
                <NavLink
                  key={feature.id}
                  to={base + '/' + feature.path}
                  end={feature.path === 'freelancer'}
                  className={({ isActive }) =>
                    isActive || isFreelancerContextActive(role, feature.path, pathname, base)
                      ? 'active'
                      : undefined
                  }
                  onClick={onNavigate}
                >
                  <feature.icon size={17} />
                  <span>{feature.title}</span>
                  {!feature.ready && (
                    <span className="nav-planned" aria-label="Đang phát triển" />
                  )}
                </NavLink>
              ))}
            </div>
          </section>
        ))}

        <div className="nav-divider" />
        <NavLink to={base + '/notifications'} onClick={onNavigate}>
          <Bell size={18} />
          <span>Thông báo</span>
        </NavLink>
        <NavLink to={base + '/settings'} onClick={onNavigate}>
          <Settings2 size={18} />
          <span>Tài khoản & bảo mật</span>
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <div className="sidebar-note">
          <span className="sidebar-note__icon">
            <Sparkles size={16} />
          </span>
          <strong>Mỗi kết nối đều có giá trị.</strong>
          <p>Chủ động hôm nay, vững bước ngày mai.</p>
        </div>
        <p className="sidebar-footer">
          <span>STUDENT CONNECT</span>
          <ArrowUpRight size={13} />
        </p>
      </div>
    </div>
  )
}

function isFreelancerContextActive(
  role: Role,
  featurePath: string,
  pathname: string,
  base: string
) {
  const relative = pathname.slice(base.length).replace(/^\//, '')
  if (!relative.startsWith('freelancer/')) return false
  if (featurePath === 'freelancer/projects') return /^freelancer\/projects(?:\/|$)/.test(relative)
  if (featurePath === 'freelancer/work') {
    if (role === 'ADMIN') return false
    return /^freelancer\/(?:work|contracts|milestones|disputes)(?:\/|$)/.test(relative)
  }
  if (featurePath === 'freelancer/finance')
    return /^freelancer\/(?:finance|payments|settlements)(?:\/|$)/.test(relative)
  if (role === 'ADMIN' && featurePath === 'freelancer/admin/projects')
    return /^freelancer\/projects(?:\/|$)/.test(relative)
  if (role === 'ADMIN' && featurePath === 'freelancer/admin/disputes')
    return /^freelancer\/disputes(?:\/|$)/.test(relative)
  return false
}
