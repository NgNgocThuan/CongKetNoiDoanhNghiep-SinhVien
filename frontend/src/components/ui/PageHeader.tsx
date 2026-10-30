import type { ReactNode } from 'react'
import { Flex, Typography } from 'antd'

interface Props {
  eyebrow?: string
  title: ReactNode
  subtitle?: ReactNode
  extra?: ReactNode
  meta?: ReactNode
}

/** Đầu trang theo thiết kế: nhãn chip, tiêu đề lớn, mô tả và nhóm nút bên phải. */
export default function PageHeader({ eyebrow, title, subtitle, extra, meta }: Props) {
  return (
    <div className="sc-card" style={{ padding: 24, marginBottom: 24 }}>
      <Flex justify="space-between" align="flex-start" gap={16} wrap>
        <div style={{ minWidth: 0, flex: '1 1 320px' }}>
          {eyebrow && <span className="sc-eyebrow">{eyebrow}</span>}
          <Typography.Title
            level={1}
            style={{ margin: '8px 0 4px', fontSize: 'clamp(1.5rem, 3vw, 2.25rem)', color: '#00288E' }}
          >
            {title}
          </Typography.Title>
          {subtitle && <Typography.Text type="secondary">{subtitle}</Typography.Text>}
          {meta && <div style={{ marginTop: 12 }}>{meta}</div>}
        </div>
        {extra && (
          <Flex gap={8} wrap>
            {extra}
          </Flex>
        )}
      </Flex>
    </div>
  )
}
