import type { ButtonHTMLAttributes } from 'react'
import { LoaderCircle } from 'lucide-react'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
  pending?: boolean
}
export function Button({ variant = 'primary', size = 'md', pending, disabled, className = '', type = 'button', children, ...props }: Props) {
  return <button type={type} className={['button', 'button--' + variant, 'button--' + size, className].join(' ')}
    disabled={disabled || pending} aria-busy={pending || undefined} {...props}>
    {pending && <LoaderCircle size={16} className="spin" aria-hidden="true" />}{children}
  </button>
}
