import { http } from '@/lib/http'
export const textValue = (value: unknown) =>
  value === null || value === undefined || value === '' ? '—' : String(value)
export const getData = async <T>(path: string, params?: object) =>
  (await http.get<T>(path, { params })).data
