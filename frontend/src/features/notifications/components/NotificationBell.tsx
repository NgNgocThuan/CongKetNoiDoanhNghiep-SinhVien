import { Link } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuth, roleHome } from '@/features/auth'
import { notificationsApi } from '../api/notifications.api'

export function NotificationBell() {
  const { user } = useAuth()
  const { data } = useQuery({ queryKey: ['notifications', 'count'], queryFn: notificationsApi.count, enabled: !!user })
  return <Link to={user ? roleHome[user.role] + '/notifications' : '/login'} className="icon-button notification-bell" aria-label={data?.unread_count ? 'Thông báo, ' + data.unread_count + ' chưa đọc' : 'Thông báo'}><Bell size={20} />{data && data.unread_count > 0 && <span className="notification-dot" aria-hidden="true" />}</Link>
}
