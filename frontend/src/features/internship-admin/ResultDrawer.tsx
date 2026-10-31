/**
 * Chi tiết kết quả thực tập của một sinh viên: đánh giá của doanh nghiệp (chỉ xem), nhận xét + điểm của nhà trường
 * (admin nhập thay giảng viên) và xác nhận PASSED/FAILED. Sau khi xác nhận mọi thao tác bị khóa.
 */
import { Alert, App, Button, Descriptions, Drawer, Flex, Form, Input, InputNumber, Popconfirm, Typography } from 'antd'
import { formatDateTime, formatScore } from '@/features/school-shared/format'
import { getErrorMessage } from '@/features/school-shared/http'
import { useConfirmResult, useSaveLecturerReview } from './api'
import { ResultBadge } from './badges'
import { hasReviewContent, isResultLocked } from './rules'
import type { InternshipResult } from './types'

interface FormValues {
  comment: string
  score: number | null
}

export default function ResultDrawer({ result, onClose }: { result: InternshipResult | null; onClose: () => void }) {
  return result ? <ResultDrawerContent key={result.id} result={result} onClose={onClose} /> : null
}

function ResultDrawerContent({ result, onClose }: { result: InternshipResult; onClose: () => void }) {
  const { message } = App.useApp()
  const [form] = Form.useForm<FormValues>()
  const saveReview = useSaveLecturerReview()
  const confirm = useConfirmResult()
  const locked = result ? isResultLocked(result) : true

  const onSave = async () => {
    if (!result) return
    const values = await form.validateFields()
    try {
      await saveReview.mutateAsync({
        resultId: result.id,
        comment: values.comment?.trim() || null,
        score: values.score ?? null,
      })
      message.success('Đã lưu nhận xét của nhà trường')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const onConfirm = async (outcome: 'PASSED' | 'FAILED') => {
    if (!result) return
    try {
      await confirm.mutateAsync({ resultId: result.id, result: outcome })
      message.success(outcome === 'PASSED' ? 'Đã xác nhận: Đạt' : 'Đã xác nhận: Không đạt')
      onClose()
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Drawer
      open={result !== null}
      onClose={onClose}
      size={620}
      destroyOnHidden
      title={result ? `${result.student_code} - ${result.student_name}` : ''}
    >
      {result && (
        <Flex vertical gap={24}>
          <Descriptions size="small" column={1} bordered>
            <Descriptions.Item label="Kết quả hiện tại">
              <ResultBadge result={result.result} />
            </Descriptions.Item>
            <Descriptions.Item label="Giảng viên hướng dẫn">{result.lecturer_name ?? 'Chưa phân công'}</Descriptions.Item>
            {result.company_id && !locked && <Descriptions.Item label="Link đánh giá cho doanh nghiệp">
              <Typography.Text copyable>{`${window.location.origin}/company/evaluations/${result.id}`}</Typography.Text>
              <Typography.Paragraph type="secondary">Gửi link này cho doanh nghiệp được gắn với kết quả. Doanh nghiệp cần đăng nhập đúng tài khoản để đánh giá.</Typography.Paragraph>
            </Descriptions.Item>}
            {result.confirmed_at && (
              <Descriptions.Item label="Xác nhận lúc">{formatDateTime(result.confirmed_at)}</Descriptions.Item>
            )}
          </Descriptions>

          <div>
            <Typography.Title level={4}>Đánh giá của doanh nghiệp</Typography.Title>
            {result.company_evaluation ? (
              <Descriptions size="small" column={1} bordered>
                <Descriptions.Item label="Doanh nghiệp">{result.company_name ?? '—'}</Descriptions.Item>
                <Descriptions.Item label="Điểm (thang 10)">{formatScore(result.company_score)}</Descriptions.Item>
                <Descriptions.Item label="Gửi lúc">{formatDateTime(result.evaluated_at)}</Descriptions.Item>
                <Descriptions.Item label="Nhận xét">
                  <div style={{ whiteSpace: 'pre-wrap' }}>{result.company_evaluation}</div>
                </Descriptions.Item>
              </Descriptions>
            ) : (
              <Alert type="info" showIcon title="Doanh nghiệp chưa gửi đánh giá cho sinh viên này." />
            )}
          </div>

          <div>
            <Typography.Title level={4}>Nhận xét của nhà trường</Typography.Title>
            {locked && (
              <Alert
                type="success"
                showIcon
                title="Kết quả đã được xác nhận nên không thể chỉnh sửa."
                style={{ marginBottom: 12 }}
              />
            )}
            <Form
              key={`${result.id}-${result.result}`}
              form={form}
              layout="vertical"
              disabled={locked}
              initialValues={{
                comment: result.lecturer_comment ?? '',
                score: result.lecturer_score === null ? null : Number(result.lecturer_score),
              }}
            >
              <Form.Item name="comment" label="Nhận xét">
                <Input.TextArea rows={4} maxLength={5000} showCount />
              </Form.Item>
              <Form.Item name="score" label="Điểm (thang 10)">
                <InputNumber min={0} max={10} step={0.1} style={{ width: 160 }} />
              </Form.Item>
              <Form.Item shouldUpdate noStyle>
                {() => {
                  const v = form.getFieldsValue()
                  return (
                    <Button
                      type="primary"
                      loading={saveReview.isPending}
                      disabled={locked || !hasReviewContent(v.comment, v.score)}
                      onClick={onSave}
                    >
                      Lưu nhận xét
                    </Button>
                  )
                }}
              </Form.Item>
            </Form>
          </div>

          {!locked && (
            <div>
              <Typography.Title level={4}>Xác nhận kết quả</Typography.Title>
              <Typography.Paragraph type="secondary">
                Sau khi xác nhận, đánh giá và nhận xét bị khóa và sinh viên được thông báo.
                {!result.company_evaluation && ' Lưu ý: doanh nghiệp chưa gửi đánh giá.'}
              </Typography.Paragraph>
              <Flex gap={8} wrap>
                <Popconfirm
                  title="Xác nhận sinh viên ĐẠT?"
                  description="Thao tác này không thể hoàn tác."
                  okText="Xác nhận Đạt"
                  cancelText="Hủy"
                  onConfirm={() => onConfirm('PASSED')}
                >
                  <Button type="primary" style={{ background: '#16A34A' }} loading={confirm.isPending}>
                    Xác nhận Đạt
                  </Button>
                </Popconfirm>
                <Popconfirm
                  title="Xác nhận sinh viên KHÔNG ĐẠT?"
                  description="Thao tác này không thể hoàn tác."
                  okText="Xác nhận Không đạt"
                  okButtonProps={{ danger: true }}
                  cancelText="Hủy"
                  onConfirm={() => onConfirm('FAILED')}
                >
                  <Button danger loading={confirm.isPending}>
                    Xác nhận Không đạt
                  </Button>
                </Popconfirm>
              </Flex>
            </div>
          )}
        </Flex>
      )}
    </Drawer>
  )
}
