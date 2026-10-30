import React, { useState } from 'react';

interface Invitation {
    id: string;
    studentId: string;
    studentName: string;
    studentAvatar: string;
    studentMeta: string;
    isVerifiedOpen: boolean;
    jobId: string;
    jobTitle: string;
    jobCode: string;
    sentTime: string;
    status: 'ACCEPTED' | 'PENDING' | 'REJECTED';
    statusText: string;
    statusBadge: string;
    message: string;
}

export const InvitedApplicationsPage: React.FC = () => {
    // State danh sách lời mời đã gửi
    const [invitations, setInvitations] = useState<Invitation[]>([
        {
            id: 'INV-001',
            studentId: 'BK-2021-0849',
            studentName: 'Nguyễn Minh Đức',
            studentAvatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD4-WDb6-F0mBA2Rd-zz1kBow2Gw9O1nl6BNl_J3AG1YIz_CEjblUxUFX1thoG8z4u7pEzeVs_AWbxY7KYrOvs3fuX-9gmbnu1r8srdonSo3up4MHIdqV2eN69dgVRWi-Ca4NkvDcW2tXySlfNWOJJeeB6LtbkWppXHcE7RQynm5JKkwsE6fIIMigqjfZlvq5x4ISHxlrw6IECXGmmeEQtqgHS4c6Fw3g37Mmml10I',
            studentMeta: 'ĐH Bách Khoa • KHMT (GPA: 3.65/4.0)',
            isVerifiedOpen: true,
            jobId: 'JOB-FE-2025',
            jobTitle: 'Frontend Intern (React/Next.js)',
            jobCode: 'Mã Job: #JOB-FE-2025',
            sentTime: '14:30 - Hôm nay',
            status: 'ACCEPTED',
            statusText: 'Đã nộp đơn',
            statusBadge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
            message: 'Chào Đức, team FPT rất ấn tượng với portfolio React của bạn...'
        },
        {
            id: 'INV-002',
            studentId: 'UIT-2022-1102',
            studentName: 'Trần Mai Phương',
            studentAvatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC-iz3PrR-prPTjklmiqUaFh6vvQfwPW8ZYlbmuibCt8R1_RqFL5ZvaRpoL6VjcVPB2YZqOi5zpRqWlglIKDdcgknvFAampdkuZb2__XZfNDTI5VQBBzZUpkxM7nSOY1p__c36RL6Iw4DWn7OsrVWpmPsUJ0qPb8MqYL3dDiQz2DN6vFXtndOrPkm_xgYrs8eC8G20t4AG70BwTf8sKX0vVJdFmSNaUKEUSzoGzBBQ',
            studentMeta: 'ĐH Công Nghệ Thông Tin (UIT) • HTTT',
            isVerifiedOpen: true,
            jobId: 'JOB-DA-092',
            jobTitle: 'Data Analyst & BI Intern',
            jobCode: 'Mã Job: #JOB-DA-092',
            sentTime: '09:15 - Hôm qua',
            status: 'PENDING',
            statusText: 'Đang chờ (còn 2 ngày)',
            statusBadge: 'bg-amber-100 text-amber-800 border-amber-200',
            message: 'Chào Phương, mời bạn ứng tuyển nhờ giải Ba cuộc thi Data...'
        },
        {
            id: 'INV-003',
            studentId: 'FPT-2021-5541',
            studentName: 'Lê Hoàng Nam',
            studentAvatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDpYDGpckwuarapa_Rr8lF0XaUO7M1JN51KsfNWWYXLcoWrMQtv8r8--p69blOxrPF74NSEYFAeNukZeRFapYaK9PTt5W6Ce5IgO2JAUkaO5Ae2rYqPQsSO2ynlAVQLSMjn0poe2bxR8xkP62B-A-mFdD7VfusVsKbfQmz5Xg86Z9f5p6njbED561SkW4C_CezOvg7W3hQUZ7m_gxDibVWyyzR3pO9i12qyZOu-7jE',
            studentMeta: 'Đại học FPT • Kỹ thuật Phần mềm (GPA: 3.42)',
            isVerifiedOpen: true,
            jobId: 'JOB-BE-104',
            jobTitle: 'Backend Node.js & Go Developer',
            jobCode: 'Mã Job: #JOB-BE-104',
            sentTime: '24/05/2025',
            status: 'ACCEPTED',
            statusText: 'Đã nộp đơn',
            statusBadge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
            message: 'Dự án Microservices đang tìm ứng viên có nền tảng Golang...'
        }
    ]);

    // State Modal Gửi lời mời
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedJobId, setSelectedJobId] = useState('JOB-FE-2025');
    const [selectedStudentId] = useState('BK-2021-0849');
    const [invitationMessage, setInvitationMessage] = useState(
        'Chào Minh Đức, Bộ phận Nhân sự FPT Software rất ấn tượng với hồ sơ và các sản phẩm React của bạn trên Student Connect. Chúng tôi trân trọng mời bạn tham gia ứng tuyển trực tiếp vào vị trí Frontend Intern (React/Next.js) đợt Hè 2025 này. Khi nộp hồ sơ qua thư mời này, bạn sẽ được ưu tiên vào thẳng vòng phỏng vấn kỹ thuật.'
    );

    // Toast Notification state
    const [showToast, setShowToast] = useState(false);

    const handleOpenModal = () => setIsModalOpen(true);
    const handleCloseModal = () => setIsModalOpen(false);

    // Gợi ý mẫu lời nhắn
    const handleSetTemplate = (type: number) => {
        if (type === 1) {
            setInvitationMessage('Chào Minh Đức, Đội ngũ kỹ sư tại FPT Software rất ấn tượng với đồ án Smart Campus và tư duy cấu trúc code ReactJS sạch của bạn. Chúng tôi trân trọng mời bạn nộp hồ sơ vào vị trí Frontend Intern để cùng tham gia các dự án thực tế quy mô lớn.');
        } else {
            setInvitationMessage('Chào bạn, Nhận thấy hồ sơ và định hướng công nghệ của bạn rất phù hợp với tiêu chuẩn tuyển dụng đợt Hè 2025, FPT Software xin gửi lời mời bạn ứng tuyển trực tiếp. Khi chấp nhận, hồ sơ của bạn sẽ được ưu tiên xếp lịch phỏng vấn sớm nhất.');
        }
    };

    // Xử lý gửi lời mời mới
    const handleSendInvitation = () => {
        const jobTitlesMap: Record<string, string> = {
            'JOB-FE-2025': 'Frontend Intern (React/Next.js)',
            'JOB-BE-104': 'Backend Node.js & Go Developer',
            'JOB-AI-881': 'AI / Machine Learning Research Intern',
            'JOB-QA-330': 'QC & Automation QA Tester'
        };

        const newInvitation: Invitation = {
            id: `INV-${Date.now()}`,
            studentId: selectedStudentId,
            studentName: 'Nguyễn Minh Đức',
            studentAvatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCapgL7JDVLYPUfcXuxE-TZOLx2-Hf3pap_B80qoEikLWGVIZF7XwuvWK9p83F0Kk4imY8pyQa9bBpqkisYkuZp4FHBLuG6FPfdayGA7KeNtY7hR9NolAR30wdY7T1r4HzP_esDjTld4USfQOmwtXGJjUlhxBiNYF-6xWFzXXMvFNUXzA5Y75Yb88rh1SGWz_pKal-A7lMj05oUGdzZsgfUic28j3BKESTuxoZr1Nw',
            studentMeta: 'ĐH Bách Khoa • Khoa Khoa học Máy tính',
            isVerifiedOpen: true,
            jobId: selectedJobId,
            jobTitle: jobTitlesMap[selectedJobId] || 'Frontend Intern (React/Next.js)',
            jobCode: `Mã Job: #${selectedJobId}`,
            sentTime: 'Vừa xong',
            status: 'PENDING',
            statusText: 'Đang chờ (còn 3 ngày)',
            statusBadge: 'bg-amber-100 text-amber-800 border-amber-200',
            message: invitationMessage
        };

        setInvitations((currentInvitations) => [newInvitation, ...currentInvitations]);
        setIsModalOpen(false);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 4000);
    };

    return (
        <>
            {/* Sidebar render trực tiếp trong React tree, không dùng Portal. */}
            <aside
                        aria-label="Thanh điều hướng chính"
                        className="fixed inset-y-0 left-0 z-[9999] h-screen w-[280px] bg-white border-r border-slate-200 flex flex-col justify-between p-4 shadow-sm select-none overflow-y-auto overscroll-contain"
                    >
                <div className="flex flex-col h-full">
                    {/* Brand Header */}
                    <div className="flex items-center gap-3 px-2 py-3 border-b border-slate-100 pb-4 mb-2">
                        <div className="w-10 h-10 rounded-xl bg-[#00288e] flex items-center justify-center text-white shadow-sm font-bold text-lg">
                            <span className="material-symbols-outlined text-white text-2xl">hub</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-base font-bold text-[#00288e]">Student Connect</span>
                            <span className="text-xs text-slate-400 font-medium">Enterprise Portal</span>
                        </div>
                    </div>

                    {/* Quick Action Post Button */}
                    <div className="my-2 px-1">
                        <button onClick={handleOpenModal} className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-[#1e40af] text-white text-sm font-semibold hover:bg-[#00288e] transition-all duration-150 active:scale-[0.99] shadow-sm cursor-pointer">
                            <span className="material-symbols-outlined text-white text-lg">add_circle</span>
                            <span>Đăng tin mới</span>
                        </button>
                    </div>

                    {/* Nav Sections */}
                    <nav className="flex-1 space-y-4 pt-1 text-sm">
                        {/* 1. SINH VIÊN */}
                        <div>
                            <div className="px-3 py-1 text-xs font-bold tracking-wider text-slate-400 uppercase">
                                SINH VIÊN
                            </div>
                            <div className="space-y-0.5 mt-1">
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">search</span><span>Tìm việc làm</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">auto_awesome</span><span>Gợi ý việc làm</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">bookmark</span><span>Việc đã lưu</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">person</span><span>Hồ sơ cá nhân</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">description</span><span>Quản lý CV</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">send</span><span>Đơn ứng tuyển</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">mail</span><span>Lời mời phỏng vấn</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">school</span><span>Theo dõi thực tập</span></a>
                            </div>
                        </div>

                        {/* 2. DOANH NGHIỆP */}
                        <div>
                            <div className="px-3 py-1 text-xs font-bold tracking-wider text-slate-400 uppercase">
                                DOANH NGHIỆP
                            </div>
                            <div className="space-y-0.5 mt-1">
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">rate_review</span><span>Tin tuyển dụng</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">groups</span><span>Quản lý ứng viên</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">person_search</span><span>Gợi ý ứng viên</span></a>
                                <a className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-50 text-[#00288e] font-bold border-l-4 border-[#00288e]" href="#">
                                    <span className="material-symbols-outlined text-[#00288e] text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>mark_email_read</span>
                                    <span>Lời mời đã gửi</span>
                                </a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">domain</span><span>Hồ sơ công ty</span></a>
                            </div>
                        </div>

                        {/* 3. NHÀ TRƯỜNG / ADMIN */}
                        <div>
                            <div className="px-3 py-1 text-xs font-bold tracking-wider text-slate-400 uppercase">
                                NHÀ TRƯỜNG / ADMIN
                            </div>
                            <div className="space-y-0.5 mt-1">
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">insights</span><span>Tổng quan hệ thống</span></a>
                                <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" href="#"><span className="material-symbols-outlined text-lg">badge</span><span>Quản lý sinh viên</span></a>
                            </div>
                        </div>
                    </nav>

                    {/* Footer Tabs */}
                    <div className="pt-3 border-t border-slate-200 space-y-1 text-sm mt-auto">
                        <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="#"><span className="material-symbols-outlined text-lg">settings</span><span>Cài đặt hệ thống</span></a>
                        <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="#"><span className="material-symbols-outlined text-lg">help</span><span>Hỗ trợ & Trợ giúp</span></a>
                    </div>
                </div>
            </aside>

            <div className="min-h-screen w-full bg-slate-50 text-slate-900 font-sans antialiased relative">
            {/* ==================== MAIN CONTENT WRAPPER (CÓ PADDING LEFT 260px) ==================== */}
            <div className="pl-[280px] flex flex-col min-h-screen">
                {/* Top Navigation Bar */}
                <header className="sticky top-0 right-0 z-30 flex items-center justify-between w-full h-16 px-6 bg-white border-b border-slate-200 shadow-sm">
                    <div className="flex items-center gap-4 flex-1 max-w-lg">
                        <div className="relative w-full">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
                            <input className="w-full pl-10 pr-4 py-1.5 rounded-lg border border-slate-200 text-sm placeholder:text-slate-400 focus:outline-none focus:border-[#1e40af] focus:ring-1 focus:ring-[#1e40af] bg-slate-50 transition-all" placeholder="Tìm theo tên sinh viên, kỹ năng hoặc vị trí tuyển dụng..." type="text" />
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={handleOpenModal} className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-50 text-[#00288e] font-semibold hover:bg-blue-100 transition-colors cursor-pointer text-sm">
                            <span className="material-symbols-outlined">add_task</span>
                            <span>Tạo phỏng vấn</span>
                        </button>
                        <div className="h-6 w-px bg-slate-200 mx-1"></div>
                        <button className="relative p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">
                            <span className="material-symbols-outlined">notifications</span>
                            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-600"></span>
                        </button>
                        <button className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer">
                            <span className="material-symbols-outlined">help_outline</span>
                        </button>
                        <div className="flex items-center gap-3 pl-2 ml-1 cursor-pointer">
                            <img className="w-9 h-9 rounded-full object-cover border border-slate-200" src="https://lh3.googleusercontent.com/aida-public/AB6AXuD9fnbnyuC0oMyWXuyCy3J2yF8uSWSElztPVLBPjlwLHOIjVZOQy2-S4xQHX_AqjLlsoP6RkuIOwyVwGThjTR6-HEjFKpM7RCYubYAJhGB1nlnw1IGplRx2ghN9czc-zE83uA0LACErbcfRLnv158pHaYyO5h5XWo_K8SY9plGzuvx8GylMaaw3Y3Mz3V1p2XQYtWSXx2LawCz7lMllVO9n1t4-Z5uIDjGY0rohloE" alt="Khôi HR Lead" />
                            <div className="hidden lg:flex flex-col text-left">
                                <span className="text-sm font-semibold leading-tight text-slate-900">Khôi (HR Lead)</span>
                                <span className="text-xs text-slate-400">FPT Software JSC</span>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Main Workspace */}
                <main className="p-8 space-y-6 flex-1 bg-slate-50">
                    {/* Header Section */}
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                            <div className="flex items-center gap-2">
                                <h1 className="text-2xl font-bold text-slate-900">Quản lý lời mời đã gửi</h1>
                                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-[#00288e] border border-blue-200">Đợt Hè 2025</span>
                            </div>
                            <p className="text-sm text-slate-600 mt-1">
                                Theo dõi tình trạng phản hồi lời mời ứng tuyển trực tiếp đến sinh viên đang bật tìm việc (Open to work)
                            </p>
                        </div>
                        <button onClick={handleOpenModal} className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#1e40af] text-white font-semibold hover:bg-[#00288e] transition-all duration-150 active:scale-[0.98] shadow-sm cursor-pointer text-sm">
                            <span className="material-symbols-outlined text-white">forward_to_inbox</span>
                            <span>+ Gửi lời mời mới</span>
                        </button>
                    </div>

                    {/* KPI Metrics Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-[#00288e] transition-colors">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Tổng lời mời đã gửi</span>
                                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-[#00288e]">
                                    <span className="material-symbols-outlined">outgoing_mail</span>
                                </div>
                            </div>
                            <div className="mt-3">
                                <span className="text-3xl font-bold text-slate-900">{invitations.length + 40}</span>
                                <div className="flex items-center gap-1.5 mt-1 text-xs font-semibold text-[#00288e]">
                                    <span className="material-symbols-outlined text-sm">trending_up</span>
                                    <span>+18% so với tuần trước</span>
                                </div>
                            </div>
                            <div className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-100">
                                Áp dụng cho 6 vị trí thực tập đang tuyển
                            </div>
                        </div>

                        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-green-600 transition-colors">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Đã chấp nhận & nộp đơn</span>
                                <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center text-green-700">
                                    <span className="material-symbols-outlined">check_circle</span>
                                </div>
                            </div>
                            <div className="mt-3">
                                <div className="flex items-baseline gap-2">
                                    <span className="text-3xl font-bold text-slate-900">{invitations.filter(i => i.status === 'ACCEPTED').length + 26}</span>
                                    <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">Tỷ lệ 62.2%</span>
                                </div>
                                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2">
                                    <div className="bg-green-600 h-1.5 rounded-full" style={{ width: '62.2%' }}></div>
                                </div>
                            </div>
                            <div className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-100">
                                21 sinh viên đã bước vào vòng Phỏng vấn kỹ thuật
                            </div>
                        </div>

                        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-amber-500 transition-colors">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Đang chờ phản hồi</span>
                                <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-700">
                                    <span className="material-symbols-outlined">pending</span>
                                </div>
                            </div>
                            <div className="mt-3">
                                <span className="text-3xl font-bold text-slate-900">{invitations.filter(i => i.status === 'PENDING').length + 10}</span>
                                <div className="flex items-center gap-1.5 mt-1 text-xs text-amber-800">
                                    <span className="material-symbols-outlined text-sm">schedule</span>
                                    <span>Thời gian hết hạn trung bình: 48h</span>
                                </div>
                            </div>
                            <div className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-100">
                                Hệ thống tự động nhắc nhở sau 3 ngày
                            </div>
                        </div>

                        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-rose-500 transition-colors">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Sinh viên từ chối</span>
                                <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center text-rose-700">
                                    <span className="material-symbols-outlined">cancel</span>
                                </div>
                            </div>
                            <div className="mt-3">
                                <span className="text-3xl font-bold text-slate-900">{invitations.filter(i => i.status === 'REJECTED').length + 4}</span>
                                <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-600">
                                    <span>Tỷ lệ từ chối: 11.1% (Thấp)</span>
                                </div>
                            </div>
                            <div className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-100">
                                3 do đã nhận offer khác, 2 không phù hợp thời gian
                            </div>
                        </div>
                    </div>

                    {/* Filter Controls Bar */}
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3 text-sm">
                        <div className="flex flex-wrap items-center gap-3">
                            <select className="rounded-lg border border-slate-300 py-2 pl-3 pr-8 bg-white focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e] text-slate-900 cursor-pointer">
                                <option value="all">Tất cả tin tuyển dụng (6)</option>
                                <option value="fe">Frontend Intern (React/Next.js)</option>
                                <option value="be">Backend Node.js & Go Developer</option>
                            </select>
                            <select className="rounded-lg border border-slate-300 py-2 pl-3 pr-8 bg-white focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e] text-slate-900 cursor-pointer">
                                <option value="all">Tất cả trạng thái</option>
                                <option value="accepted">Đã nộp đơn (28)</option>
                                <option value="pending">Đang chờ phản hồi (12)</option>
                                <option value="rejected">Đã từ chối (5)</option>
                            </select>
                            <select className="rounded-lg border border-slate-300 py-2 pl-3 pr-8 bg-white focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e] text-slate-900 cursor-pointer">
                                <option value="all">Tất cả trường ĐH</option>
                                <option value="bk">ĐH Bách Khoa (HUST / VNU-HCM)</option>
                                <option value="uit">ĐH Công Nghệ Thông Tin (UIT)</option>
                            </select>
                        </div>
                        <div className="flex items-center gap-2">
                            <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer">
                                <span className="material-symbols-outlined text-sm">file_download</span>
                                <span>Xuất Excel</span>
                            </button>
                        </div>
                    </div>

                    {/* Sent Invitations Table */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-400 tracking-wider font-bold">
                                        <th className="py-3 px-4">Ứng viên được mời</th>
                                        <th className="py-3 px-4">Vị trí mời tuyển</th>
                                        <th className="py-3 px-4">Ngày gửi</th>
                                        <th className="py-3 px-4">Trạng thái</th>
                                        <th className="py-3 px-4 min-w-[220px]">Lời nhắn gửi kèm</th>
                                        <th className="py-3 px-4 text-right">Thao tác</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 text-sm">
                                    {invitations.map((inv) => (
                                        <tr key={inv.id} className="hover:bg-slate-50/70 transition-colors">
                                            <td className="py-3.5 px-4">
                                                <div className="flex items-center gap-3">
                                                    <img src={inv.studentAvatar} alt={inv.studentName} className="w-10 h-10 rounded-full object-cover border border-slate-200" />
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-bold text-slate-900">{inv.studentName}</span>
                                                            {inv.isVerifiedOpen && (
                                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                                                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
                                                                    Open to Work
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="text-xs text-slate-400">{inv.studentMeta} (ID: {inv.studentId})</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-3.5 px-4">
                                                <div className="font-semibold text-slate-900">{inv.jobTitle}</div>
                                                <div className="text-xs text-slate-400">{inv.jobCode}</div>
                                            </td>
                                            <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap text-xs">{inv.sentTime}</td>
                                            <td className="py-3.5 px-4 whitespace-nowrap">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${inv.statusBadge}`}>
                                                    {inv.statusText}
                                                </span>
                                            </td>
                                            <td className="py-3.5 px-4 text-slate-600 max-w-xs truncate" title={inv.message}>
                                                <span className="italic">"{inv.message}"</span>
                                            </td>
                                            <td className="py-3.5 px-4 text-right whitespace-nowrap">
                                                <div className="flex items-center justify-end gap-1.5">
                                                    {inv.status === 'ACCEPTED' ? (
                                                        <button className="px-2.5 py-1.5 rounded bg-[#1e40af] text-white hover:bg-[#00288e] transition-colors inline-flex items-center gap-1 text-xs font-semibold cursor-pointer">
                                                            <span className="material-symbols-outlined text-sm">assignment_ind</span>
                                                            Xem đơn
                                                        </button>
                                                    ) : inv.status === 'PENDING' ? (
                                                        <button onClick={() => alert(`Đã gửi thông báo nhắc nhở đến sinh viên ${inv.studentName}!`)} className="px-2.5 py-1.5 rounded border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors inline-flex items-center gap-1 text-xs font-semibold cursor-pointer">
                                                            <span className="material-symbols-outlined text-sm">notification_important</span>
                                                            Nhắc nhở
                                                        </button>
                                                    ) : (
                                                        <span className="text-xs text-slate-400 italic">Đã đóng</span>
                                                    )}
                                                    <button className="p-1.5 rounded text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer" title="Xem hồ sơ">
                                                        <span className="material-symbols-outlined text-lg">visibility</span>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="px-4 py-3 bg-white border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                            <div>Hiển thị <span className="font-semibold text-slate-900">1 - {invitations.length}</span> trên tổng số <span className="font-semibold text-slate-900">45</span> lời mời</div>
                            <div className="flex items-center gap-1">
                                <button className="px-3 py-1 rounded border border-slate-200 opacity-60 cursor-not-allowed">Trước</button>
                                <button className="px-3 py-1 rounded bg-[#00288e] text-white font-semibold">1</button>
                                <button className="px-3 py-1 rounded border border-slate-200 hover:bg-slate-50">Sau</button>
                            </div>
                        </div>
                    </div>
                </main>
            </div>

            {/* ========================================== */}
            {/* MODAL: GỬI LỜI MỜI ỨNG TUYỂN TRỰC TIẾP       */}
            {/* ========================================== */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-xl mx-4 overflow-hidden animate-in fade-in duration-200">
                        {/* Modal Header */}
                        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                            <div className="flex items-center gap-2.5">
                                <div className="w-9 h-9 rounded-lg bg-[#1e40af] text-white flex items-center justify-center">
                                    <span className="material-symbols-outlined">forward_to_inbox</span>
                                </div>
                                <div>
                                    <h3 className="text-base font-bold text-slate-900">Gửi lời mời ứng tuyển trực tiếp</h3>
                                    <p className="text-xs text-slate-500">Gửi đề xuất thực tập đến sinh viên ưu tú với mã định danh lời mời</p>
                                </div>
                            </div>
                            <button onClick={handleCloseModal} className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer">
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto text-sm">
                            {/* Chọn vị trí tuyển dụng */}
                            <div>
                                <label className="block font-semibold text-slate-900 mb-1.5">
                                    Chọn vị trí tuyển dụng <span className="text-red-500">*</span> <span className="text-xs text-slate-400 font-normal">(`jobId` đang mở)</span>
                                </label>
                                <select 
                                    value={selectedJobId} 
                                    onChange={(e) => setSelectedJobId(e.target.value)}
                                    className="w-full rounded-lg border border-slate-300 py-2.5 pl-3.5 pr-8 bg-white focus:border-[#1e40af] focus:ring-1 focus:ring-[#1e40af] text-slate-900 cursor-pointer"
                                >
                                    <option value="JOB-FE-2025">Frontend Intern (React/Next.js) • 4 chỉ tiêu còn lại</option>
                                    <option value="JOB-BE-104">Backend Node.js & Go Developer • 2 chỉ tiêu còn lại</option>
                                    <option value="JOB-AI-881">AI / Machine Learning Research Intern • 1 chỉ tiêu còn lại</option>
                                    <option value="JOB-QA-330">QC & Automation QA Tester • 3 chỉ tiêu còn lại</option>
                                </select>
                            </div>

                            {/* Thông tin sinh viên */}
                            <div>
                                <label className="block font-semibold text-slate-900 mb-1.5">
                                    Ứng viên được chọn <span className="text-red-500">*</span> <span className="text-xs text-slate-400 font-normal">(`studentId: {selectedStudentId}`)</span>
                                </label>
                                <div className="p-3.5 rounded-xl border border-blue-200 bg-blue-50/40 flex items-start justify-between gap-3">
                                    <div className="flex items-center gap-3">
                                        <img 
                                            src="https://lh3.googleusercontent.com/aida-public/AB6AXuCapgL7JDVLYPUfcXuxE-TZOLx2-Hf3pap_B80qoEikLWGVIZF7XwuvWK9p83F0Kk4imY8pyQa9bBpqkisYkuZp4FHBLuG6FPfdayGA7KeNtY7hR9NolAR30wdY7T1r4HzP_esDjTld4USfQOmwtXGJjUlhxBiNYF-6xWFzXXMvFNUXzA5Y75Yb88rh1SGWz_pKal-A7lMj05oUGdzZsgfUic28j3BKESTuxoZr1Nw" 
                                            alt="Minh Đức" 
                                            className="w-12 h-12 rounded-full object-cover border-2 border-[#1e40af]"
                                        />
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-bold text-slate-900">Nguyễn Minh Đức</span>
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
                                                    Open to Work
                                                </span>
                                            </div>
                                            <div className="text-xs text-slate-500">ĐH Bách Khoa • Khoa Khoa học Máy tính</div>
                                            <div className="flex flex-wrap gap-1.5 mt-1.5">
                                                <span className="px-2 py-0.5 rounded bg-white text-xs font-semibold text-[#00288e] border border-slate-200">ReactJS</span>
                                                <span className="px-2 py-0.5 rounded bg-white text-xs font-semibold text-[#00288e] border border-slate-200">NodeJS</span>
                                                <span className="px-2 py-0.5 rounded bg-white text-xs font-semibold text-[#00288e] border border-slate-200">TypeScript</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="px-2 py-1 rounded-lg bg-[#00288e] text-white text-xs font-bold flex items-center gap-1 shadow-sm">
                                            <span className="material-symbols-outlined text-xs">psychology</span>
                                            Match 94%
                                        </span>
                                        <span className="text-[11px] text-slate-400 mt-1">Đánh giá bởi AI</span>
                                    </div>
                                </div>
                            </div>

                            {/* Lời nhắn mời ứng tuyển */}
                            <div>
                                <div className="flex items-center justify-between mb-1.5">
                                    <label className="block font-semibold text-slate-900">
                                        Lời nhắn mời ứng tuyển <span className="text-red-500">*</span>
                                    </label>
                                    <div className="flex items-center gap-1 text-xs">
                                        <span className="text-slate-400">Gợi ý mẫu:</span>
                                        <button onClick={() => handleSetTemplate(1)} className="text-[#1e40af] underline hover:text-blue-800 font-semibold cursor-pointer" type="button">Khen ngợi đồ án</button>
                                        <span className="text-slate-400">•</span>
                                        <button onClick={() => handleSetTemplate(2)} className="text-[#1e40af] underline hover:text-blue-800 font-semibold cursor-pointer" type="button">Lời mời trực tiếp</button>
                                    </div>
                                </div>
                                <textarea 
                                    value={invitationMessage} 
                                    onChange={(e) => setInvitationMessage(e.target.value)}
                                    className="w-full rounded-lg border border-slate-300 p-3 focus:border-[#1e40af] focus:ring-1 focus:ring-[#1e40af] text-slate-900" 
                                    rows={4} 
                                />
                            </div>

                            <div className="p-3 bg-slate-100 rounded-lg border border-slate-200 flex items-start gap-2.5 text-xs text-slate-600">
                                <span className="material-symbols-outlined text-[#00288e] text-lg mt-0.5">info</span>
                                <div>
                                    <strong>Ghi chú hệ thống:</strong> Sinh viên sẽ nhận được thông báo đẩy và email tức thì với mã <code className="text-[#00288e] font-semibold">Invitation ID: #INV-2025-098</code> để được miễn vòng duyệt hồ sơ sơ loại.
                                </div>
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
                            <button onClick={handleCloseModal} className="px-4 py-2 rounded-lg border border-slate-300 bg-white text-slate-700 font-semibold hover:bg-slate-100 transition-colors cursor-pointer text-sm" type="button">
                                Hủy bỏ
                            </button>
                            <button onClick={handleSendInvitation} className="px-5 py-2 rounded-lg bg-[#1e40af] hover:bg-[#00288e] text-white font-semibold transition-all shadow-sm flex items-center gap-2 text-sm cursor-pointer" type="button">
                                <span className="material-symbols-outlined text-white text-lg">send</span>
                                <span>Gửi lời mời ngay</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {showToast && (
                <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-xl transition-all duration-300">
                    <span className="material-symbols-outlined text-emerald-400">check_circle</span>
                    <div className="text-sm">
                        <span className="font-bold">Thành công!</span> Đã gửi lời mời ứng tuyển đến sinh viên <strong>Nguyễn Minh Đức</strong>.
                    </div>
                </div>
            )}
            </div>
        </>
    );
};
