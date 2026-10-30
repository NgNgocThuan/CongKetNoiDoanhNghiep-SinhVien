import { z } from 'zod'

const schema = z.object({
  VITE_API_BASE_URL: z.string().refine(
    value => value.startsWith('/') && !value.startsWith('//') || /^https?:\/\//.test(value),
    'VITE_API_BASE_URL phải là đường dẫn tương đối hoặc URL HTTP(S).',
  ),
})
const parsed = schema.parse({ VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL || '/api/v1' })
export const env = { apiBaseUrl: parsed.VITE_API_BASE_URL.replace(/\/$/, '') }
