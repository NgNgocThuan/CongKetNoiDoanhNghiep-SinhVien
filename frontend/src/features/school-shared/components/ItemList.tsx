import type { Key, ReactNode } from 'react'
import { Empty, Flex } from 'antd'

export interface ItemView {
  title: ReactNode
  description?: ReactNode
  actions?: ReactNode
}

/** Danh sách dòng đơn giản có viền (thay cho List của Ant Design vốn sắp bị loại bỏ). */
export default function ItemList<T>({
  items,
  rowKey,
  render,
  empty,
}: {
  items: T[]
  rowKey: (item: T) => Key
  render: (item: T) => ItemView
  empty: string
}) {
  if (items.length === 0) {
    return (
      <div style={{ border: '1px solid #E2E8F0', borderRadius: 12, padding: 16 }}>
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={empty} />
      </div>
    )
  }
  return (
    <div style={{ border: '1px solid #E2E8F0', borderRadius: 12, overflow: 'hidden' }}>
      {items.map((item, index) => {
        const view = render(item)
        return (
          <Flex
            key={rowKey(item)}
            justify="space-between"
            align="flex-start"
            gap={12}
            style={{ padding: '12px 16px', borderTop: index === 0 ? 'none' : '1px solid #E2E8F0' }}
          >
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 600 }}>{view.title}</div>
              {view.description && <div style={{ color: '#64748B', marginTop: 2 }}>{view.description}</div>}
            </div>
            {view.actions && <div style={{ flexShrink: 0 }}>{view.actions}</div>}
          </Flex>
        )
      })}
    </div>
  )
}
