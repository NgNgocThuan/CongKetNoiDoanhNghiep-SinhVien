/**
 * Khung giao diện admin (thanh bên + thanh trên) theo thiết kế Stitch.
 * TẠM THỜI: Thuận (khung ứng dụng) sẽ thay/hoàn thiện; các trang chỉ cần được đặt trong <Outlet />.
 * Chỉ liệt kê các mục đã có trang thật; thêm mục mới khi module của người khác sẵn sàng.
 */
import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Avatar, Button, Drawer, Dropdown, Flex, Grid, Layout, Menu, Typography } from 'antd'
import {
  AppstoreOutlined,
  BookOutlined,
  CalendarOutlined,
  LogoutOutlined,
  MenuOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useAuth } from '@/features/auth/AuthProvider'

const { Sider, Header, Content } = Layout

const MENU = [
  { key: '/admin/students', icon: <UserOutlined />, label: 'Sinh viên' },
  { key: '/admin/lecturers', icon: <TeamOutlined />, label: 'Giảng viên' },
  { key: '/admin/internship-terms', icon: <CalendarOutlined />, label: 'Đợt thực tập' },
  { key: '/admin/catalog', icon: <AppstoreOutlined />, label: 'Danh mục' },
]

function Brand() {
  return (
    <div style={{ padding: '20px 24px 12px' }}>
      <Flex align="center" gap={10}>
        <BookOutlined style={{ fontSize: 24, color: '#1E40AF' }} />
        <div>
          <div className="sc-display" style={{ fontSize: 20, fontWeight: 700, color: '#1E40AF', lineHeight: 1.1 }}>
            Student Connect
          </div>
          <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', color: '#0F766E' }}>PORTAL 3 BÊN</div>
        </div>
      </Flex>
      <div style={{ margin: '20px 0 4px', fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', color: '#64748B' }}>
        NHÀ TRƯỜNG / ADMIN
      </div>
    </div>
  )
}

export default function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const screens = Grid.useBreakpoint()
  const isDesktop = screens.lg ?? true
  const [drawerOpen, setDrawerOpen] = useState(false)

  // Trang con (vd /admin/students/12) vẫn sáng đúng mục cha
  const selected = MENU.find((m) => location.pathname.startsWith(m.key))?.key

  const menu = (
    <Menu
      mode="inline"
      selectedKeys={selected ? [selected] : []}
      items={MENU}
      style={{ border: 'none', padding: '0 12px', background: 'transparent' }}
      onClick={({ key }) => {
        navigate(key)
        setDrawerOpen(false)
      }}
    />
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isDesktop ? (
        <Sider
          width={264}
          theme="light"
          style={{ borderRight: '1px solid #E2E8F0', position: 'sticky', top: 0, height: '100vh', overflow: 'auto' }}
        >
          <Brand />
          {menu}
        </Sider>
      ) : (
        <Drawer
          placement="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          size={280}
          styles={{ body: { padding: 0 } }}
        >
          <Brand />
          {menu}
        </Drawer>
      )}
      <Layout style={{ minWidth: 0 }}>
        <Header
          style={{
            background: '#fff',
            borderBottom: '1px solid #E2E8F0',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}
        >
          <Flex align="center" gap={12}>
            {!isDesktop && (
              <Button
                type="text"
                aria-label="Mở menu"
                icon={<MenuOutlined />}
                onClick={() => setDrawerOpen(true)}
              />
            )}
            <Typography.Text strong style={{ color: '#475569' }}>
              Cổng liên kết thực tập & tuyển dụng doanh nghiệp
            </Typography.Text>
          </Flex>
          <Dropdown
            menu={{
              items: [{ key: 'logout', icon: <LogoutOutlined />, label: 'Đăng xuất', onClick: logout }],
            }}
            trigger={['click']}
          >
            <Flex align="center" gap={10} style={{ cursor: 'pointer' }}>
              <div style={{ textAlign: 'right', lineHeight: 1.2 }}>
                <div style={{ fontWeight: 600 }}>Quản trị nhà trường</div>
                <div style={{ fontSize: 12, color: '#0F766E', fontWeight: 600 }}>ADMIN</div>
              </div>
              <Avatar style={{ background: '#1E40AF' }} icon={<UserOutlined />} />
            </Flex>
          </Dropdown>
        </Header>
        <Content>
          <div className="sc-page">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}
