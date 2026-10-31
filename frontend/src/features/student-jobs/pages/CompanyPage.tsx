import { useParams } from 'react-router-dom'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { ReportDialog } from '@/features/administration/pages'
import { CompanyPublicProfile } from '../components/CompanyPublicProfile'
import { StudentPage } from '../components/StudentUI'
export default function CompanyPage() {
  const { id } = useParams()
  const [report, setReport] = useState(false)
  return (
    <StudentPage title="Hồ sơ doanh nghiệp">
      <CompanyPublicProfile companyId={Number(id)} />
      <Button variant="ghost" onClick={() => setReport(true)}>
        Báo cáo doanh nghiệp
      </Button>
      {report && (
        <ReportDialog
          targetType="COMPANY"
          targetId={Number(id)}
          onClose={() => setReport(false)}
        />
      )}
    </StudentPage>
  )
}
