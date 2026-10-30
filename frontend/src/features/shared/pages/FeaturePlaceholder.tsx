import { Link } from 'react-router-dom'
import { ArrowLeft, Construction } from 'lucide-react'
import type { FeatureItem } from '@/config/navigation'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/common/PageHeader'
import { Card } from '@/components/ui/Card'
import { useAuth, roleHome } from '@/features/auth'

export default function FeaturePlaceholder({ feature }: { feature: FeatureItem }) {
  const { user } = useAuth()
  return <><PageHeader eyebrow="KHÔNG GIAN LÀM VIỆC" title={feature.title} description={feature.description} actions={<Badge tone="warning">Đang phát triển</Badge>} /><Card><div className="state planned-state"><span className="state__icon"><Construction size={31} /></span><h2>Chúng tôi đang hoàn thiện tiện ích này</h2><p>Bạn sẽ có thể sử dụng ngay khi tính năng sẵn sàng. Cảm ơn bạn đã đồng hành.</p><Link className="button button--secondary" to={user ? roleHome[user.role] : '/login'}><ArrowLeft size={16} />Về trang chủ</Link></div></Card></>
}
