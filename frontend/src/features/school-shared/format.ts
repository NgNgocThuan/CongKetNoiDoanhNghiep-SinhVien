import dayjs from 'dayjs'

/** dd/MM/yyyy; rỗng/null hiển thị "—" (không đổi thành 0 hay ngày mặc định). */
export function formatDate(value?: string | null): string {
  if (!value) return '—'
  const d = dayjs(value)
  return d.isValid() ? d.format('DD/MM/YYYY') : '—'
}

export function formatDateTime(value?: string | null): string {
  if (!value) return '—'
  const d = dayjs(value)
  return d.isValid() ? d.format('DD/MM/YYYY HH:mm') : '—'
}

/** Điểm/số thập phân từ API (chuỗi hoặc số); null giữ "—". */
export function formatScore(value?: string | number | null): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(2).replace(/\.?0+$/, '') : '—'
}
