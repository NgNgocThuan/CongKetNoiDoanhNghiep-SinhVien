import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
export default function NotFoundPage() {
  return <main className="center-page"><div className="state"><Compass size={40} /><p className="eyebrow">404 · Không tìm thấy</p><h1>Đường dẫn không còn ở đây</h1><p>Hãy trở về trang chủ để tiếp tục.</p><Link className="button button--primary" to="/">Về trang chủ</Link></div></main>
}
