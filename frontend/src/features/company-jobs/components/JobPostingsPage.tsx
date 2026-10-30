import React, { useState } from 'react';

interface JobPosting {
    id: string;
    code: string;
    title: string;
    type: string;
    term: string;
    startDate: string;
    quota: string;
    status: 'OPEN' | 'PENDING' | 'DRAFT' | 'CLOSED';
    statusText: string;
    statusBadge: string;
    subText: string;
    deadline: string;
    skills: string[];
    stats?: {
        applications: number;
        views: number;
        matchRate: string;
    };
    isClosed?: boolean;
}

export const JobPostingsPage: React.FC = () => {
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<string>('ALL');
    const [searchKeyword, setSearchKeyword] = useState('');
    const [selectedCohort, setSelectedCohort] = useState('Đợt Fall 2026');
    const [selectedIndustry, setSelectedIndustry] = useState('Tất cả ngành nghề');

    // Dữ liệu danh sách tin tuyển dụng đầy đủ 5 trạng thái
    const [jobs, setJobs] = useState<JobPosting[]>([
        {
            id: '1',
            code: 'JD-2026-081',
            title: 'Thực tập sinh Lập trình Frontend (ReactJS / Tailwind)',
            type: 'Full-time',
            term: 'Fall 2026',
            startDate: 'Bắt đầu: 15/09/2026',
            quota: '05 SV',
            status: 'OPEN',
            statusText: 'Đang mở nhận hồ sơ',
            statusBadge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
            subText: 'ĐH Bách Khoa, RMIT, FPT',
            deadline: '30/11/2026',
            skills: ['React', 'TypeScript'],
            stats: { applications: 42, views: 380, matchRate: '88%' }
        },
        {
            id: '2',
            code: 'JD-2026-094',
            title: 'Thực tập sinh Trí tuệ nhân tạo (AI / Data Science Engineer)',
            type: 'Hybrid',
            term: 'Fall 2026',
            startDate: 'Bắt đầu: 15/09/2026',
            quota: '03 SV',
            status: 'PENDING',
            statusText: 'Chờ Ban HTDN ĐH duyệt',
            statusBadge: 'bg-amber-100 text-amber-900 border-amber-300',
            subText: 'Đã gửi: 2 ngày trước',
            deadline: '15/12/2026',
            skills: ['Python', 'PyTorch', 'LLMs']
        },
        {
            id: '3',
            code: 'JD-2026-102',
            title: 'Thực tập sinh Thiết kế UI/UX Sản phẩm (Product Design Intern)',
            type: 'Part-time',
            term: 'Fall 2026',
            startDate: 'Chưa khóa đợt',
            quota: '02 SV',
            status: 'DRAFT',
            statusText: 'Bản nháp nội bộ',
            statusBadge: 'bg-slate-100 text-slate-700 border-slate-300',
            subText: 'Cập nhật 3 giờ trước',
            deadline: 'Chưa cài hạn',
            skills: ['Figma', 'User Research']
        },
        {
            id: '4',
            code: 'JD-2026-077',
            title: 'Thực tập sinh Backend Developer (Node.js / PostgreSQL / AWS)',
            type: 'Full-time',
            term: 'Fall 2026',
            startDate: 'Bắt đầu: 15/09/2026',
            quota: '04 SV',
            status: 'OPEN',
            statusText: 'Đang mở nhận hồ sơ',
            statusBadge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
            subText: 'ĐH Công nghệ, Sư phạm Kỹ thuật',
            deadline: '20/11/2026',
            skills: ['Node.js', 'SQL'],
            stats: { applications: 29, views: 245, matchRate: '91%' }
        },
        {
            id: '5',
            code: 'JD-2026-052',
            title: 'Thực tập sinh Kiểm thử Phần mềm (Manual / Automation QA)',
            type: 'Full-time',
            term: 'Spring 2026',
            startDate: 'Đã hoàn thành đợt',
            quota: '03 / 03 SV',
            status: 'CLOSED',
            statusText: 'Đã đóng (Đủ chỉ tiêu)',
            statusBadge: 'bg-rose-100 text-rose-800 border-rose-200',
            subText: 'Đã đóng ngày 10/10/2026',
            deadline: '10/10/2026',
            skills: ['QA', 'Testing'],
            stats: { applications: 54, views: 420, matchRate: '85%' },
            isClosed: true
        }
    ]);

    // Form state trong Drawer
    const [formTitle, setFormTitle] = useState('Thực tập sinh Lập trình viên AI & Data Science (Kỳ Fall 2026)');
    const [formQuota, setFormQuota] = useState('5');
    const [formType, setFormType] = useState('Toàn thời gian (Full-time)');
    const [formDeadline, setFormDeadline] = useState('2026-11-30');

    const openDrawer = () => setIsDrawerOpen(true);
    const closeDrawer = () => setIsDrawerOpen(false);

    // Chức năng: Lưu nháp
    const saveDraft = () => {
        const newJob: JobPosting = {
            id: String(Date.now()),
            code: `JD-2026-${Math.floor(100 + Math.random() * 900)}`,
            title: formTitle,
            type: formType.includes('Full') ? 'Full-time' : 'Part-time',
            term: 'Fall 2026',
            startDate: 'Chưa khóa đợt',
            quota: `${formQuota} SV`,
            status: 'DRAFT',
            statusText: 'Bản nháp nội bộ',
            statusBadge: 'bg-slate-100 text-slate-700 border-slate-300',
            subText: 'Vừa lưu nháp',
            deadline: formDeadline,
            skills: ['Python', 'AI']
        };
        setJobs([newJob, ...jobs]);
        alert("Đã lưu bản nháp thành công vào hệ thống nội bộ doanh nghiệp!");
        closeDrawer();
    };

    // Chức năng: Gửi nhà trường duyệt
    const submitReview = () => {
        const newJob: JobPosting = {
            id: String(Date.now()),
            code: `JD-2026-${Math.floor(100 + Math.random() * 900)}`,
            title: formTitle,
            type: formType.includes('Full') ? 'Full-time' : 'Hybrid',
            term: 'Fall 2026',
            startDate: 'Bắt đầu: 15/09/2026',
            quota: `${formQuota} SV`,
            status: 'PENDING',
            statusText: 'Chờ Ban HTDN ĐH duyệt',
            statusBadge: 'bg-amber-100 text-amber-900 border-amber-300',
            subText: 'Đã gửi: Vừa xong',
            deadline: formDeadline,
            skills: ['Python', 'AI']
        };
        setJobs([newJob, ...jobs]);
        alert("Đã gửi tin tuyển dụng tới Ban Hợp tác Doanh nghiệp các trường Đại học để phê duyệt!");
        closeDrawer();
    };

    // Chức năng: Đóng tin
    const handleCloseJob = (id: string) => {
        setJobs(jobs.map(j => j.id === id ? {
            ...j,
            status: 'CLOSED',
            statusText: 'Đã đóng (Đủ chỉ tiêu)',
            statusBadge: 'bg-rose-100 text-rose-800 border-rose-200',
            subText: 'Đã đóng thủ công',
            isClosed: true
        } : j));
        alert("Đã đóng tin tuyển dụng thành công.");
    };

    // Lọc danh sách theo Tab trạng thái và từ khóa tìm kiếm
    const filteredJobs = jobs.filter(job => {
        if (activeTab !== 'ALL' && job.status !== activeTab) return false;
        if (searchKeyword && !job.title.toLowerCase().includes(searchKeyword.toLowerCase()) && !job.code.toLowerCase().includes(searchKeyword.toLowerCase())) {
            return false;
        }
        return true;
    });

    // Thống kê đếm số lượng cho KPI
    const counts = {
        all: jobs.length,
        open: jobs.filter(j => j.status === 'OPEN').length,
        pending: jobs.filter(j => j.status === 'PENDING').length,
        draft: jobs.filter(j => j.status === 'DRAFT').length,
        closed: jobs.filter(j => j.status === 'CLOSED').length,
    };

    return (
        <div className="h-full bg-slate-50 text-slate-900 font-sans antialiased overflow-x-hidden">
            {/* ======================================================== */}
            {/* 1. LEFT SIDEBAR NAVIGATION                               */}
            {/* ======================================================== */}
            <aside className="fixed left-0 top-0 h-full w-[260px] z-40 bg-white border-r border-slate-200 flex flex-col justify-between overflow-y-auto">
                <div className="p-4 flex flex-col gap-6">
                    <div className="flex items-center gap-3 px-2 py-1">
                        <div className="w-10 h-10 rounded-lg bg-[#00288e] flex items-center justify-center text-white shadow-sm">
                            <span className="material-symbols-outlined text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>hub</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="font-bold text-[#00288e] text-base tracking-tight">Student Connect</span>
                            <span className="text-xs text-slate-400 font-medium">Enterprise Portal</span>
                        </div>
                    </div>

                    <button 
                        onClick={openDrawer}
                        className="w-full bg-[#00288e] hover:bg-blue-800 text-white font-semibold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer text-sm"
                    >
                        <span className="material-symbols-outlined text-lg">add_circle</span>
                        <span>Đăng tin mới</span>
                    </button>

                    <nav className="flex flex-col gap-5">
                        <div className="flex flex-col gap-1">
                            <div className="px-3 pb-1 text-slate-400 text-[11px] font-bold uppercase tracking-wider">SINH VIÊN</div>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">search</span><span>Tìm việc làm</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">auto_awesome</span><span>Gợi ý việc làm</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">bookmark</span><span>Việc đã lưu</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">person</span><span>Hồ sơ cá nhân</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">description</span><span>Quản lý CV</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">send</span><span>Đơn ứng tuyển</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">mail</span><span>Lời mời phỏng vấn</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">school</span><span>Theo dõi thực tập</span></a>
                        </div>

                        <div className="flex flex-col gap-1">
                            <div className="px-3 pb-1 text-slate-400 text-[11px] font-bold uppercase tracking-wider">DOANH NGHIỆP</div>
                            <a className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-50 text-[#00288e] text-sm font-bold border-l-4 border-[#00288e] shadow-sm cursor-pointer" href="#">
                                <span className="material-symbols-outlined text-[#00288e]" style={{ fontVariationSettings: "'FILL' 1" }}>assignment</span>
                                <span>Tin tuyển dụng</span>
                            </a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">groups</span><span>Quản lý ứng viên</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">person_search</span><span>Gợi ý ứng viên</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">mark_email_read</span><span>Lời mời đã gửi</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">domain</span><span>Hồ sơ công ty</span></a>
                        </div>

                        <div className="flex flex-col gap-1">
                            <div className="px-3 pb-1 text-slate-400 text-[11px] font-bold uppercase tracking-wider">NHÀ TRƯỜNG / ADMIN</div>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">monitoring</span><span>Tổng quan hệ thống</span></a>
                            <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">badge</span><span>Quản lý sinh viên</span></a>
                        </div>
                    </nav>
                </div>

                <div className="p-4 border-t border-slate-200 bg-white flex flex-col gap-1">
                    <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">settings</span><span>Cài đặt hệ thống</span></a>
                    <a className="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#"><span className="material-symbols-outlined text-slate-500">help</span><span>Hỗ trợ & Trợ giúp</span></a>
                    <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-3 px-2">
                        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-[#00288e] font-bold text-sm">F</div>
                        <div className="flex flex-col min-w-0">
                            <span className="text-sm font-bold text-slate-900 truncate">FPT Software Corp</span>
                            <span className="text-xs text-slate-500 truncate">Khôi (Talent Lead)</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* ======================================================== */}
            {/* 2. TOP NAV BAR (STICKY HEADER)                           */}
            {/* ======================================================== */}
            <header className="sticky top-0 right-0 z-30 flex items-center justify-between w-[calc(100%-260px)] ml-[260px] h-16 px-8 bg-white border-b border-slate-200 shadow-sm">
                <div className="relative w-96">
                    <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">search</span>
                    <input 
                        value={searchKeyword}
                        onChange={(e) => setSearchKeyword(e.target.value)}
                        className="w-full h-10 pl-10 pr-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00288e] focus:bg-white transition-all" 
                        placeholder="Tìm kiếm tin tuyển dụng, mã tin, kỹ năng..." 
                        type="text"
                    />
                </div>
                <div className="flex items-center gap-4">
                    <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-[#00288e] border border-blue-200 rounded-lg text-xs font-semibold">
                        <span className="material-symbols-outlined text-base">calendar_month</span>
                        <span>Kỳ thực tập: Fall 2026</span>
                    </div>
                    <button className="flex items-center gap-2 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-semibold rounded-lg transition-colors cursor-pointer">
                        <span className="material-symbols-outlined text-lg">event</span>
                        <span>Tạo phỏng vấn</span>
                    </button>
                    <button className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer" title="Thông báo hệ thống">
                        <span className="material-symbols-outlined">notifications</span>
                        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
                    </button>
                    <button className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer" title="Trợ giúp">
                        <span className="material-symbols-outlined">help_outline</span>
                    </button>
                    <div className="h-6 w-px bg-slate-200"></div>
                    <div className="flex items-center gap-3 pl-1 cursor-pointer">
                        <img className="w-9 h-9 rounded-full object-cover border border-slate-200" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBp6Zy3FmkkYlvesUoRVKlG1nkVjs1lT6LjSaUmjwr1vZT0-dNzw3vziPyLzMv2VUTn3iiAQSXLoX2oxAKQGCSOz7CXaMEe7gowouV5wBx7hqRSXAbmzzKYmE2u5mIVwZysopYOyr3y2ifw_5m25XZjGnbdC1RFVfV6DusUj6ZGkm3OZLAbUAA943mCV5-r96gc294OxsrMbxM6Bm1dP2JHFEmpOQ-ohiCUXxzZekY" alt="Đặng Văn Khôi"/>
                        <div className="hidden lg:flex flex-col text-left">
                            <span className="text-sm font-bold text-slate-900 leading-tight">Đặng Văn Khôi</span>
                            <span className="text-xs text-slate-500">Phụ trách Doanh nghiệp</span>
                        </div>
                        <span className="material-symbols-outlined text-slate-400 text-lg">expand_more</span>
                    </div>
                </div>
            </header>

            {/* ======================================================== */}
            {/* 3. MAIN WORKSPACE CANVAS                                -->
            {/* ======================================================== */}
            <main className="w-[calc(100%-260px)] ml-[260px] min-h-[calc(100vh-64px)] p-8 flex flex-col gap-6">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-[30px] font-bold text-slate-900 tracking-tight">Tin tuyển dụng của tôi</h1>
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                                Học kỳ Fall 2026 đang mở
                            </span>
                        </div>
                        <p className="text-sm text-slate-500 mt-1">
                            Quản lý danh sách đăng tuyển, gửi phê duyệt Nhà trường và theo dõi hiệu quả tiếp cận thực tập sinh.
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-sm font-semibold rounded-lg shadow-sm transition-all cursor-pointer">
                            <span className="material-symbols-outlined text-lg">download</span>
                            <span>Xuất báo cáo</span>
                        </button>
                        <button 
                            onClick={openDrawer}
                            className="flex items-center gap-2 px-4 py-2.5 bg-[#00288e] hover:bg-blue-800 text-white text-sm font-semibold rounded-lg shadow-sm transition-all cursor-pointer"
                        >
                            <span className="material-symbols-outlined text-lg">add</span>
                            <span>Đăng tin mới</span>
                        </button>
                    </div>
                </div>

                {/* KPI STATS CARDS GRID */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">TỔNG TIN ĐĂNG</span>
                            <span className="p-1.5 rounded-lg bg-slate-100 text-slate-600"><span className="material-symbols-outlined text-lg">folder_open</span></span>
                        </div>
                        <div className="my-2">
                            <span className="text-[36px] font-bold text-slate-900 tabular-nums">{counts.all}</span>
                            <span className="text-xs text-slate-500 ml-1">vị trí</span>
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-1">
                            <span className="text-emerald-600 font-semibold flex items-center"><span className="material-symbols-outlined text-xs">trending_up</span> +3</span>
                            <span>so với kỳ Spring 2026</span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-gradient-to-br from-white to-emerald-50/20 shadow-sm flex flex-col justify-between">
                        <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">ĐANG MỞ TUYỂN</span>
                            <span className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700"><span className="material-symbols-outlined text-lg">check_circle</span></span>
                        </div>
                        <div className="my-2">
                            <span className="text-[36px] font-bold text-emerald-950 tabular-nums">{counts.open}</span>
                            <span className="text-xs text-emerald-700 ml-1">đang nhận hồ sơ</span>
                        </div>
                        <div className="text-xs text-emerald-700 flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            <span>Hiển thị trên Cổng SV</span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-amber-200 bg-gradient-to-br from-white to-amber-50/20 shadow-sm flex flex-col justify-between">
                        <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">CHỜ NHÀ TRƯỜNG DUYỆT</span>
                            <span className="p-1.5 rounded-lg bg-amber-100 text-amber-700"><span className="material-symbols-outlined text-lg">hourglass_top</span></span>
                        </div>
                        <div className="my-2">
                            <span className="text-[36px] font-bold text-amber-950 tabular-nums">{counts.pending}</span>
                            <span className="text-xs text-amber-700 ml-1">tin đang duyệt</span>
                        </div>
                        <div className="text-xs text-amber-700 flex items-center gap-1">
                            <span className="material-symbols-outlined text-xs">info</span>
                            <span>Ban HTDN Đại học xem xét</span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">BẢN NHÁP</span>
                            <span className="p-1.5 rounded-lg bg-slate-100 text-slate-600"><span className="material-symbols-outlined text-lg">edit_note</span></span>
                        </div>
                        <div className="my-2">
                            <span className="text-[36px] font-bold text-slate-900 tabular-nums">{counts.draft}</span>
                            <span className="text-xs text-slate-500 ml-1">chưa gửi duyệt</span>
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-1">
                            <span className="text-[#00288e] font-semibold">Cần hoàn thiện JD</span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                        <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">ĐÃ ĐÓNG / HẾT HẠN</span>
                            <span className="p-1.5 rounded-lg bg-rose-50 text-rose-600"><span className="material-symbols-outlined text-lg">do_not_disturb_on</span></span>
                        </div>
                        <div className="my-2">
                            <span className="text-[36px] font-bold text-slate-700 tabular-nums">{counts.closed}</span>
                            <span className="text-xs text-slate-500 ml-1">đã đủ chỉ tiêu</span>
                        </div>
                        <div className="text-xs text-rose-600 flex items-center gap-1">
                            <span className="material-symbols-outlined text-xs">archive</span>
                            <span>Đã lưu vào kho dữ liệu</span>
                        </div>
                    </div>
                </div>

                {/* FILTER & SEARCH CONTROL BAR */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col lg:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg w-full lg:w-auto overflow-x-auto">
                        <button onClick={() => setActiveTab('ALL')} className={`px-3.5 py-1.5 rounded-md text-sm font-semibold transition-colors whitespace-nowrap cursor-pointer ${activeTab === 'ALL' ? 'bg-white text-[#00288e] shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'}`}>
                            Tất cả ({counts.all})
                        </button>
                        <button onClick={() => setActiveTab('OPEN')} className={`px-3.5 py-1.5 rounded-md text-sm font-semibold transition-colors whitespace-nowrap cursor-pointer ${activeTab === 'OPEN' ? 'bg-white text-[#00288e] shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'}`}>
                            Đang mở ({counts.open})
                        </button>
                        <button onClick={() => setActiveTab('PENDING')} className={`px-3.5 py-1.5 rounded-md text-sm font-semibold transition-colors whitespace-nowrap cursor-pointer ${activeTab === 'PENDING' ? 'bg-white text-[#00288e] shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'}`}>
                            Chờ duyệt ({counts.pending})
                        </button>
                        <button onClick={() => setActiveTab('DRAFT')} className={`px-3.5 py-1.5 rounded-md text-sm font-semibold transition-colors whitespace-nowrap cursor-pointer ${activeTab === 'DRAFT' ? 'bg-white text-[#00288e] shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'}`}>
                            Bản nháp ({counts.draft})
                        </button>
                        <button onClick={() => setActiveTab('CLOSED')} className={`px-3.5 py-1.5 rounded-md text-sm font-semibold transition-colors whitespace-nowrap cursor-pointer ${activeTab === 'CLOSED' ? 'bg-white text-[#00288e] shadow-sm' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'}`}>
                            Đã đóng ({counts.closed})
                        </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
                        <div className="relative min-w-[170px]">
                            <select value={selectedCohort} onChange={(e) => setSelectedCohort(e.target.value)} className="w-full h-10 pl-3 pr-8 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-[#00288e] appearance-none cursor-pointer">
                                <option>Đợt Fall 2026</option>
                                <option>Đợt Spring 2026</option>
                                <option>Tất cả các đợt</option>
                            </select>
                            <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none text-sm">expand_more</span>
                        </div>
                        <div className="relative min-w-[170px]">
                            <select value={selectedIndustry} onChange={(e) => setSelectedIndustry(e.target.value)} className="w-full h-10 pl-3 pr-8 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-[#00288e] appearance-none cursor-pointer">
                                <option>Tất cả ngành nghề</option>
                                <option>Kỹ thuật Phần mềm</option>
                                <option>Trí tuệ nhân tạo (AI)</option>
                            </select>
                            <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none text-sm">expand_more</span>
                        </div>
                        <button className="h-10 px-3 bg-slate-50 hover:bg-slate-100 border border-slate-300 rounded-lg text-slate-600 flex items-center gap-1.5 text-sm transition-colors cursor-pointer">
                            <span className="material-symbols-outlined text-lg">tune</span>
                            <span className="hidden sm:inline">Bộ lọc</span>
                        </button>
                    </div>
                </div>

                {/* TABLE VIEW: DANH SÁCH TIN TUYỂN DỤNG */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[11px] font-bold uppercase tracking-wider">
                                    <th className="py-3.5 px-6">Vị trí tuyển dụng</th>
                                    <th className="py-3.5 px-4">Đợt thực tập</th>
                                    <th className="py-3.5 px-4 text-center">Chỉ tiêu</th>
                                    <th className="py-3.5 px-4">Trạng thái duyệt</th>
                                    <th className="py-3.5 px-6">Thống kê tương tác</th>
                                    <th className="py-3.5 px-6 text-right">Thao tác nghiệp vụ</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 text-sm">
                                {filteredJobs.map(job => (
                                    <tr key={job.id} className={`hover:bg-slate-50/70 transition-colors group ${job.isClosed ? 'opacity-80 bg-slate-50/40' : ''}`}>
                                        <td className="py-4 px-6">
                                            <div className="flex flex-col">
                                                <div className="flex items-center gap-2">
                                                    <span className={`text-base font-bold ${job.isClosed ? 'text-slate-600 line-through' : 'text-slate-900 group-hover:text-[#00288e]'} transition-colors`}>
                                                        {job.title}
                                                    </span>
                                                    <span className="px-2 py-0.5 text-[11px] font-semibold bg-blue-50 text-[#00288e] rounded border border-blue-200">{job.type}</span>
                                                </div>
                                                <div className="flex items-center gap-3 mt-1.5 text-slate-500 text-xs">
                                                    <span className="font-mono text-slate-400">#{job.code}</span>
                                                    <span>•</span>
                                                    <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm text-slate-400">schedule</span> Hạn: {job.deadline}</span>
                                                    <span>•</span>
                                                    <div className="flex items-center gap-1">
                                                        {job.skills.map(s => (
                                                            <span key={s} className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 text-xs">{s}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4 text-slate-700 whitespace-nowrap">
                                            <span className="font-semibold text-slate-800">{job.term}</span>
                                            <div className="text-xs text-slate-400">{job.startDate}</div>
                                        </td>
                                        <td className="py-4 px-4 text-center whitespace-nowrap">
                                            <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-blue-50 text-[#00288e] font-bold text-sm">{job.quota}</span>
                                        </td>
                                        <td className="py-4 px-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${job.statusBadge}`}>
                                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                                                {job.statusText}
                                            </span>
                                            <div className="text-[11px] text-slate-400 mt-1">{job.subText}</div>
                                        </td>
                                        <td className="py-4 px-6 whitespace-nowrap">
                                            {job.stats ? (
                                                <div className="flex items-center gap-4">
                                                    <div className="flex flex-col"><span className="text-slate-900 font-bold tabular-nums">{job.stats.applications}</span><span className="text-xs text-slate-400">Đơn nộp</span></div>
                                                    <div className="w-px h-6 bg-slate-200"></div>
                                                    <div className="flex flex-col"><span className="text-slate-900 font-bold tabular-nums">{job.stats.views}</span><span className="text-xs text-slate-400">Lượt xem</span></div>
                                                    <div className="w-px h-6 bg-slate-200"></div>
                                                    <div className="flex flex-col"><span className="text-emerald-700 font-bold tabular-nums">{job.stats.matchRate}</span><span className="text-xs text-slate-400">Độ khớp TB</span></div>
                                                </div>
                                            ) : (
                                                <span className="text-xs text-slate-400 italic">Chưa công khai trên cổng sinh viên</span>
                                            )}
                                        </td>
                                        <td className="py-4 px-6 text-right whitespace-nowrap">
                                            <div className="flex items-center justify-end gap-2">
                                                {job.status === 'OPEN' && (
                                                    <button className="px-3 py-1.5 rounded-lg bg-[#00288e] hover:bg-blue-800 text-white text-sm font-semibold transition-colors flex items-center gap-1 shadow-sm cursor-pointer">
                                                        <span className="material-symbols-outlined text-sm">groups</span>
                                                        <span>Ứng viên</span>
                                                    </button>
                                                )}
                                                {job.status === 'DRAFT' && (
                                                    <button onClick={submitReview} className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold transition-colors flex items-center gap-1 shadow-sm cursor-pointer">
                                                        <span className="material-symbols-outlined text-sm">send</span>
                                                        <span>Gửi duyệt</span>
                                                    </button>
                                                )}
                                                <button onClick={openDrawer} className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer" title="Chỉnh sửa tin">
                                                    <span className="material-symbols-outlined text-lg">edit</span>
                                                </button>
                                                {job.status !== 'CLOSED' && (
                                                    <button onClick={() => handleCloseJob(job.id)} className="p-1.5 text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer" title="Đóng tin tuyển dụng">
                                                        <span className="material-symbols-outlined text-lg">lock</span>
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="p-4 border-t border-slate-200 bg-white flex flex-col sm:flex-row items-center justify-between gap-4 text-slate-600 text-xs">
                        <div className="flex items-center gap-2">
                            <span>Hiển thị <strong>1 - {filteredJobs.length}</strong> trên tổng số <strong>{jobs.length}</strong> tin tuyển dụng</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <button className="p-1.5 rounded border border-slate-200 text-slate-400 hover:bg-slate-50 disabled:opacity-50" disabled><span className="material-symbols-outlined text-sm">chevron_left</span></button>
                            <button className="w-8 h-8 rounded bg-[#00288e] text-white font-bold text-xs flex items-center justify-center">1</button>
                            <button className="p-1.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-50"><span className="material-symbols-outlined text-sm">chevron_right</span></button>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-slate-400 pt-2 pb-6 border-t border-slate-200">
                    <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-[#00288e]">verified</span>
                        <span>Cổng kết nối Doanh nghiệp - Viện Đào tạo & Hợp tác Doanh nghiệp Quốc tế</span>
                    </div>
                    <div>Phiên bản Enterprise 2.6.4 • Hỗ trợ kỹ thuật: hotro@studentconnect.edu.vn</div>
                </div>
            </main>

            {/* ========================================================================= */}
            {/* 4. SLIDE-OVER DRAWER (MODAL TẠO/SỬA TIN)                                  */}
            {/* ========================================================================= */}
            {isDrawerOpen && (
                <>
                    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 transition-opacity" onClick={closeDrawer}></div>
                    <div className="fixed top-0 right-0 h-full w-full max-w-[620px] bg-white z-50 shadow-2xl flex flex-col justify-between border-l border-slate-200 animate-in slide-in-from-right duration-300">
                        <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-blue-100 text-[#00288e] flex items-center justify-center">
                                    <span className="material-symbols-outlined text-xl">post_add</span>
                                </div>
                                <div>
                                    <h2 className="text-base font-bold text-slate-900">Đăng tin tuyển dụng mới</h2>
                                    <p className="text-xs text-slate-500">Khởi tạo phiếu tuyển dụng để gửi Ban Hợp tác Đại học duyệt</p>
                                </div>
                            </div>
                            <button onClick={closeDrawer} className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer">
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto flex flex-col gap-6 text-sm text-slate-700 flex-1">
                            <div className="bg-blue-50/60 p-4 rounded-xl border border-blue-200 flex flex-col gap-3">
                                <div className="flex items-center gap-2 text-[#00288e] font-semibold text-sm">
                                    <span className="material-symbols-outlined text-lg">school</span>
                                    <span>Liên kết chương trình thực tập của trường</span>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="block text-xs font-semibold text-slate-700 mb-1">Học kỳ / Đợt áp dụng *</label>
                                        <select className="w-full h-10 px-3 bg-white border border-slate-300 rounded-lg text-sm text-slate-800">
                                            <option>Học kỳ Fall 2026 (09/2026 - 12/2026)</option>
                                            <option>Học kỳ Spring 2027 (01/2027 - 04/2027)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-semibold text-slate-700 mb-1">Mã tin tuyển dụng</label>
                                        <input className="w-full h-10 px-3 bg-slate-100 border border-slate-300 rounded-lg font-mono text-slate-600 text-xs cursor-not-allowed" readOnly value="JD-2026-FPT-08" />
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-800 mb-1.5">Tiêu đề vị trí tuyển dụng <span className="text-rose-500">*</span></label>
                                <input value={formTitle} onChange={(e) => setFormTitle(e.target.value)} className="w-full h-10 px-3.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-900 focus:ring-2 focus:ring-[#00288e]" type="text" />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">Số lượng cần tuyển <span className="text-rose-500">*</span></label>
                                    <input value={formQuota} onChange={(e) => setFormQuota(e.target.value)} className="w-full h-10 px-3.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-900" type="number" min="1" />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">Hình thức làm việc <span className="text-rose-500">*</span></label>
                                    <select value={formType} onChange={(e) => setFormType(e.target.value)} className="w-full h-10 px-3 bg-white border border-slate-300 rounded-lg text-sm text-slate-800">
                                        <option>Toàn thời gian (Full-time)</option>
                                        <option>Bán thời gian (Part-time)</option>
                                        <option>Linh hoạt / Hybrid</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">Hạn nhận hồ sơ <span className="text-rose-500">*</span></label>
                                    <input value={formDeadline} onChange={(e) => setFormDeadline(e.target.value)} className="w-full h-10 px-3.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800" type="date" />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">Phụ cấp thực tập (Hàng tháng)</label>
                                    <input className="w-full h-10 px-3.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800" type="text" defaultValue="6.000.000 - 9.000.000 VNĐ" />
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-800 mb-1.5">Địa điểm làm việc cụ thể <span className="text-rose-500">*</span></label>
                                <input className="w-full h-10 px-3.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800" type="text" defaultValue="F-Town 3, Khu Công nghệ cao TP. Thủ Đức, TP. Hồ Chí Minh" />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-800 mb-1.5">Mô tả công việc & Trách nhiệm chính <span className="text-rose-500">*</span></label>
                                <textarea className="w-full p-3.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800" rows={4} defaultValue="- Tham gia trực tiếp vào việc nghiên cứu và tối ưu các mô hình LLM ứng dụng cho hệ sinh thái doanh nghiệp."></textarea>
                            </div>
                        </div>

                        <div className="p-6 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
                            <button onClick={closeDrawer} className="px-4 py-2.5 border border-slate-300 hover:bg-slate-200 text-slate-700 text-sm font-semibold rounded-lg cursor-pointer">
                                Hủy bỏ
                            </button>
                            <div className="flex items-center gap-3">
                                <button onClick={saveDraft} className="px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 text-sm font-semibold rounded-lg shadow-sm cursor-pointer flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-slate-500 text-base">save</span>
                                    <span>Lưu bản nháp</span>
                                </button>
                                <button onClick={submitReview} className="px-5 py-2.5 bg-[#00288e] hover:bg-blue-800 text-white text-sm font-semibold rounded-lg shadow-sm cursor-pointer flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-base">send</span>
                                    <span>Gửi nhà trường phê duyệt</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};