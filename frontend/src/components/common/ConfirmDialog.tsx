import { useState } from 'react'
import { Dialog } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'
import { toApiError } from '@/lib/api-error'

export function ConfirmDialog({ open, onOpenChange, title, description, onConfirm, confirmLabel = 'Xác nhận', danger = false }: {
  open: boolean; onOpenChange: (open: boolean) => void; title: string; description: string;
  onConfirm: () => Promise<void>; confirmLabel?: string; danger?: boolean
}) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  async function confirm() {
    setPending(true); setError('')
    try { await onConfirm(); onOpenChange(false) } catch (err) { setError(toApiError(err).message) }
    finally { setPending(false) }
  }
  return <Dialog open={open} onOpenChange={value => { if (!pending) { setError(''); onOpenChange(value) } }} title={title} description={description}>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="dialog__actions"><Button variant="secondary" disabled={pending} onClick={() => onOpenChange(false)}>Hủy</Button><Button pending={pending} variant={danger ? 'danger' : 'primary'} onClick={() => void confirm()}>{confirmLabel}</Button></div>
  </Dialog>
}
