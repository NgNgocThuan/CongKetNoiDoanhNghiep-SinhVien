import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/Button'
export function Pagination({ page, pages, total, onChange }: { page: number; pages: number; total: number; onChange: (page: number) => void }) {
  return <nav className="pagination" aria-label="Phân trang"><p><strong>{total}</strong> kết quả <span className="pagination__separator">·</span> Trang {pages === 0 ? 0 : page}/{pages}</p>
    <div><Button variant="secondary" size="sm" disabled={page <= 1} aria-label="Trang trước" onClick={() => onChange(page - 1)}><ChevronLeft size={16} /></Button>
    <Button variant="secondary" size="sm" disabled={page >= pages} aria-label="Trang sau" onClick={() => onChange(page + 1)}><ChevronRight size={16} /></Button></div>
  </nav>
}
