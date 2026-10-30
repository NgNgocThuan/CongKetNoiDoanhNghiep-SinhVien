/**
 * Admin: chi tiết sinh viên. Tách rõ hai nguồn dữ liệu:
 *  - Dữ liệu nhà trường (chính thức, nhà trường được sửa)
 *  - Thông tin tự khai (do sinh viên nhập, chỉ xem; chứng chỉ tự khai có thể được nhà trường xác thực)
 */
import { useState, type ReactNode } from 'react'
import { App, Button, Descriptions, Empty, Flex, Popconfirm, Result, Skeleton, Table, Tabs, Typography } from 'antd'
import ItemList from '@/features/school-shared/components/ItemList'
import { ArrowLeftOutlined, EditOutlined, MailOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import PageHeader from '@/features/school-shared/components/PageHeader'
import QueryError from '@/features/school-shared/components/QueryError'
import { Badge } from '@/features/school-shared/components/StatusTag'
import { formatDate } from '@/features/school-shared/format'
import { getErrorMessage, getErrorStatus } from '@/features/school-shared/http'
import { useIssueAccount, useStudentDetail, useVerifyCertificate } from './api'
import AchievementSection from './AchievementSection'
import EditAcademicModal from './EditAcademicModal'
import { AccountStatusBadge } from './labels'
import { SKILL_LEVEL_LABEL } from './labels.constants'
import type { Certificate, SelfSkill, StudentDetail } from './types'

function Source({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'neutral' }) {
  return <Badge tone={tone}>{children}</Badge>
}

function CertificateList({
  items,
  studentId,
  verifiable,
}: {
  items: Certificate[]
  studentId: number
  verifiable: boolean
}) {
  const { message } = App.useApp()
  const verify = useVerifyCertificate(studentId)
  const onVerify = async (id: number) => {
    try {
      await verify.mutateAsync(id)
      message.success('Đã xác thực chứng chỉ')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }
  return (
    <ItemList
      items={items}
      rowKey={(c) => c.id}
      empty="Chưa có chứng chỉ"
      render={(c) => ({
        title: (
          <Flex gap={8} align="center" wrap>
            <span>{c.name}</span>
            {c.source === 'SCHOOL' ? (
              <Source>Nhà trường</Source>
            ) : c.is_verified ? (
              <Badge tone="success">Đã xác thực</Badge>
            ) : (
              <Badge tone="pending">Tự khai · chờ xác thực</Badge>
            )}
          </Flex>
        ),
        description: (
          <>
            {c.issuer && <div>Đơn vị cấp: {c.issuer}</div>}
            <div>
              Cấp ngày {formatDate(c.issued_at)}
              {c.expires_at ? ` · Hết hạn ${formatDate(c.expires_at)}` : ''}
            </div>
            {c.credential_url && (
              <a href={c.credential_url} target="_blank" rel="noreferrer">
                Xem chứng chỉ
              </a>
            )}
          </>
        ),
        actions:
          verifiable && !c.is_verified ? (
            <Popconfirm
              title="Xác thực chứng chỉ này?"
              description="Nhà trường xác nhận chứng chỉ do sinh viên tự khai là đúng."
              okText="Xác thực"
              cancelText="Hủy"
              onConfirm={() => onVerify(c.id)}
            >
              <Button size="small" type="primary" loading={verify.isPending && verify.variables === c.id}>
                Xác thực
              </Button>
            </Popconfirm>
          ) : undefined,
      })}
    />
  )
}

function OfficialTab({ detail, studentId, onEdit }: { detail: StudentDetail['official']; studentId: number; onEdit: () => void }) {
  const a = detail.academic
  return (
    <Flex vertical gap={24}>
      <div>
        <Flex justify="space-between" align="center" style={{ marginBottom: 12 }}>
          <Flex gap={8} align="center">
            <Typography.Title level={4} style={{ margin: 0 }}>
              Dữ liệu học thuật
            </Typography.Title>
            <Source>Nguồn: nhà trường</Source>
          </Flex>
          <Button icon={<EditOutlined />} onClick={onEdit}>
            Sửa
          </Button>
        </Flex>
        <Descriptions bordered size="small" column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label="Mã sinh viên">{a.student_code}</Descriptions.Item>
          <Descriptions.Item label="Họ và tên">{a.full_name}</Descriptions.Item>
          <Descriptions.Item label="Ngày sinh">{formatDate(a.date_of_birth)}</Descriptions.Item>
          <Descriptions.Item label="Lớp">{a.class_name ?? '—'}</Descriptions.Item>
          <Descriptions.Item label="Khoa">{a.faculty_name}</Descriptions.Item>
          <Descriptions.Item label="Ngành">{a.major_name}</Descriptions.Item>
          <Descriptions.Item label="Khóa học">{a.cohort}</Descriptions.Item>
          <Descriptions.Item label="GPA (thang 4)">{a.gpa ?? '—'}</Descriptions.Item>
          <Descriptions.Item label="Xếp loại">{a.academic_result ?? '—'}</Descriptions.Item>
          <Descriptions.Item label="Điện thoại">{a.phone ?? '—'}</Descriptions.Item>
          <Descriptions.Item label="Email tài khoản">{a.email}</Descriptions.Item>
          <Descriptions.Item label="Tài khoản">
            <AccountStatusBadge status={a.account_status} />
          </Descriptions.Item>
        </Descriptions>
      </div>
      <AchievementSection studentId={studentId} items={detail.achievements} />
      <div>
        <Typography.Title level={4}>Chứng chỉ do nhà trường xác nhận</Typography.Title>
        <CertificateList items={detail.school_certificates} studentId={studentId} verifiable={false} />
      </div>
    </Flex>
  )
}

function SelfDeclaredTab({ data, studentId }: { data: StudentDetail['self_declared']; studentId: number }) {
  const p = data.profile
  return (
    <Flex vertical gap={24}>
      <Typography.Text type="secondary">
        Thông tin do sinh viên tự nhập, nhà trường chỉ xem. Riêng chứng chỉ tự khai có thể được xác thực.
      </Typography.Text>
      <div>
        <Typography.Title level={4}>Hồ sơ</Typography.Title>
        {p ? (
          <Descriptions bordered size="small" column={{ xs: 1, md: 2 }}>
            <Descriptions.Item label="Giới thiệu" span="filled">{p.bio ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Mục tiêu nghề nghiệp" span="filled">{p.career_goal ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Email liên hệ">{p.contact_email ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Điện thoại liên hệ">{p.contact_phone ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Địa chỉ" span="filled">{p.address ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="LinkedIn">{p.linkedin_url ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="GitHub">{p.github_url ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Cài đặt riêng tư" span="filled">
              <Flex gap={8} wrap>
                <Badge tone={p.is_open_to_work ? 'success' : 'neutral'}>
                  {p.is_open_to_work ? 'Đang tìm việc' : 'Không tìm việc'}
                </Badge>
                <Badge tone={p.show_gpa ? 'info' : 'neutral'}>{p.show_gpa ? 'Chia sẻ GPA' : 'Ẩn GPA'}</Badge>
                <Badge tone={p.show_contact ? 'info' : 'neutral'}>{p.show_contact ? 'Chia sẻ liên hệ' : 'Ẩn liên hệ'}</Badge>
                <Badge tone={p.show_achievements ? 'info' : 'neutral'}>
                  {p.show_achievements ? 'Chia sẻ thành tích' : 'Ẩn thành tích'}
                </Badge>
              </Flex>
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sinh viên chưa có hồ sơ tự khai" />
        )}
      </div>
      <div>
        <Typography.Title level={4}>Kỹ năng</Typography.Title>
        <Table<SelfSkill>
          size="small"
          rowKey="skill_id"
          pagination={false}
          dataSource={data.skills}
          locale={{ emptyText: 'Chưa khai báo kỹ năng' }}
          columns={[
            { title: 'Kỹ năng', dataIndex: 'name' },
            { title: 'Mức độ', dataIndex: 'level', render: (l: SelfSkill['level']) => SKILL_LEVEL_LABEL[l] },
            { title: 'Nguồn', dataIndex: 'source', render: (s: string) => ({ SELF: 'Tự khai', CV_AI: 'Phân tích CV', SCHOOL: 'Nhà trường' })[s] ?? s },
          ]}
        />
      </div>
      <div>
        <Typography.Title level={4}>Kinh nghiệm</Typography.Title>
        <ItemList
          items={data.experiences}
          rowKey={(e) => e.id}
          empty="Chưa khai báo kinh nghiệm"
          render={(e) => ({
            title: `${e.position} · ${e.company_name}`,
            description: (
              <>
                <div>
                  {formatDate(e.start_date)} - {e.end_date ? formatDate(e.end_date) : 'nay'}
                </div>
                {e.description && <div>{e.description}</div>}
              </>
            ),
          })}
        />
      </div>
      <div>
        <Typography.Title level={4}>Dự án</Typography.Title>
        <ItemList
          items={data.projects}
          rowKey={(pr) => pr.id}
          empty="Chưa khai báo dự án"
          render={(pr) => ({
            title: pr.name + (pr.role ? ` · ${pr.role}` : ''),
            description: (
              <>
                {pr.description && <div>{pr.description}</div>}
                {pr.tech_stack && <div>Công nghệ: {pr.tech_stack}</div>}
                {pr.project_url && (
                  <a href={pr.project_url} target="_blank" rel="noreferrer">
                    {pr.project_url}
                  </a>
                )}
              </>
            ),
          })}
        />
      </div>
      <div>
        <Typography.Title level={4}>Chứng chỉ tự khai</Typography.Title>
        <CertificateList items={data.certificates} studentId={studentId} verifiable />
      </div>
    </Flex>
  )
}

export default function StudentDetailPage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const params = useParams()
  const studentId = Number(params.studentId)
  const [editing, setEditing] = useState(false)
  const query = useStudentDetail(studentId)
  const issue = useIssueAccount(studentId)

  if (!Number.isInteger(studentId)) return <Result status="404" title="Không tìm thấy sinh viên" />
  if (query.isLoading) return <Skeleton active paragraph={{ rows: 8 }} />
  if (getErrorStatus(query.error) === 404) {
    return (
      <Result
        status="404"
        title="Không tìm thấy sinh viên"
        extra={<Button onClick={() => navigate('/admin/students')}>Về danh sách</Button>}
      />
    )
  }
  if (query.isError || !query.data) return <QueryError error={query.error} onRetry={() => query.refetch()} />

  const detail = query.data
  const academic = detail.official.academic

  const resend = async () => {
    try {
      await issue.mutateAsync()
      message.success('Đã gửi lại email kích hoạt')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <>
      <PageHeader
        eyebrow={`Mã SV: ${academic.student_code}`}
        title={academic.full_name}
        subtitle={`${academic.faculty_name} · ${academic.major_name} · Khóa ${academic.cohort}`}
        meta={<AccountStatusBadge status={academic.account_status} />}
        extra={
          <>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/admin/students')}>
              Danh sách
            </Button>
            {academic.account_status === 'PENDING_ACTIVATION' && (
              <Popconfirm
                title="Gửi lại email kích hoạt?"
                description={`Liên kết mới sẽ được gửi tới ${academic.email}; liên kết cũ không dùng được nữa.`}
                okText="Gửi"
                cancelText="Hủy"
                onConfirm={resend}
              >
                <Button type="primary" icon={<MailOutlined />} loading={issue.isPending}>
                  Gửi lại email kích hoạt
                </Button>
              </Popconfirm>
            )}
          </>
        }
      />
      <div className="sc-card" style={{ padding: 24 }}>
        <Tabs
          items={[
            {
              key: 'official',
              label: 'Dữ liệu nhà trường',
              children: <OfficialTab detail={detail.official} studentId={studentId} onEdit={() => setEditing(true)} />,
            },
            {
              key: 'self',
              label: 'Thông tin tự khai',
              children: <SelfDeclaredTab data={detail.self_declared} studentId={studentId} />,
            },
          ]}
        />
      </div>
      <EditAcademicModal student={academic} open={editing} onClose={() => setEditing(false)} />
    </>
  )
}
