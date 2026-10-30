import type { ReactNode } from 'react'
import { EmptyState } from './States'

export interface Column<T> { id: string; header: string; render: (row: T) => ReactNode }
export function DataTable<T>({ rows, columns, rowKey, caption }: { rows: T[]; columns: Column<T>[]; rowKey: (row: T) => string | number; caption: string }) {
  if (!rows.length) return <EmptyState description="Thử thay đổi bộ lọc hoặc quay lại sau." />
  return <div className="table-scroll"><table><caption className="sr-only">{caption}</caption>
    <thead><tr>{columns.map(col => <th key={col.id} scope="col">{col.header}</th>)}</tr></thead>
    <tbody>{rows.map(row => <tr key={rowKey(row)}>{columns.map(col => <td key={col.id}>{col.render(row)}</td>)}</tr>)}</tbody>
  </table></div>
}
