import { useEffect, useState } from 'react'

export function DocumentPreview({ file }: { file: File | Blob | null }) {
  const [url, setUrl] = useState('')
  useEffect(() => {
    if (!file) { setUrl(''); return }
    const next = URL.createObjectURL(file)
    setUrl(next)
    return () => URL.revokeObjectURL(next)
  }, [file])
  if (!file || !url) return null
  return <div className="fl-document-preview">
    <p>{file instanceof File ? file.name : 'Bản xem trước văn bản'}</p>
    {file.type === 'application/pdf'
      ? <object data={url} type="application/pdf" aria-label="Xem trước tài liệu PDF"><a href={url} target="_blank" rel="noreferrer">Mở PDF để xem trước</a></object>
      : <img src={url} alt="Xem trước tài liệu đã chọn" />}
  </div>
}
