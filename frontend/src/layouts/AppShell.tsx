import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import type { Role } from '@/features/auth'
import { Header } from './components/Header'
import { Sidebar } from './components/Sidebar'

export function AppShell({ role }: { role: Role }) {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  useEffect(() => { setOpen(false) }, [pathname])
  return <div className="app-shell" data-role={role}>
    <a href="#main-content" className="skip-link">Đến nội dung chính</a>
    <aside className="desktop-sidebar"><Sidebar role={role} /></aside>
    <Dialog.Root open={open} onOpenChange={setOpen}><Dialog.Portal><Dialog.Overlay className="dialog-overlay" /><Dialog.Content className="mobile-sidebar" aria-describedby={undefined}><Dialog.Title className="sr-only">Điều hướng</Dialog.Title><Dialog.Close className="icon-button mobile-sidebar__close" aria-label="Đóng điều hướng"><X size={20} /></Dialog.Close><Sidebar role={role} onNavigate={() => setOpen(false)} /></Dialog.Content></Dialog.Portal></Dialog.Root>
    <div className="app-main"><Header onOpenMenu={() => setOpen(true)} /><main id="main-content" className="page-content" tabIndex={-1}><Outlet /></main><footer className="app-footer">Student Connect<span>Kết nối để cùng phát triển.</span></footer></div>
  </div>
}
