import * as Primitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { useId } from 'react'
import type { ReactNode } from 'react'

export function Dialog({ open, onOpenChange, title, description, children }: {
  open: boolean; onOpenChange: (open: boolean) => void; title: string; description?: string; children: ReactNode
}) {
  const descriptionId = useId()
  return <Primitive.Root open={open} onOpenChange={onOpenChange}>
    <Primitive.Portal><Primitive.Overlay className="dialog-overlay" />
      <Primitive.Content className="dialog" aria-describedby={description ? descriptionId : undefined}>
        <div className="dialog__heading"><Primitive.Title>{title}</Primitive.Title>
          <Primitive.Close className="icon-button" aria-label="Đóng"><X size={19} /></Primitive.Close>
        </div>
        {description && <Primitive.Description id={descriptionId} className="muted">{description}</Primitive.Description>}
        {children}
      </Primitive.Content>
    </Primitive.Portal>
  </Primitive.Root>
}
