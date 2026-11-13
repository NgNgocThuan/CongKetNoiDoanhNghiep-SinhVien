import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react'
import { useToast } from '@/lib/toast'

export function ToastContainer() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 99999,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        maxWidth: '420px',
        width: 'calc(100vw - 40px)',
        pointerEvents: 'none',
      }}
      aria-live="polite"
    >
      {toasts.map((t) => {
        const bg =
          t.type === 'success'
            ? '#ecfdf5'
            : t.type === 'error'
            ? '#fef2f2'
            : t.type === 'warning'
            ? '#fffbeb'
            : '#eff6ff'
        const border =
          t.type === 'success'
            ? '#10b981'
            : t.type === 'error'
            ? '#ef4444'
            : t.type === 'warning'
            ? '#f59e0b'
            : '#3b82f6'
        const color =
          t.type === 'success'
            ? '#065f46'
            : t.type === 'error'
            ? '#991b1b'
            : t.type === 'warning'
            ? '#92400e'
            : '#1e40af'

        const Icon =
          t.type === 'success'
            ? CheckCircle2
            : t.type === 'error'
            ? AlertCircle
            : t.type === 'warning'
            ? AlertTriangle
            : Info

        return (
          <div
            key={t.id}
            style={{
              pointerEvents: 'auto',
              background: bg,
              borderLeft: `4px solid ${border}`,
              borderTop: `1px solid ${border}33`,
              borderRight: `1px solid ${border}33`,
              borderBottom: `1px solid ${border}33`,
              borderRadius: '8px',
              padding: '12px 16px',
              boxShadow: '0 8px 24px -4px rgba(0, 0, 0, 0.12)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              color,
              animation: 'fadeIn 0.2s ease-out',
            }}
          >
            <Icon size={20} style={{ flexShrink: 0, marginTop: '2px', color: border }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              {t.title && (
                <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '2px' }}>
                  {t.title}
                </div>
              )}
              <div style={{ fontSize: '13px', lineHeight: 1.45, wordBreak: 'break-word' }}>
                {t.message}
              </div>
            </div>
            <button
              onClick={() => dismiss(t.id)}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '2px',
                color: 'inherit',
                opacity: 0.6,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              aria-label="Đóng"
            >
              <X size={16} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
