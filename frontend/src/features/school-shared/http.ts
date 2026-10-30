// Compatibility helpers for school modules; all requests use the shared authenticated client.
import { toApiError } from '@/lib/api-error'
export { http } from '@/lib/http'
export function getErrorMessage(error: unknown): string {
  const normalized = toApiError(error)
  const fields = Object.entries(normalized.fields)
  return fields.length ? fields.map(([field, message]) => field + ': ' + message).join('; ') : normalized.message
}
export function getErrorStatus(error: unknown): number | undefined {
  return toApiError(error).status ?? undefined
}
