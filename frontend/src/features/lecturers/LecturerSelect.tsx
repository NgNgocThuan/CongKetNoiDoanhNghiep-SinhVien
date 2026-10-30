import { Select, type SelectProps } from 'antd'
import { useLecturers } from './api'

/** Chọn giảng viên đang hoạt động (tối đa 100 người theo giới hạn của API). Giá trị là id. */
export default function LecturerSelect(
  props: Pick<SelectProps<number>, 'value' | 'onChange' | 'allowClear' | 'placeholder' | 'disabled' | 'style'>,
) {
  const { data, isLoading } = useLecturers({ size: 100 })
  return (
    <Select<number>
      showSearch={{ optionFilterProp: 'label' }}
      loading={isLoading}
      placeholder="Chọn giảng viên"
      {...props}
      options={data?.items.map((l) => ({ value: l.id, label: l.code ? `${l.code} - ${l.full_name}` : l.full_name }))}
    />
  )
}
