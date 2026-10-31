import { useParams } from 'react-router-dom'
import { CompanyPublicProfile } from '../components/CompanyPublicProfile'
import { StudentPage } from '../components/StudentUI'
export default function CompanyPage(){const {id}=useParams(); return <StudentPage title="Hồ sơ doanh nghiệp"><CompanyPublicProfile companyId={Number(id)}/></StudentPage>}

