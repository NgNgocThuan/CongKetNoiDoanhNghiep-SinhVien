import * as Primitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { useId, useRef } from 'react'
import type { ReactNode } from 'react'

export function Dialog({ open, onOpenChange, title, description, children, wide = false }: {
  open: boolean; onOpenChange: (open: boolean) => void; title: string; description?: string; children: ReactNode; wide?: boolean
}) {
  const descriptionId = useId()
  const returnFocus = useRef<HTMLElement | null>(null)
  return <Primitive.Root open={open} onOpenChange={onOpenChange}>
    <Primitive.Portal><Primitive.Overlay className="dialog-overlay" />
      <Primitive.Content className={wide ? 'dialog dialog--wide' : 'dialog'} aria-describedby={description ? descriptionId : undefined}
        onOpenAutoFocus={() => { returnFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null }}
        onCloseAutoFocus={event => {
          event.preventDefault()
          const target = returnFocus.current
          if (target?.isConnected && target !== document.body) target.focus({ preventScroll: true })
          else document.getElementById('main-content')?.focus({ preventScroll: true })
        }}>
        <div className="dialog__heading"><Primitive.Title>{title}</Primitive.Title>
          <Primitive.Close className="icon-button" aria-label="Đóng"><X size={19} /></Primitive.Close>
        </div>
        {description && <Primitive.Description id={descriptionId} className="muted">{description}</Primitive.Description>}
        {children}
      </Primitive.Content>
    </Primitive.Portal>
  </Primitive.Root>
}
