import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCheck, Bell } from 'lucide-react'
import { notificationsApi } from '../api/notifications.api'
import { PageHeader } from '@/components/common/PageHeader'
import { Pagination } from '@/components/common/Pagination'
import { EmptyState, ErrorState, LoadingState } from '@/components/common/States'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/utils/format'

export default function NotificationsPage() {
  const [page, setPage] = useState(1)
  const client = useQueryClient()
  const query = useQuery({ queryKey: ['notifications', 'list', page], queryFn: ({ signal }) => notificationsApi.list(page, signal) })
  const read = useMutation({ mutationFn: (id: number | 'all') => id === 'all' ? notificationsApi.readAll() : notificationsApi.read(id),
    onSuccess: () => client.invalidateQueries({ queryKey: ['notifications'] }) })
  return <><PageHeader eyebrow="GIỮ KẾT NỐI" title="Thông báo" description="Theo dõi những cập nhật liên quan đến bạn." actions={<Button variant="secondary" pending={read.isPending} onClick={() => read.mutate('all')}><CheckCheck size={17} />Đánh dấu tất cả đã đọc</Button>} /><Card className="notification-card">
    {read.isError && <p className="form-error" role="alert">{read.error.message}</p>}
    {query.isPending ? <LoadingState /> : query.isError ? <ErrorState message={query.error.message} onRetry={() => void query.refetch()} /> : query.data.items.length === 0 ? <EmptyState title="Bạn đã cập nhật mọi thông tin" description="Thông báo mới sẽ xuất hiện tại đây." /> : <><ul className="notification-list">{query.data.items.map(item => <li key={item.id} className={item.is_read ? '' : 'is-unread'}><span className="notification-list__icon"><Bell size={19} /></span><div><h2>{item.title}</h2>{item.content && <p>{item.content}</p>}<time dateTime={item.created_at}>{formatDate(item.created_at)}</time></div>{!item.is_read && <Button size="sm" variant="ghost" disabled={read.isPending} onClick={() => read.mutate(item.id)}>Đã đọc</Button>}</li>)}</ul><Pagination page={page} pages={query.data.pages} total={query.data.total} onChange={setPage} /></>}
  </Card></>
}
