/** TẠM THỜI: trang đăng nhập tối thiểu (Quang sẽ thay bằng trang A01 theo thiết kế). */
import { useState } from 'react'
import { Alert, Button, Form, Input, Typography } from 'antd'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { getErrorMessage } from '@/lib/http'
import { useAuth } from './AuthProvider'

interface LoginForm {
  email: string
  password: string
}

export default function LoginPage() {
  const { token, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const from = (location.state as { from?: string } | null)?.from ?? '/admin'

  if (token) return <Navigate to={from} replace />

  const onFinish = async (values: LoginForm) => {
    setSubmitting(true)
    setError(null)
    try {
      await login(values.email.trim(), values.password)
      navigate(from, { replace: true })
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <div className="sc-card" style={{ width: '100%', maxWidth: 400, padding: 32 }}>
        <Typography.Title level={2} style={{ color: '#1E40AF', marginTop: 0, marginBottom: 4 }}>
          Student Connect
        </Typography.Title>
        <Typography.Paragraph type="secondary">Đăng nhập để tiếp tục</Typography.Paragraph>
        {error && <Alert type="error" showIcon title={error} style={{ marginBottom: 16 }} />}
        <Form<LoginForm> layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item name="email" label="Email" rules={[{ required: true, message: 'Vui lòng nhập email' }]}>
            <Input autoComplete="username" placeholder="admin@school.edu.vn" />
          </Form.Item>
          <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={submitting}>
            Đăng nhập
          </Button>
        </Form>
      </div>
    </div>
  )
}
