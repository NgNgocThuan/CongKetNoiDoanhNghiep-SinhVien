/** Tên gọi khác (alias) của một kỹ năng: xem, thêm, xóa (API không có sửa alias). */
import { useState } from 'react'
import { App, Button, Drawer, Flex, Input, Popconfirm, Spin, Typography } from 'antd'
import ItemList from '@/features/school-shared/components/ItemList'
import QueryError from '@/features/school-shared/components/QueryError'
import { getErrorMessage } from '@/features/school-shared/http'
import { useAddAlias, useDeleteAlias, useSkillAliases } from './hooks'
import type { Skill } from './types'

export default function AliasDrawer({ skill, onClose }: { skill: Skill | null; onClose: () => void }) {
  const { message } = App.useApp()
  const [alias, setAlias] = useState('')
  const skillId = skill?.id ?? 0
  const query = useSkillAliases(skill?.id ?? null)
  const add = useAddAlias(skillId)
  const remove = useDeleteAlias(skillId)

  const submit = async () => {
    const value = alias.trim()
    if (!value) return
    try {
      await add.mutateAsync(value)
      setAlias('')
      message.success('Đã thêm tên gọi khác')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const removeAlias = async (id: number) => {
    try {
      await remove.mutateAsync(id)
      message.success('Đã xóa tên gọi khác')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  return (
    <Drawer
      open={skill !== null}
      onClose={onClose}
      size={420}
      title={skill ? `Tên gọi khác của "${skill.name}"` : ''}
      destroyOnHidden
    >
      <Typography.Paragraph type="secondary">
        Dùng để nhận diện kỹ năng khi AI trả về tên khác (ví dụ "ReactJS" → React). Không phân biệt chữ hoa/thường.
      </Typography.Paragraph>
      <Flex gap={8} style={{ marginBottom: 16 }}>
        <Input
          value={alias}
          maxLength={100}
          placeholder="Nhập tên gọi khác"
          onChange={(e) => setAlias(e.target.value)}
          onPressEnter={submit}
        />
        <Button type="primary" loading={add.isPending} disabled={!alias.trim()} onClick={submit}>
          Thêm
        </Button>
      </Flex>
      {query.isError && <QueryError error={query.error} onRetry={() => query.refetch()} />}
      <Spin spinning={query.isFetching}>
        <ItemList
          items={query.data ?? []}
          rowKey={(a) => a.id}
          empty="Chưa có tên gọi khác"
          render={(a) => ({
            title: a.alias,
            actions: (
              <Popconfirm
                title="Xóa tên gọi khác này?"
                okText="Xóa"
                cancelText="Hủy"
                onConfirm={() => removeAlias(a.id)}
              >
                <Button size="small" danger>
                  Xóa
                </Button>
              </Popconfirm>
            ),
          })}
        />
      </Spin>
    </Drawer>
  )
}
