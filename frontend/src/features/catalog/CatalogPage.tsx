/** Admin: quản lý danh mục (khoa, ngành, lĩnh vực, loại hình công việc, kỹ năng). */
import { useState } from 'react'
import { Button, Form, Input, Tabs } from 'antd'
import PageHeader from '@/features/school-shared/components/PageHeader'
import AliasDrawer from './AliasDrawer'
import ResourceTab from './ResourceTab'
import { useFaculties } from './hooks'
import { FacultySelect } from './selectors'
import type { Skill } from './types'

const required = [{ required: true, message: 'Vui lòng nhập thông tin này' }]

function MajorsTab() {
  const { data: faculties } = useFaculties()
  const facultyName = new Map(faculties?.items.map((f) => [f.id, f.name]))
  return (
    <ResourceTab
      resource="majors"
      noun="ngành"
      columns={[
        { title: 'Mã ngành', dataIndex: 'code', width: 140 },
        { title: 'Tên ngành', dataIndex: 'name' },
        { title: 'Khoa', dataIndex: 'faculty_id', render: (id: number) => facultyName.get(id) ?? `#${id}` },
      ]}
      extraFilters={(value, onChange) => (
        <FacultySelect
          allowClear
          placeholder="Lọc theo khoa"
          style={{ width: 240 }}
          value={value.faculty_id}
          onChange={(v) => onChange({ faculty_id: v })}
        />
      )}
      fields={
        <>
          <Form.Item name="faculty_id" label="Khoa" rules={[{ required: true, message: 'Vui lòng chọn khoa' }]}>
            <FacultySelect />
          </Form.Item>
          <Form.Item name="code" label="Mã ngành" rules={required}>
            <Input maxLength={30} />
          </Form.Item>
          <Form.Item name="name" label="Tên ngành" rules={required}>
            <Input maxLength={255} />
          </Form.Item>
        </>
      }
    />
  )
}

function SkillsTab() {
  const [aliasSkill, setAliasSkill] = useState<Skill | null>(null)
  return (
    <>
      <ResourceTab
        resource="skills"
        noun="kỹ năng"
        columns={[
          { title: 'Tên kỹ năng', dataIndex: 'name' },
          { title: 'Nhóm', dataIndex: 'category', render: (v: string | null) => v ?? '—' },
        ]}
        optionalKeys={['category']}
        extraFilters={(value, onChange) => (
          <Input
            allowClear
            placeholder="Lọc theo nhóm"
            style={{ width: 180 }}
            value={value.category}
            onChange={(e) => onChange({ category: e.target.value })}
          />
        )}
        rowExtra={(skill) => (
          <Button size="small" onClick={() => setAliasSkill(skill)}>
            Tên gọi khác
          </Button>
        )}
        fields={
          <>
            <Form.Item name="name" label="Tên kỹ năng" rules={required}>
              <Input maxLength={100} />
            </Form.Item>
            <Form.Item name="category" label="Nhóm (tùy chọn)">
              <Input maxLength={100} placeholder="Ví dụ: Frontend, Backend" />
            </Form.Item>
          </>
        }
      />
      <AliasDrawer skill={aliasSkill} onClose={() => setAliasSkill(null)} />
    </>
  )
}

export default function CatalogPage() {
  return (
    <>
      <PageHeader
        eyebrow="Phân hệ quản trị"
        title="Danh mục"
        subtitle="Dữ liệu dùng chung cho hồ sơ sinh viên, tin tuyển dụng và đợt thực tập. Danh mục không xóa hẳn mà chuyển sang ngừng hoạt động."
      />
      <div className="sc-card" style={{ padding: 24 }}>
        <Tabs
          destroyOnHidden
          items={[
            {
              key: 'faculties',
              label: 'Khoa',
              children: (
                <ResourceTab
                  resource="faculties"
                  noun="khoa"
                  columns={[
                    { title: 'Mã khoa', dataIndex: 'code', width: 140 },
                    { title: 'Tên khoa', dataIndex: 'name' },
                  ]}
                  fields={
                    <>
                      <Form.Item name="code" label="Mã khoa" rules={required}>
                        <Input maxLength={30} />
                      </Form.Item>
                      <Form.Item name="name" label="Tên khoa" rules={required}>
                        <Input maxLength={255} />
                      </Form.Item>
                    </>
                  }
                />
              ),
            },
            { key: 'majors', label: 'Ngành', children: <MajorsTab /> },
            {
              key: 'industries',
              label: 'Lĩnh vực',
              children: (
                <ResourceTab
                  resource="industries"
                  noun="lĩnh vực"
                  columns={[{ title: 'Tên lĩnh vực', dataIndex: 'name' }]}
                  fields={
                    <Form.Item name="name" label="Tên lĩnh vực" rules={required}>
                      <Input maxLength={255} />
                    </Form.Item>
                  }
                />
              ),
            },
            {
              key: 'job-types',
              label: 'Loại hình công việc',
              children: (
                <ResourceTab
                  resource="job-types"
                  noun="loại hình"
                  columns={[
                    { title: 'Mã', dataIndex: 'code', width: 160 },
                    { title: 'Tên loại hình', dataIndex: 'name' },
                  ]}
                  fields={
                    <>
                      <Form.Item name="code" label="Mã" rules={required}>
                        <Input maxLength={30} placeholder="Ví dụ: INTERN" />
                      </Form.Item>
                      <Form.Item name="name" label="Tên loại hình" rules={required}>
                        <Input maxLength={100} />
                      </Form.Item>
                    </>
                  }
                />
              ),
            },
            { key: 'skills', label: 'Kỹ năng', children: <SkillsTab /> },
          ]}
        />
      </div>
    </>
  )
}
