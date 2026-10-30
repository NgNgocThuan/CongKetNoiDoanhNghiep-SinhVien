import type { ReactNode } from 'react'
import { PageHeader as CommonPageHeader } from '@/components/common/PageHeader'
export default function PageHeader({ eyebrow, title, subtitle, extra, meta }: {
  eyebrow?: string; title: ReactNode; subtitle?: ReactNode; extra?: ReactNode; meta?: ReactNode
}) {
  return <><CommonPageHeader eyebrow={eyebrow} title={title} description={subtitle} actions={extra} />
    {meta && <div className="school-page-meta">{meta}</div>}</>
}
