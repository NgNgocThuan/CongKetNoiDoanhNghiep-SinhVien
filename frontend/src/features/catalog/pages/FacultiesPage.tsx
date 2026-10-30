import { useSearchParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { DataTable } from '@/components/common/DataTable'
import { Pagination } from '@/components/common/Pagination'
import { ErrorState, LoadingState } from '@/components/common/States'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { useFaculties } from '../hooks/useFaculties'
import type { Column } from '@/components/common/DataTable'
import type { Faculty } from '../types/catalog.types'

const columns: Column<Faculty>[] = [
  { id: 'code', header: 'Mã khoa', render: row => <span className="table-code">{row.code}</span> },
  { id: 'name', header: 'Tên khoa', render: row => <strong>{row.name}</strong> },
  { id: 'status', header: 'Trạng thái', render: row => <Badge tone={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Đang hoạt động' : 'Ngừng hoạt động'}</Badge> },
]
export default function FacultiesPage() {
  const [params, setParams] = useSearchParams()
  const candidate = Number(params.get('page') || 1)
  const page = Number.isInteger(candidate) && candidate > 0 ? candidate : 1, q = params.get('q') || ''
  const query = useFaculties({ page, size: 10, q })
  function search(value: string) { setParams(value ? { q: value, page: '1' } : {}, { replace: true }) }
  return <><PageHeader eyebrow="DỮ LIỆU NHÀ TRƯỜNG" title="Danh mục khoa" description="Tra cứu các khoa đang hoạt động trong hệ thống." /><Card className="table-card"><div className="table-toolbar"><div><h2>Các khoa</h2><p className="muted">Danh mục do nhà trường quản lý.</p></div><label className="search-input"><Search size={17} aria-hidden="true" /><span className="sr-only">Tìm khoa theo tên hoặc mã</span><Input value={q} onChange={event => search(event.target.value)} placeholder="Tìm tên hoặc mã khoa…" /></label></div>
    {query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : <><DataTable rows={query.data.items} columns={columns} rowKey={row => row.id} caption="Danh sách khoa" /><Pagination page={page} pages={query.data.pages} total={query.data.total} onChange={next => setParams({ q, page: String(next) })} /></>}
  </Card></>
}
