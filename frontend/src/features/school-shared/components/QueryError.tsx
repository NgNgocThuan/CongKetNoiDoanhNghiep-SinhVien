import { Alert, Button } from 'antd'
import { getErrorMessage } from '@/features/school-shared/http'

/** Khối báo lỗi tải dữ liệu kèm nút thử lại. */
export default function QueryError({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <Alert
      type="error"
      showIcon
      title="Không tải được dữ liệu"
      description={getErrorMessage(error)}
      action={
        onRetry ? (
          <Button size="small" onClick={onRetry}>
            Thử lại
          </Button>
        ) : undefined
      }
      style={{ marginBottom: 16 }}
    />
  )
}
