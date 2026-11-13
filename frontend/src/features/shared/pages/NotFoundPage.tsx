import { Link } from 'react-router-dom'
import { ArrowLeft, Compass } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <main className="center-page">
      <div className="state">
        <span className="state__icon">
          <Compass size={32} />
        </span>
        <p className="eyebrow">404 · Không tìm thấy trang</p>
        <h1>Đường dẫn không tồn tại hoặc đã thay đổi</h1>
        <p>Trang bạn đang tìm kiếm không tồn tại hoặc bạn không có quyền truy cập. Vui lòng quay lại trang chủ.</p>
        <Link className="button button--primary" to="/">
          <ArrowLeft size={16} />
          <span>Về trang chủ</span>
        </Link>
      </div>
    </main>
  )
}
