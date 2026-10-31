import { useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toApiError } from '@/lib/api-error'
export function useStudentAction(keys: string[] = ['student']) {
  const client = useQueryClient(),
    busy = useRef(false)
  const [pending, setPending] = useState(false),
    [error, setError] = useState(''),
    [success, setSuccess] = useState('')
  async function run(
    action: () => Promise<unknown>,
    message = 'Đã lưu thay đổi.',
  ) {
    if (busy.current) return false
    busy.current = true
    setPending(true)
    setError('')
    setSuccess('')
    try {
      await action()
      for (const key of keys)
        await client.invalidateQueries({ queryKey: [key] })
      if (keys.includes('student-cvs'))
        await client.invalidateQueries({ queryKey: ['cvs'] })
      if (keys.includes('student-profile') || keys.includes('student-cvs'))
        await client.invalidateQueries({ queryKey: ['matching'] })
      setSuccess(message)
      return true
    } catch (err) {
      const e = toApiError(err)
      setError([e.message, ...Object.values(e.fields)].join(' '))
      return false
    } finally {
      busy.current = false
      setPending(false)
    }
  }
  return { pending, error, success, run }
}
