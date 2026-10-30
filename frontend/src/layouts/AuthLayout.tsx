import { Outlet } from 'react-router-dom'
import { ArrowUpRight, BriefcaseBusiness, GraduationCap, School } from 'lucide-react'
import { Brand } from '@/components/common/Brand'

export function AuthLayout() {
  return <div className="auth-layout">
    <section className="auth-form-side"><header className="auth-header"><Brand /><span className="auth-header__label">CỔNG KẾT NỐI NGHỀ NGHIỆP</span></header>
      <main className="auth-form-area"><Outlet /></main><footer className="auth-footer">Student Connect <span>Học tập hôm nay. Cơ hội ngày mai.</span></footer>
    </section>
    <aside className="auth-story" aria-label="Giới thiệu Student Connect"><div className="auth-story__grid" aria-hidden="true" />
      <div className="auth-story__top"><span className="pill-light"><span className="dot" /> CÙNG NHAU TIẾN XA</span><ArrowUpRight size={24} /></div>
      <div className="auth-story__content"><p className="eyebrow">MỖI KẾT NỐI, MỘT KHỞI ĐẦU</p><h2>Cơ hội đúng.<br />Tương lai <em>rộng mở.</em></h2><p>Một không gian chung để sinh viên tìm cơ hội, doanh nghiệp tìm nhân tài và nhà trường đồng hành.</p>
        <div className="connection-cards"><div><GraduationCap size={22} /><span>Sinh viên<strong>Khám phá tiềm năng</strong></span></div><div><BriefcaseBusiness size={22} /><span>Doanh nghiệp<strong>Kết nối nhân tài</strong></span></div><div><School size={22} /><span>Nhà trường<strong>Đồng hành phát triển</strong></span></div></div>
      </div>
      <p className="auth-story__bottom"><span className="story-line" /> Từ giảng đường đến hành trình nghề nghiệp.</p>
    </aside>
  </div>
}
