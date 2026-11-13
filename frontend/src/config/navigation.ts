import { BarChart3, Bell, BriefcaseBusiness, Building2, ClipboardList, FileCheck2, FileText, GraduationCap, Heart, Layers3, LayoutDashboard, Mail, Network, Send, Settings2, ShieldCheck, Sparkles, Users } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Role } from '@/features/auth'

export interface FeatureItem { id: string; path: string; title: string; description: string; owner: string; icon: LucideIcon; ready?: boolean }
const item = (id: string, path: string, title: string, description: string, owner: string, icon: LucideIcon, ready = false): FeatureItem => ({ id, path, title, description, owner, icon, ready })
export const features: Record<Role, FeatureItem[]> = {
  CLIENT: [],
  STUDENT: [
    item('student-jobs', 'jobs', 'Tìm việc', 'Khám phá cơ hội phù hợp với mục tiêu nghề nghiệp.', 'Việt Anh', BriefcaseBusiness, true),
    item('matching-jobs', 'recommended', 'Gợi ý phù hợp', 'Tìm hướng đi từ kỹ năng và kinh nghiệm của bạn.', 'Thuận', Sparkles, true),
    item('saved-jobs', 'saved-jobs', 'Việc đã lưu', 'Giữ lại những cơ hội bạn quan tâm.', 'Việt Anh', Heart, true),
    item('student-profile', 'profile', 'Hồ sơ của tôi', 'Kể câu chuyện học tập và năng lực của bạn.', 'Việt Anh', GraduationCap, true),
    item('student-cvs', 'cvs', 'CV của tôi', 'Chuẩn bị hồ sơ cho cơ hội tiếp theo.', 'Việt Anh', FileText, true),
    item('student-applications', 'applications', 'Đơn ứng tuyển', 'Theo dõi từng bước trong hành trình ứng tuyển.', 'Việt Anh', ClipboardList, true),
    item('student-invitations', 'invitations', 'Lời mời', 'Những kết nối mới từ doanh nghiệp.', 'Việt Anh', Mail, true),
  ],
  COMPANY: [
    item('company-jobs', 'jobs', 'Tin tuyển dụng', 'Quản lý nội dung và quy trình gửi duyệt tin.', 'Khôi', BriefcaseBusiness, true),
    item('company-applications', 'applications', 'Quản lý ứng viên', 'Theo dõi hồ sơ và các bước tuyển dụng.', 'Khôi', Users, true),
    item('matching-candidates', 'candidates', 'Gợi ý ứng viên', 'Kết nối với kỹ năng mà đội ngũ đang tìm kiếm.', 'Thuận', Sparkles, true),
    item('company-invitations', 'invitations', 'Lời mời đã gửi', 'Theo dõi những kết nối bạn đã mở ra.', 'Khôi', Send, true),
    item('company-profile', 'profile', 'Hồ sơ doanh nghiệp', 'Giới thiệu môi trường và giá trị của công ty.', 'Khôi', Building2, true),
  ],
  ADMIN: [
    item('analytics', 'analytics', 'Phân tích & báo cáo', 'Góc nhìn tổng quan về cơ hội và nguồn nhân lực.', 'Thuận', BarChart3, true),
    item('school-students', 'students', 'Sinh viên', 'Quản lý hồ sơ học thuật và dữ liệu sinh viên.', 'Phong', GraduationCap, true),
    item('moderation-companies', 'companies', 'Doanh nghiệp', 'Xem xét và phê duyệt hồ sơ đối tác.', 'Quang', Building2, true),
    item('moderation-jobs', 'jobs', 'Kiểm duyệt tin', 'Giữ chất lượng các cơ hội tuyển dụng.', 'Quang', FileCheck2, true),
    item('catalog', 'catalog', 'Danh mục', 'Khoa, ngành và các danh mục dùng chung.', 'Phong', Layers3, true),
    item('account-admin', 'users', 'Tài khoản', 'Quản lý quyền truy cập và trạng thái tài khoản.', 'Quang', ShieldCheck, true),
    item('reports', 'reports', 'Báo cáo vi phạm', 'Xem xét phản ánh và xử lý theo quy định.', 'Quang', FileText, true),
    item('email-logs', 'email-logs', 'Nhật ký email', 'Theo dõi quá trình gửi thông báo hệ thống.', 'Quang', Mail, true),
  ],
}
export const shellCopy: Record<Role, { subtitle: string; heading: string; description: string }> = {
  CLIENT: { subtitle: 'FREELANCER', heading: 'K\u1ebft n\u1ed1i \u0111\u00fang ng\u01b0\u1eddi.', description: 'Qu\u1ea3n l\u00fd d\u1ef1 \u00e1n, h\u1ee3p \u0111\u1ed3ng v\u00e0 thanh to\u00e1n.' },
  STUDENT: { subtitle: 'KHÔNG GIAN SINH VIÊN', heading: 'Mở cánh cửa cho\nhành trình của bạn.', description: 'Hồ sơ, cơ hội và những kết nối ý nghĩa. Tất cả bắt đầu từ một bước chủ động.' },
  COMPANY: { subtitle: 'KHÔNG GIAN DOANH NGHIỆP', heading: 'Kết nối đúng người.\nCùng tạo giá trị.', description: 'Đồng hành cùng thế hệ nhân sự mới, từ cơ hội thực tập đến đội ngũ tương lai.' },
  ADMIN: { subtitle: 'QUẢN TRỊ NHÀ TRƯỜNG', heading: 'Đồng hành cùng\nmỗi bước trưởng thành.', description: 'Một không gian để quản lý, kết nối và tạo cơ hội cho cộng đồng sinh viên.' },
}
export const sharedNavigation = { home: LayoutDashboard, notifications: Bell, settings: Settings2, network: Network }

