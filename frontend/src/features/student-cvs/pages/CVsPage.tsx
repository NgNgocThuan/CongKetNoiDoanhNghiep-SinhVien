import { useStudentAction } from '@/features/student-jobs/useStudentAction'
import { dateText } from '@/features/student-jobs/format'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileText, Plus, Star, Download } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/States'
import { downloadFile } from '@/utils/download'
import {
  StudentPage,
  QueryState,
  Feedback,
} from '@/features/student-jobs/components/StudentUI'
import { cvsApi } from '../api'
import { CVEditor } from '../components/CVEditor'
import { CVAnalysis, CVContent } from '../components/CVAnalysis'
import type { CV } from '../types'
export default function CVsPage() {
  const query = useQuery({
    queryKey: ['student-cvs'],
    queryFn: ({ signal }) => cvsApi.list(signal),
  })
  const [editor, setEditor] = useState<CV | null | undefined>(),
    [remove, setRemove] = useState<CV | null>(null),
    [preview, setPreview] = useState<CV | null>(null),
    [selected, setSelected] = useState<number | null>(null)
  const action = useStudentAction(['student-cvs']),
    active =
      query.data?.find((cv) => cv.id === selected) ||
      query.data?.find((cv) => cv.is_default) ||
      query.data?.[0]
  return (
    <StudentPage
      title="CV của tôi"
      description="Chuẩn bị hồ sơ cho cơ hội tiếp theo. Mỗi phiên bản kể một câu chuyện về bạn."
      actions={
        <>
          <Button onClick={() => setEditor(null)}>
            <Plus size={16} />
            Tạo CV online
          </Button>
        </>
      }
    >
      <QueryState query={query} />
      <Feedback {...action} />
      {query.data && (
        <>
          {!query.data.length ? (
            <EmptyState
              title="CV đầu tiên, bước khởi đầu mới"
              description="Tạo CV từ thông tin nhà trường và bổ sung năng lực của bạn."
            />
          ) : (
            <div className="student-split">
              <div className="student-stack">
                {query.data.map((cv) => (
                  <article
                    className="student-panel student-cv-card"
                    key={cv.id}
                  >
                    <div className="student-card-top">
                      <span className="student-logo">
                        <FileText />
                      </span>
                      <div>
                        <h2>{cv.title}</h2>
                        <p className="muted">
                          {cv.type === 'ONLINE'
                            ? 'CV trực tuyến'
                            : 'File tải lên'}{' '}
                          · {dateText(cv.updated_at)}
                        </p>
                      </div>
                      {cv.is_default && (
                        <span className="student-tag teal">
                          <Star size={12} />
                          Mặc định
                        </span>
                      )}
                    </div>
                    <p className="muted">
                      {cv.parsed_json
                        ? 'Đã phân tích CV'
                        : 'Chưa có phân tích AI'}
                    </p>
                    <div className="student-actions">
                      <Button variant="secondary" onClick={() => setEditor(cv)}>
                        {cv.type === 'ONLINE' ? 'Chỉnh sửa' : 'Đổi tiêu đề'}
                      </Button>
                      {cv.type === 'ONLINE' && (
                        <Button
                          variant="secondary"
                          onClick={() => setPreview(cv)}
                        >
                          Xem trước
                        </Button>
                      )}
                      <Button
                        variant="secondary"
                        pending={action.pending}
                        onClick={() =>
                          void action.run(
                            () =>
                              downloadFile(
                                '/api/v1/cvs/' + cv.id + '/download',
                                'cv-' +
                                  cv.id +
                                  (cv.type === 'ONLINE'
                                    ? '.json'
                                    : cv.file_url
                                          ?.toLowerCase()
                                          .endsWith('.docx')
                                      ? '.docx'
                                      : '.pdf'),
                              ),
                            'Đã tải CV.',
                          )
                        }
                      >
                        <Download size={14} />
                        {cv.type === 'ONLINE' ? 'Tải JSON' : 'Tải file'}
                      </Button>
                      {!cv.is_default && (
                        <Button
                          variant="secondary"
                          pending={action.pending}
                          onClick={() =>
                            void action.run(() => cvsApi.default(cv.id))
                          }
                        >
                          Đặt mặc định
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        onClick={() => setSelected(cv.id)}
                      >
                        Xem phân tích
                      </Button>
                      <Button variant="ghost" onClick={() => setRemove(cv)}>
                        Xóa CV
                      </Button>
                    </div>
                  </article>
                ))}
              </div>
              {active && <CVAnalysis key={active.id} cv={active} />}
            </div>
          )}
        </>
      )}
      <Dialog
        open={editor !== undefined}
        onOpenChange={(open) => {
          if (!open) setEditor(undefined)
        }}
        title={editor ? 'Chỉnh sửa CV' : 'Tạo CV online'}
      >
        {editor !== undefined && (
          <CVEditor
            key={editor?.id || 'new'}
            cv={editor || undefined}
            onDone={() => setEditor(undefined)}
          />
        )}
      </Dialog>
      <Dialog
        open={preview !== null}
        onOpenChange={(open) => {
          if (!open) setPreview(null)
        }}
        title={preview?.title || 'Xem trước CV'}
      >
        <CVContent value={preview?.content_json} />
      </Dialog>
      <ConfirmDialog
        open={remove !== null}
        onOpenChange={(open) => {
          if (!open) setRemove(null)
        }}
        title="Xóa CV này?"
        description="CV sẽ được ẩn khỏi danh sách. Các đơn đã nộp vẫn giữ bản CV tại thời điểm ứng tuyển."
        danger
        confirmLabel="Xóa CV"
        onConfirm={async () => {
          await cvsApi.remove(remove!.id)
          await action.run(async () => undefined)
        }}
      />
    </StudentPage>
  )
}
