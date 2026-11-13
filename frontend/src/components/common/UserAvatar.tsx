import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { http } from '@/lib/http'
import { useAuth, userDisplayName } from '@/features/auth'

export function UserAvatar({ userId, name, size = 36 }: { userId: string | number; name: string; size?: number }) {
  const [url, setUrl] = useState('')
  const query = useQuery({
    queryKey: ['user-avatar', String(userId)],
    enabled: Boolean(userId),
    staleTime: 60_000,
    queryFn: async () => {
      const response = await http.get<Blob>(`/auth/users/${userId}/avatar`, { responseType: 'blob' })
      return response.status === 204 ? null : response.data
    },
  })
  useEffect(() => {
    if (!query.data) {
      setUrl('')
      return
    }
    const value = URL.createObjectURL(query.data)
    setUrl(value)
    return () => URL.revokeObjectURL(value)
  }, [query.data])
  return (
    <span style={{ display: 'inline-flex', width: size, height: size, flexShrink: 0, alignItems: 'center', justifyContent: 'center', overflow: 'hidden', borderRadius: '50%', background: '#e7f4ef', color: '#00685f', fontWeight: 750 }}>
      {url ? <img src={url} alt={`Ảnh đại diện ${name}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : name.trim().slice(0, 1).toUpperCase()}
    </span>
  )
}

export function AvatarUpload() {
  const { user } = useAuth()
  const client = useQueryClient()
  const [selected, setSelected] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    if (!selected) return
    const value = URL.createObjectURL(selected)
    setPreview(value)
    return () => URL.revokeObjectURL(value)
  }, [selected])
  const save = useMutation({
    mutationFn: async () => {
      const body = new FormData()
      body.append('file', selected!)
      await http.put('/auth/me/avatar', body)
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: ['user-avatar'] })
      setSelected(null)
      setPreview('')
    },
  })
  if (!user) return null
  return (
    <section style={{ padding: 24, marginBottom: 24, background: 'white', border: '1px solid #dce8e3', borderRadius: 16 }}>
      <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>Ảnh đại diện</h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        {selected && preview ? <img src={preview} alt="Xem trước ảnh đại diện" style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover' }} /> : <UserAvatar userId={user.id} name={userDisplayName(user)} size={80} />}
        <div>
          <label style={{ display: 'grid', gap: 8 }}>
            <strong>Chọn ảnh từ thiết bị</strong>
            <input type="file" accept="image/jpeg,image/png,image/webp" disabled={save.isPending} onChange={(event) => {
              const file = event.target.files?.[0]
              setError('')
              save.reset()
              setSelected(null)
              setPreview('')
              if (!file) return
              if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 2 * 1024 * 1024) {
                setError('Vui lòng chọn ảnh JPG, PNG hoặc WebP tối đa 2 MB.')
                event.target.value = ''
                return
              }
              setSelected(file)
            }} />
          </label>
          <p style={{ color: '#647570', fontSize: 12 }}>JPG, PNG hoặc WebP · Tối đa 2 MB. Ảnh hiển thị cùng tài khoản khi tương tác.</p>
          <button type="button" disabled={!selected || save.isPending} onClick={() => save.mutate()} style={{ background: '#00685f', color: 'white', padding: '9px 16px', border: 0, borderRadius: 8, opacity: !selected || save.isPending ? .5 : 1 }}>{save.isPending ? 'Đang tải ảnh…' : 'Lưu ảnh đại diện'}</button>
        </div>
      </div>
      {(error || save.isError) && <p role="alert" style={{ color: '#b42318' }}>{error || save.error?.message}</p>}
      {save.isSuccess && <p role="status" style={{ color: '#00685f' }}>Đã cập nhật ảnh đại diện.</p>}
    </section>
  )
}
