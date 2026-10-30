/**
 * Selector dùng chung cho form ở mọi module: khoa, ngành (theo khoa), lĩnh vực, loại hình công việc, kỹ năng.
 * Chỉ hiển thị mục đang hoạt động; giá trị là id (number). Dùng được cả trong Form.Item của Ant Design.
 */
import { useState } from 'react'
import { Select, type SelectProps } from 'antd'
import { useDebounced } from '@/lib/useDebounced'
import { useFaculties, useIndustries, useJobTypes, useMajors, useSkillSearch } from './hooks'

type Common = Pick<SelectProps<number>, 'value' | 'onChange' | 'allowClear' | 'placeholder' | 'disabled' | 'style' | 'id'>

export function FacultySelect(props: Common) {
  const { data, isLoading } = useFaculties()
  return (
    <Select<number>
      showSearch={{ optionFilterProp: 'label' }}
      loading={isLoading}
      placeholder="Chọn khoa"
      {...props}
      options={data?.items.map((f) => ({ value: f.id, label: f.name }))}
    />
  )
}

/** Ngành thuộc một khoa. Chưa chọn khoa thì hiện toàn bộ ngành (dùng cho bộ lọc). */
export function MajorSelect({ facultyId, ...props }: Common & { facultyId?: number }) {
  const { data, isLoading } = useMajors(facultyId)
  return (
    <Select<number>
      showSearch={{ optionFilterProp: 'label' }}
      loading={isLoading}
      placeholder="Chọn ngành"
      {...props}
      options={data?.items.map((m) => ({ value: m.id, label: m.name }))}
    />
  )
}

export function IndustrySelect(props: Common) {
  const { data, isLoading } = useIndustries()
  return (
    <Select<number>
      showSearch={{ optionFilterProp: 'label' }}
      loading={isLoading}
      placeholder="Chọn lĩnh vực"
      {...props}
      options={data?.items.map((i) => ({ value: i.id, label: i.name }))}
    />
  )
}

export function JobTypeSelect(props: Common) {
  const { data, isLoading } = useJobTypes()
  return (
    <Select<number>
      loading={isLoading}
      placeholder="Chọn loại hình công việc"
      {...props}
      options={data?.items.map((j) => ({ value: j.id, label: j.name }))}
    />
  )
}

/** Tìm kỹ năng theo tên hoặc tên gọi khác (alias); chọn nhiều, trả về mảng id. */
export function SkillSelect({
  value,
  onChange,
  placeholder = 'Gõ để tìm kỹ năng',
  disabled,
  style,
}: {
  value?: number[]
  onChange?: (ids: number[]) => void
  placeholder?: string
  disabled?: boolean
  style?: React.CSSProperties
}) {
  const [text, setText] = useState('')
  const debounced = useDebounced(text)
  const { data, isFetching } = useSkillSearch(debounced)
  return (
    <Select<number[]>
      mode="multiple"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      style={style}
      filterOption={false}
      onSearch={setText}
      loading={isFetching}
      notFoundContent={debounced ? 'Không tìm thấy kỹ năng' : 'Nhập tên kỹ năng để tìm'}
      options={data?.map((s) => ({ value: s.id, label: s.name }))}
    />
  )
}
