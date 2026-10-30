import { Link } from 'react-router-dom'
import { ArrowDown, ArrowUpRight, CheckCircle2, Fingerprint, Network, Sparkles } from 'lucide-react'
import { useAuth, roleHome, roleLabel, userDisplayName } from '@/features/auth'
import { features, shellCopy } from '@/config/navigation'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

export default function WorkspacePage() {
  const { user } = useAuth()
  if (!user) return null
  const copy = shellCopy[user.role], base = roleHome[user.role]
  return <><div className="workspace-welcome"><div><p className="eyebrow">{copy.subtitle}</p><p>Xin chào, <strong>{userDisplayName(user)}</strong> <span aria-hidden="true">✦</span></p></div><Badge tone="success"><CheckCircle2 size={12} /> Đã đăng nhập</Badge></div>
    <section className="workspace-hero"><div className="workspace-hero__copy"><span className="hero-label"><span className="dot" /> MỘT CỘNG ĐỒNG · NHIỀU CƠ HỘI</span><h1>{copy.heading}</h1><p>{copy.description}</p><a className="button button--white" href="#workspace">Khám phá không gian <ArrowDown size={16} /></a></div><div className="hero-orbit" aria-hidden="true"><div className="orbit orbit--one" /><div className="orbit orbit--two" /><div className="orbit-center"><Network size={52} strokeWidth={1.2} /></div><span className="orbit-tag orbit-tag--one">Học tập</span><span className="orbit-tag orbit-tag--two">Kết nối</span><span className="orbit-tag orbit-tag--three">Phát triển</span><span className="orbit-spark"><Sparkles size={22} /></span></div></section>
    <div className="workspace-grid"><section id="workspace"><div className="section-heading"><div><p className="eyebrow">DÀNH CHO BẠN</p><h2>Không gian làm việc</h2></div><span className="muted">{features[user.role].length} tiện ích</span></div><div className="feature-grid">{features[user.role].map(feature => <Link to={base + '/' + feature.path} className="feature-card" key={feature.id}><span className="feature-card__icon"><feature.icon size={22} /></span><ArrowUpRight className="feature-card__arrow" size={18} /><h3>{feature.title}</h3><p>{feature.description}</p><Badge tone={feature.ready ? 'success' : 'neutral'}>{feature.ready ? 'Có thể sử dụng' : 'Đang phát triển'}</Badge></Link>)}</div></section>
    <aside className="workspace-aside"><Card><span className="aside-icon"><Fingerprint size={26} /></span><p className="eyebrow">TÀI KHOẢN CỦA BẠN</p><h3>{userDisplayName(user)}</h3><p className="account-email">{user.email}</p><Badge tone="info">{roleLabel[user.role]}</Badge><div className="aside-separator" /><p className="muted">Quản lý mật khẩu và bảo vệ không gian riêng của bạn.</p><Link to={base + '/settings'} className="text-link">Tài khoản & bảo mật <ArrowUpRight size={15} /></Link></Card><div className="workspace-note"><span className="dot" /><p>Các tiện ích đang phát triển sẽ được bổ sung dần. Những dữ liệu đã lưu trên hệ thống vẫn được giữ nguyên.</p></div></aside></div>
  </>
}
