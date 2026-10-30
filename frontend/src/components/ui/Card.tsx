import type { HTMLAttributes } from 'react'
export function Card({ className = '', children, ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={'card ' + className} {...props}>{children}</section>
}
