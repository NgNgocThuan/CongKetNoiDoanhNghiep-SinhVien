import { BarChart3, Bell, BookOpen, BriefcaseBusiness, Building2, ClipboardList, FileCheck2, FileText, GraduationCap, Heart, Layers3, LayoutDashboard, Mail, Network, Send, Settings2, ShieldCheck, Sparkles, Users } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Role } from '@/features/auth'

export interface FeatureItem { id: string; path: string; title: string; description: string; owner: string; icon: LucideIcon; ready?: boolean }
const item = (id: string, path: string, title: string, description: string, owner: string, icon: LucideIcon, ready = false): FeatureItem => ({ id, path, title, description, owner, icon, ready })
export const features: Record<Role, FeatureItem[]> = {
  STUDENT: [
    item('student-jobs', 'jobs', 'Tìm việc', 'Khám phá cơ hội phù hợp với mục tiêu nghề nghiệp.', 'Việt Anh', BriefcaseBusiness),
    item('matching-jobs', 'recommended', 'Gợi ý phù hợp', 'Tìm hướng đi từ kỹ năng và kinh nghiệm của bạn.', 'Thuận', Sparkles),
    item('saved-jobs', 'saved-jobs', 'Việc đã lưu', 'Giữ lại những cơ hội bạn quan tâm.', 'Việt Anh', Heart),
    item('student-profile', 'profile', 'Hồ sơ của tôi', 'Kể câu chuyện học tập và năng lực của bạn.', 'Việt Anh', GraduationCap),
    item('student-cvs', 'cvs', 'CV của tôi', 'Chuẩn bị hồ sơ cho cơ hội tiếp theo.', 'Việt Anh', FileText),
    item('student-applications', 'applications', 'Đơn ứng tuyển', 'Theo dõi từng bước trong hành trình ứng tuyển.', 'Việt Anh', ClipboardList),
    item('student-invitations', 'invitations', 'Lời mời', 'Những kết nối mới từ doanh nghiệp.', 'Việt Anh', Mail),
    item('student-internships', 'internships', 'Thực tập của tôi', 'Thông tin đợt thực tập và giảng viên hướng dẫn.', 'Việt Anh', BookOpen),
  ],
  COMPANY: [
    item('company-jobs', 'jobs', 'Tin tuyển dụng', 'Quản lý nội dung và quy trình gửi duyệt tin.', 'Khôi', BriefcaseBusiness),
    item('company-applications', 'applications', 'Quản lý ứng viên', 'Theo dõi hồ sơ và các bước tuyển dụng.', 'Khôi', Users),
    item('matching-candidates', 'candidates', 'Gợi ý ứng viên', 'Kết nối với kỹ năng mà đội ngũ đang tìm kiếm.', 'Thuận', Sparkles),
    item('company-invitations', 'invitations', 'Lời mời đã gửi', 'Theo dõi những kết nối bạn đã mở ra.', 'Khôi', Send),
    item('company-profile', 'profile', 'Hồ sơ doanh nghiệp', 'Giới thiệu môi trường và giá trị của công ty.', 'Khôi', Building2),
  ],
  ADMIN: [
    item('analytics', 'analytics', 'Phân tích & báo cáo', 'Góc nhìn tổng quan về cơ hội và nguồn nhân lực.', 'Thuận', BarChart3),
    item('school-students', 'students', 'Sinh viên', 'Quản lý hồ sơ học thuật và dữ liệu sinh viên.', 'Phong', GraduationCap),
    item('lecturers', 'lecturers', 'Giảng viên', 'Quản lý thông tin giảng viên hướng dẫn.', 'Phong', Users),
    item('moderation-companies', 'companies', 'Doanh nghiệp', 'Xem xét và phê duyệt hồ sơ đối tác.', 'Quang', Building2, true),
    item('moderation-jobs', 'jobs', 'Kiểm duyệt tin', 'Giữ chất lượng các cơ hội tuyển dụng.', 'Quang', FileCheck2, true),
    item('internship-admin', 'internships', 'Đợt thực tập', 'Tổ chức đợt, phân công và xác nhận kết quả.', 'Phong', ClipboardList),
    item('catalog', 'catalog', 'Danh mục', 'Danh sách khoa và dữ liệu danh mục dùng chung.', 'Phong', Layers3, true),
    item('account-admin', 'users', 'Tài khoản', 'Quản lý quyền truy cập và trạng thái tài khoản.', 'Quang', ShieldCheck, true),
    item('reports', 'reports', 'Báo cáo vi phạm', 'Xem xét phản ánh và xử lý theo quy định.', 'Quang', FileText, true),
    item('email-logs', 'email-logs', 'Nhật ký email', 'Theo dõi quá trình gửi thông báo hệ thống.', 'Quang', Mail, true),
  ],
}
export const shellCopy: Record<Role, { subtitle: string; heading: string; description: string }> = {
  STUDENT: { subtitle: 'KHÔNG GIAN SINH VIÊN', heading: 'Mở cánh cửa cho\nhành trình của bạn.', description: 'Hồ sơ, cơ hội và những kết nối ý nghĩa. Tất cả bắt đầu từ một bước chủ động.' },
  COMPANY: { subtitle: 'KHÔNG GIAN DOANH NGHIỆP', heading: 'Kết nối đúng người.\nCùng tạo giá trị.', description: 'Đồng hành cùng thế hệ nhân sự mới, từ cơ hội thực tập đến đội ngũ tương lai.' },
  ADMIN: { subtitle: 'QUẢN TRỊ NHÀ TRƯỜNG', heading: 'Đồng hành cùng\nmỗi bước trưởng thành.', description: 'Một không gian để quản lý, kết nối và tạo cơ hội cho cộng đồng sinh viên.' },
}
export const sharedNavigation = { home: LayoutDashboard, notifications: Bell, settings: Settings2, network: Network }
