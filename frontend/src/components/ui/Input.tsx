import type { ComponentProps } from 'react'
export function Input({ className = '', ...props }: ComponentProps<'input'>) {
  return <input className={'input ' + className} {...props} />
}
export function Select({ className = '', children, ...props }: ComponentProps<'select'>) {
  return <select className={'input select ' + className} {...props}>{children}</select>
}
