import { Link } from 'react-router-dom'
import { GraduationCap } from 'lucide-react'

export function Brand({ to = '/' }: { to?: string }) {
  return (
    <Link to={to} className="brand" aria-label="Student Connect - Trang chủ">
      <span className="brand__symbol" aria-hidden="true">
        <GraduationCap size={20} className="brand__icon" strokeWidth={2.2} />
      </span>
      <span className="brand__text">
        Student<span className="brand__second">Connect</span>
      </span>
    </Link>
  )
}