export function navigationGroups(role: Role) {
  const management = new Set(['analytics', 'students', 'catalog', 'users', 'reports', 'email-logs', 'profile', 'cvs'])
  return [
    { id: 'recruitment', title: 'Tuyển dụng & công việc', items: features[role].filter(f => !f.path.startsWith('freelancer') && !management.has(f.path)) },
    { id: 'freelancer', title: 'Dự án Freelancer', items: features[role].filter(f => f.path.startsWith('freelancer')) },
    { id: 'management', title: 'Quản lý & báo cáo', items: features[role].filter(f => management.has(f.path)) },
  ].filter(group => group.items.length > 0)
}

const freelancerOwner = [
  item('freelancer-home', 'freelancer', 'Tổng quan Freelancer', 'Theo dõi hợp tác theo dự án.', 'Freelancer', LayoutDashboard, true),
  item('freelancer-projects', 'freelancer/projects', 'Dự án của tôi', 'Dự án nhiều sinh viên, hợp đồng riêng.', 'Freelancer', BriefcaseBusiness, true),
  item('freelancer-work', 'freelancer/work', 'Hợp đồng & ký quỹ', 'Điều khoản, mốc và thanh toán.', 'Freelancer', FileText, true),
  item('freelancer-finance', 'freelancer/finance', 'Ký quỹ & giao dịch', 'Xem tiền theo hợp đồng và từng mốc.', 'Freelancer', BarChart3, true),
  item('freelancer-banks', 'freelancer/banks', 'Ngân hàng nhận tiền', 'Nhận giải ngân và hoàn tiền.', 'Freelancer', Building2, true),
  item('freelancer-onboarding', 'freelancer/onboarding', 'Xác minh Freelancer', 'Liên hệ, pháp nhân và MOU.', 'Freelancer', ShieldCheck, true),
]
features.CLIENT.push(...freelancerOwner)
features.COMPANY.push(...freelancerOwner)
features.STUDENT.push(
  item('freelancer-home', 'freelancer', 'Không gian Freelancer', 'Hợp tác trong các dự án thực tế.', 'Freelancer', Layers3, true),
  item('freelancer-projects', 'freelancer/projects', 'Tìm dự án Freelancer', 'Khám phá dự án và gửi đề xuất.', 'Freelancer', BriefcaseBusiness, true),
  item('freelancer-work', 'freelancer/work', 'Công việc Freelancer', 'Ứng tuyển, hợp đồng và thanh toán.', 'Freelancer', FileText, true),
  item('freelancer-finance', 'freelancer/finance', 'Thanh toán Freelancer', 'Theo dõi ký quỹ và giải ngân.', 'Freelancer', BarChart3, true),
  item('freelancer-banks', 'freelancer/banks', 'Ngân hàng nhận tiền', 'Quản lý tài khoản nhận giải ngân.', 'Freelancer', Building2, true),
)
features.ADMIN.push(
  item('freelancer-home', 'freelancer', 'Quản trị Freelancer', 'Theo dõi các hàng đợi xử lý.', 'Freelancer', LayoutDashboard, true),
  ...([
    ['business', 'Pháp nhân & MOU'], ['projects', 'Duyệt dự án Freelancer'], ['banks', 'Tài khoản nhận tiền'],
    ['receipts', 'Thu & ký quỹ'], ['transfers', 'Giải ngân & hoàn tiền'],
    ['disputes', 'Tranh chấp Freelancer'], ['reconciliation', 'Đối soát Freelancer'],
  ]).map(([path, title]) => item('freelancer-admin-' + path, 'freelancer/admin/' + path, title, 'Quản lý nghiệp vụ Freelancer.', 'Freelancer', ShieldCheck, true)),
)
