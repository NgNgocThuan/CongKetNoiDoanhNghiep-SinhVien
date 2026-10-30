import type { ThemeConfig } from 'antd'

/** Design tokens lấy từ DESIGN.md (Student Connect Portal). */
export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#1E40AF',
    colorInfo: '#1E40AF',
    colorSuccess: '#16A34A',
    colorWarning: '#D97706',
    colorError: '#DC2626',
    colorTextBase: '#0F172A',
    colorTextSecondary: '#64748B',
    colorBorder: '#E2E8F0',
    colorBgLayout: '#F8FAFC',
    colorBgContainer: '#FFFFFF',
    borderRadius: 12,
    fontFamily: "'Be Vietnam Pro', system-ui, -apple-system, 'Segoe UI', sans-serif",
    fontSize: 14,
    controlHeight: 40,
  },
  components: {
    Table: { headerBg: '#F8FAFC', headerColor: '#64748B', rowHoverBg: '#F8FAFC' },
    Card: { borderRadiusLG: 16 },
    Modal: { borderRadiusLG: 16 },
    Menu: { itemBorderRadius: 9999, itemSelectedBg: '#1E40AF', itemSelectedColor: '#FFFFFF' },
    Tabs: { itemSelectedColor: '#1E40AF' },
  },
}

export const ACCENT = '#0F766E'
