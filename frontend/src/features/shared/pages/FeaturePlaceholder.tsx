import { Link } from 'react-router-dom'
import { ArrowLeft, Construction } from 'lucide-react'
import type { FeatureItem } from '@/config/navigation'
import { Badge } from '@/components/ui/Badge'
import { PageHeader } from '@/components/common/PageHeader'
import { Card } from '@/components/ui/Card'
import { useAuth, roleHome } from '@/features/auth'

export default function FeaturePlaceholder({ feature }: { feature: FeatureItem }) {
  const { user } = useAuth()
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="KHÔNG GIAN LÀM VIỆC"
        title={feature.title}
        description={feature.description}
        actions={<Badge tone="warning">Đang hoàn thiện tính năng</Badge>}
      />
      <Card>
        <div className="state planned-state">
          <span className="state__icon">
            <Construction size={32} />
          </span>
          <h2>Chúng tôi đang hoàn thiện tiện ích này</h2>
          <p>
            Tính năng sẽ sớm được phát hành trong bản cập nhật tiếp theo. Mọi dữ liệu của bạn trên hệ thống vẫn luôn sẵn sàng.
          </p>
          <Link className="button button--secondary" to={user ? roleHome[user.role] : '/login'}>
            <ArrowLeft size={16} />
            <span>Về trang chủ</span>
          </Link>
        </div>
      </Card>
    </div>
  )
}
