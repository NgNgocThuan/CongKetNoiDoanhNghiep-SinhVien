import type { ReactNode } from 'react'
import { Tag } from 'antd'

export type Tone = 'success' | 'pending' | 'error' | 'info' | 'neutral'

const TONES: Record<Tone, { color: string; bg: string }> = {
  success: { color: '#16A34A', bg: '#DCFCE7' },
  pending: { color: '#D97706', bg: '#FEF3C7' },
  error: { color: '#DC2626', bg: '#FEE2E2' },
  info: { color: '#1E40AF', bg: '#DBEAFE' },
  neutral: { color: '#64748B', bg: '#F1F5F9' },
}

/** Huy hiệu trạng thái bo tròn: luôn có chữ (không chỉ dựa vào màu). */
export function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  const { color, bg } = TONES[tone]
  return (
    <Tag
      style={{ color, background: bg, border: 'none', borderRadius: 9999, padding: '2px 12px', fontWeight: 600, marginInlineEnd: 0 }}
    >
      <span
        style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: color, marginRight: 6 }}
      />
      {children}
    </Tag>
  )
}

export function ActiveBadge({ active }: { active: boolean }) {
  return active ? <Badge tone="success">Đang hoạt động</Badge> : <Badge tone="neutral">Ngừng hoạt động</Badge>
}
