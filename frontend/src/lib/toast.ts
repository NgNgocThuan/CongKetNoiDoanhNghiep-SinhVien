import { useState, useEffect } from 'react'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  title?: string
  message: string
  duration?: number
}

type ToastListener = (toasts: ToastMessage[]) => void

let toasts: ToastMessage[] = []
const listeners = new Set<ToastListener>()

function notify() {
  listeners.forEach((fn) => fn([...toasts]))
}

export const toast = {
  show(msg: Omit<ToastMessage, 'id'>) {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: ToastMessage = { ...msg, id }
    toasts = [...toasts, newToast]
    notify()

    const duration = msg.duration ?? 4500
    if (duration > 0) {
      setTimeout(() => {
        toast.dismiss(id)
      }, duration)
    }
    return id
  },
  success(message: string, title?: string) {
    return toast.show({ type: 'success', message, title })
  },
  error(message: string, title?: string) {
    return toast.show({ type: 'error', message, title })
  },
  info(message: string, title?: string) {
    return toast.show({ type: 'info', message, title })
  },
  warning(message: string, title?: string) {
    return toast.show({ type: 'warning', message, title })
  },
  dismiss(id: string) {
    toasts = toasts.filter((t) => t.id !== id)
    notify()
  },
}

export function useToast() {
  const [list, setList] = useState<ToastMessage[]>(toasts)

  useEffect(() => {
    listeners.add(setList)
    return () => {
      listeners.delete(setList)
    }
  }, [])

  return { toasts: list, dismiss: toast.dismiss }
}

