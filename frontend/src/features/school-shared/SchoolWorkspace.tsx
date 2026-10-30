import { App, ConfigProvider } from 'antd'
import viVN from 'antd/locale/vi_VN'
import type { ThemeConfig } from 'antd'
import { Outlet } from 'react-router-dom'
import 'dayjs/locale/vi'
import './school.css'

const theme: ThemeConfig = {
  token: {
    colorPrimary: '#354d8b', colorInfo: '#354d8b', colorSuccess: '#14745a',
    colorWarning: '#b76a15', colorError: '#bd3545', colorTextBase: '#172840',
    colorTextSecondary: '#6c7c91', colorBorder: '#e5ebf3', colorBgLayout: '#f6f8fc',
    borderRadius: 10, fontFamily: 'Inter, "Be Vietnam Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 14, controlHeight: 40,
  },
  components: { Table: { headerBg: '#f6f8fc', headerColor: '#586b85' }, Card: { borderRadiusLG: 14 }, Modal: { borderRadiusLG: 16 } },
}
// Presentation providers only: auth, router, QueryClient and AdminLayout stay in the shared app.
export default function SchoolWorkspace() {
  return <ConfigProvider locale={viVN} theme={theme}><App className="school-workspace"><Outlet /></App></ConfigProvider>
}
