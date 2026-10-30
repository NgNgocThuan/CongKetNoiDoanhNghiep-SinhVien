import { Link } from 'react-router-dom'
export function Brand({ to = '/' }: { to?: string }) {
  return <Link to={to} className="brand" aria-label="Student Connect - Trang chủ"><span className="brand__symbol" aria-hidden="true">s<span>c</span></span><span>Student<span className="brand__second">Connect</span></span></Link>
}
