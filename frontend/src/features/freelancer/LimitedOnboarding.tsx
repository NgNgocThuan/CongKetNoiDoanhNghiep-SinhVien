import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { publicHttp } from '@/lib/http'
import { CompanyVerificationFlow } from './CompanyVerificationFlow'
import { errorText } from './messages'
import { unwrap } from './api'
import { Notice, PageHeading, Panel } from './ui'

export default function LimitedOnboarding() {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    if (!token) return
    const timer = window.setTimeout(() => { setToken(''); setError('Phiên đã hết hạn. Mở lại phiên để tiếp tục.') }, 15 * 60 * 1000)
    return () => window.clearTimeout(timer)
  }, [token])
  return <main className="fl fl-result">
    <PageHeading title="Xác minh doanh nghiệp & quyền đại diện" subtitle="Không bắt buộc ký MOU. Hồ sơ được xét duyệt bởi một admin." />
    <Panel title="Phiên hoàn thiện hồ sơ">
      {!token ? <form onSubmit={async event => {
        event.preventDefault()
        const data = new FormData(event.currentTarget)
        setBusy(true); setError('')
        try {
          const result = unwrap((await publicHttp.post('/auth/onboarding-token', { email: data.get('email'), password: data.get('password') })).data)
          setToken(String(result.access_token))
        } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
      }}>
        <label>Email đăng ký<input name="email" type="email" required autoComplete="username" /></label>
        <label>Mật khẩu<input name="password" type="password" required autoComplete="current-password" /></label>
        <button className="fl-button" disabled={busy}>{busy ? 'Đang mở…' : 'Mở hồ sơ chờ duyệt'}</button>
      </form> : <><Notice>Phiên chỉ dùng để xác minh email, gửi hồ sơ và theo dõi kết quả trong 15 phút.</Notice><button className="fl-button secondary" onClick={() => setToken('')}>Đóng phiên</button></>}
      {error && <Notice danger>{error}</Notice>}
      <p><Link to="/login">Về đăng nhập</Link> · <Link to="/register-company">Đăng ký doanh nghiệp</Link></p>
    </Panel>
    {token && <Panel title="Hồ sơ xác minh"><CompanyVerificationFlow key={token} token={token} /></Panel>}
  </main>
}
