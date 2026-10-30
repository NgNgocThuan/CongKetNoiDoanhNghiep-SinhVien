import { http } from '@/lib/http'
import { env } from '@/config/env'
export async function downloadFile(path: string, filename: string) {
  // Only accept backend-relative API paths, never a third-party token-bearing URL.
  if (!path.startsWith('/') || path.startsWith('//')) throw new Error('Invalid download path')
  const response = await http.get<Blob>(path, { responseType: 'blob', baseURL: new URL(env.apiBaseUrl, window.location.origin).origin })
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url; link.download = filename; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
