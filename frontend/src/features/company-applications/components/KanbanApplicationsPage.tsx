import React, { useState } from 'react';

interface Job {
    id: string;
    title: string;
    code: string;
    applicantsCount: number;
}

interface Candidate {
    id: string;
    appId: string;
    jobId: string;
    name: string;
    university: string;
    major: string;
    gpa: string;
    skills: string[];
    matchScore: number;
    status: 'APPLIED' | 'SCREENING' | 'INTERVIEW' | 'OFFER' | 'HIRED' | 'REJECTED';
    appliedDate: string;
    email: string;
    phone: string;
    snapshotCvName: string;
    statusLogs: {
        title: string;
        time: string;
        actor: string;
        note?: string;
    }[];
    interviewNote?: string;
}

interface KanbanApplicationsPageProps {
    currentRoute?: string;
    onRouteChange?: (route: string) => void;
}

export const KanbanApplicationsPage: React.FC<KanbanApplicationsPageProps> = ({ onRouteChange }) => {
    // 1. Bắt buộc chọn tin tuyển dụng
    const jobs: Job[] = [
        { id: 'JOB-FE-2026', title: 'Thực tập sinh Frontend React/TypeScript (Đợt Thu 2026)', code: '#JOB-FE-2026', applicantsCount: 28 },
        { id: 'JOB-BE-2026', title: 'Thực tập sinh Backend Node.js & Go (Đợt Thu 2026)', code: '#JOB-BE-2026', applicantsCount: 16 },
    ];
    const [selectedJobId, setSelectedJobId] = useState<string>('JOB-FE-2026');
    const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban');

    // Trạng thái bật/tắt Drawer chi tiết ứng viên (có nút X để đóng)
    const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(true);

    // Bộ lọc nâng cao
    const [searchKeyword, setSearchKeyword] = useState('');
    const [selectedUniversity, setSelectedUniversity] = useState('all');
    const [minMatch, setMinMatch] = useState(0);

    // Mock danh sách ứng viên chuẩn
    const [candidates, setCandidates] = useState<Candidate[]>([
        {
            id: 'CAND-001',
            appId: '#APP-2026-FPT-092',
            jobId: 'JOB-FE-2026',
            name: 'Lê Hoàng Long',
            university: 'ĐH FPT Cần Thơ (SE)',
            major: 'Kỹ thuật Phần mềm',
            gpa: '3.4/4',
            skills: ['TypeScript', 'Next.js', 'Tailwind'],
            matchScore: 92,
            status: 'SCREENING',
            appliedDate: '25/10/2026, 10:45 AM',
            email: 'long.lh.intern@fpt.edu.vn',
            phone: '+84 987 654 321',
            snapshotCvName: 'Le_Hoang_Long_Resume_Frontend.pdf',
            statusLogs: [
                { title: 'APPLIED → SCREENING', time: '26/10/2026 09:15 AM', actor: 'HR Khôi', note: 'Hồ sơ đạt yêu cầu về đồ án Frontend. Chuyển sang vòng sơ loại để hẹn lịch phỏng vấn chuyên môn với Lead Tuấn.' },
                { title: 'Hệ thống tiếp nhận hồ sơ mới', time: '25/10/2026 10:45 AM', actor: 'Student Connect Portal' }
            ]
        },
        {
            id: 'CAND-002',
            appId: '#APP-2026-FPT-088',
            jobId: 'JOB-FE-2026',
            name: 'Nguyễn Văn An',
            university: 'ĐH Bách Khoa TP.HCM',
            major: 'Khoa học Máy tính',
            gpa: 'Ẩn',
            skills: ['React', 'Redux', 'JavaScript'],
            matchScore: 88,
            status: 'APPLIED',
            appliedDate: '28/10/2026',
            email: 'an.nv@hcmut.edu.vn',
            phone: '+84 912 345 678',
            snapshotCvName: 'Nguyen_Van_An_CV.pdf',
            statusLogs: [{ title: 'Hệ thống tiếp nhận hồ sơ mới', time: '28/10/2026', actor: 'Portal' }]
        },
        {
            id: 'CAND-003',
            appId: '#APP-2026-FPT-075',
            jobId: 'JOB-FE-2026',
            name: 'Phạm Quốc Bảo',
            university: 'RMIT Vietnam',
            major: 'Software Engineering',
            gpa: '3.8/4',
            skills: ['React', 'TypeScript', 'GraphQL'],
            matchScore: 95,
            status: 'INTERVIEW',
            appliedDate: '20/10/2026',
            email: 'bao.pq@rmit.edu.vn',
            phone: '+84 933 111 222',
            snapshotCvName: 'Pham_Quoc_Bao_Resume.pdf',
            statusLogs: [{ title: 'Chuyển sang INTERVIEW', time: '22/10/2026', actor: 'HR Lead' }],
            interviewNote: 'Google Meet: meet.google.com/xyz-intern (14:00 - 02/11/2026)'
        }
    ]);

    // Drawer state
    const [selectedCandidateId, setSelectedCandidateId] = useState<string>('CAND-001');
    const currentCandidate = candidates.find(c => c.id === selectedCandidateId) || candidates[0];

    // Form chuyển trạng thái trong Drawer
    const [nextStatus, setNextStatus] = useState<Candidate['status']>('INTERVIEW');
    const [statusNoteInput, setStatusNoteInput] = useState('');

    // Phân trang
    const [currentPage] = useState(1);
    const pageSize = 5;

    const filteredCandidates = candidates.filter(c => {
        if (c.jobId !== selectedJobId) return false;
        if (searchKeyword && !c.name.toLowerCase().includes(searchKeyword.toLowerCase()) && !c.email.toLowerCase().includes(searchKeyword.toLowerCase())) {
            return false;
        }
        if (selectedUniversity !== 'all' && !c.university.includes(selectedUniversity)) return false;
        if (c.matchScore < minMatch) return false;
        return true;
    });

    const paginatedCandidates = filteredCandidates.slice((currentPage - 1) * pageSize, currentPage * pageSize);

    const kanbanColumns: { key: Candidate['status']; label: string; color: string; count: number }[] = [
        { key: 'APPLIED', label: 'ỨNG TUYỂN (APPLIED)', color: 'border-t-slate-400', count: 8 },
        { key: 'SCREENING', label: 'SƠ LOẠI (SCREENING)', color: 'border-t-blue-600', count: 6 },
        { key: 'INTERVIEW', label: 'PHỎNG VẤN (INTERVIEW)', color: 'border-t-amber-500', count: 4 },
        { key: 'OFFER', label: 'ĐỀ NGHỊ (OFFER)', color: 'border-t-indigo-600', count: 3 },
        { key: 'HIRED', label: 'TRÚNG TUYỂN (HIRED)', color: 'border-t-emerald-600', count: 5 },
        { key: 'REJECTED', label: 'TỪ CHỐI (REJECTED)', color: 'border-t-rose-500', count: 2 },
    ];

    const handleUpdateStatus = (e: React.FormEvent) => {
        e.preventDefault();
        setCandidates(prev => prev.map(c => {
            if (c.id === currentCandidate.id) {
                const updatedLogs = [
                    {
                        title: `${c.status} → ${nextStatus}`,
                        time: new Date().toLocaleString(),
                        actor: 'HR Khôi',
                        note: statusNoteInput || 'Cập nhật trạng thái ứng viên'
                    },
                    ...c.statusLogs
                ];
                return {
                    ...c,
                    status: nextStatus,
                    statusLogs: updatedLogs
                };
            }
            return c;
        }));
        alert(`Đã cập nhật trạng thái ứng viên ${currentCandidate.name} thành công sang ${nextStatus}!`);
        setStatusNoteInput('');
    };

    return (
        <div className="flex h-screen bg-slate-100 font-sans text-slate-900 antialiased overflow-hidden">
            
            {/* ==================== 1. THANH SIDEBAR ĐẦY ĐỦ ==================== */}
            <aside className="w-[260px] shrink-0 bg-white border-r border-slate-200 flex flex-col justify-between p-4 z-40 select-none overflow-y-auto">
                <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3 px-2 py-1">
                        <div className="w-10 h-10 rounded-lg bg-[#1e40af] text-white flex items-center justify-center font-bold text-lg shadow-sm">
                            <span className="material-symbols-outlined text-white">school</span>
                        </div>
                        <div className="flex flex-col leading-tight">
                            <span className="text-sm font-bold text-[#00288e]">Student Connect</span>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Enterprise Portal</span>
                        </div>
                    </div>

                    <button className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[#1e40af] text-white rounded-lg text-xs font-semibold hover:bg-blue-800 transition-all shadow-sm">
                        <span className="material-symbols-outlined text-white text-base">add_circle</span>
                        <span>Đăng tin mới</span>
                    </button>

                    <nav className="flex flex-col gap-1 mt-1 text-xs text-slate-600">
                        <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">Sinh viên</div>
                        <a href="#tim-viec" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">search</span>Tìm việc làm</a>
                        <a href="#goi-y" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">auto_awesome</span>Gợi ý việc làm</a>
                        <a href="#da-luu" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">bookmark_border</span>Việc đã lưu</a>
                        <a href="#ho-so" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">person_outline</span>Hồ sơ cá nhân</a>
                        <a href="#cv" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">description</span>Quản lý CV</a>
                        <a href="#ung-tuyen" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">send</span>Đơn ứng tuyển</a>
                        <a href="#phong-van" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">mail_outline</span>Lời mời phỏng vấn</a>
                        <a href="#thuc-tap" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">school</span>Theo dõi thực tập</a>

                        <div className="px-3 pt-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">Doanh nghiệp</div>
                        <a href="#tin-tuyen-dung" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">post_add</span>Tin tuyển dụng</a>
                        <button onClick={() => onRouteChange && onRouteChange('QLUV')} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg bg-blue-50 text-[#1e40af] font-bold border-l-4 border-[#1e40af] text-left">
                            <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>group</span>
                            <span>Quản lý ứng viên</span>
                            <span className="ml-auto px-2 py-0.5 rounded-full bg-blue-100 text-[#1e40af] text-[10px]">28</span>
                        </button>
                        <a href="#goi-y-uv" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">person_search</span>Gợi ý ứng viên</a>
                        <a href="#loi-moi" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">forward_to_inbox</span>Lời mời đã gửi</a>
                        <a href="#ho-so-cty" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">domain</span>Hồ sơ công ty</a>

                        <div className="px-3 pt-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">Nhà trường / Admin</div>
                        <a href="#tong-quan" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">trending_up</span>Tổng quan hệ thống</a>
                        <a href="#ql-sv" className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">badge</span>Quản lý sinh viên</a>
                    </nav>
                </div>

                <div className="pt-3 border-t border-slate-200 flex flex-col gap-1 text-xs">
                    <a href="#cai-dat" className="flex items-center gap-3 px-3 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">settings</span>Cài đặt hệ thống</a>
                    <a href="#ho-tro" className="flex items-center gap-3 px-3 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100"><span className="material-symbols-outlined text-slate-400 text-base">help</span>Hỗ trợ & Trợ giúp</a>
                    <div className="mt-2 p-2 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span className="text-[10px] text-slate-500 font-medium">Đồng bộ Talent API: <strong className="text-slate-700">Đã kết nối</strong></span>
                    </div>
                </div>
            </aside>

            {/* ==================== 2. MAIN WORKSPACE ==================== */}
            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                
                {/* Top Header */}
                <header className="h-16 px-6 bg-white border-b border-slate-200 flex items-center justify-between z-30 shrink-0 shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="flex flex-col">
                            <div className="flex items-center gap-2">
                                <h1 className="text-sm font-bold text-[#1e40af]">Quản lý ứng viên theo tin tuyển dụng</h1>
                                <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-100 text-slate-600 border border-slate-300 font-bold">Fall 2026 Batch</span>
                            </div>
                            <p className="text-[11px] text-slate-500">Quy trình điều phối thực tập sinh kỹ thuật & Đánh giá năng lực sinh viên</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1e40af] text-white rounded-lg text-xs font-semibold hover:bg-blue-800 shadow-sm">
                            <span className="material-symbols-outlined text-sm">video_call</span>
                            <span>Tạo phỏng vấn</span>
                        </button>
                        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-[#1e40af] font-bold text-xs">FPT</div>
                            <div className="text-right leading-tight">
                                <p className="text-xs font-bold text-slate-900">Khôi HR</p>
                                <p className="text-[10px] text-slate-400">FPT Software / VNG Tech</p>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Control & Filter Bar */}
                <div className="bg-white border-b border-slate-200 px-6 py-3 shrink-0 flex flex-col gap-2.5 shadow-xs">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="flex flex-col">
                                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-xs text-[#1e40af]">bolt</span>
                                    Tin tuyển dụng đang mở
                                </label>
                                <select 
                                    value={selectedJobId} 
                                    onChange={(e) => setSelectedJobId(e.target.value)}
                                    className="h-9 px-3 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-900 font-semibold focus:border-[#1e40af]"
                                >
                                    {jobs.map(j => (
                                        <option key={j.id} value={j.id}>{j.title} ({j.applicantsCount} ứng viên)</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex items-center gap-2 mt-4 bg-blue-50/70 border border-blue-100 rounded-lg px-3 py-1 text-xs">
                                <span className="text-slate-500">Tổng ứng viên: <strong className="text-[#1e40af]">28</strong></span>
                                <span className="text-slate-300">|</span>
                                <span className="text-slate-500">Đang phỏng vấn: <strong className="text-amber-600">4</strong></span>
                                <span className="text-slate-300">|</span>
                                <span className="text-slate-500">Đã Offer: <strong className="text-indigo-600">3</strong></span>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <div className="bg-slate-100 p-0.5 rounded-lg border border-slate-200 flex items-center">
                                <button onClick={() => setViewMode('kanban')} className={`flex items-center gap-1 px-3 py-1 rounded-md text-xs font-semibold ${viewMode === 'kanban' ? 'bg-white text-[#1e40af] shadow-xs' : 'text-slate-600'}`}>
                                    <span className="material-symbols-outlined text-base">view_kanban</span>Kanban
                                </button>
                                <button onClick={() => setViewMode('table')} className={`flex items-center gap-1 px-3 py-1 rounded-md text-xs font-semibold ${viewMode === 'table' ? 'bg-white text-[#1e40af] shadow-xs' : 'text-slate-600'}`}>
                                    <span className="material-symbols-outlined text-base">table_chart</span>Danh sách
                                </button>
                            </div>
                            <button className="h-9 px-3 bg-[#1e40af] text-white rounded-lg flex items-center gap-1.5 text-xs font-semibold hover:bg-blue-800 shadow-sm">
                                <span className="material-symbols-outlined text-base">person_add</span>Mời ứng viên mới
                            </button>
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                        <div className="relative w-64">
                            <span className="material-symbols-outlined text-slate-400 absolute left-2.5 top-2 text-base">search</span>
                            <input 
                                type="text" 
                                placeholder="Tìm theo tên, email, từ khóa..." 
                                value={searchKeyword}
                                onChange={(e) => setSearchKeyword(e.target.value)}
                                className="w-full h-8 pl-8 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-[#1e40af]" 
                            />
                        </div>
                        <select value={selectedUniversity} onChange={(e) => setSelectedUniversity(e.target.value)} className="h-8 px-2.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-700">
                            <option value="all">Trường ĐH: Tất cả</option>
                            <option value="FPT">ĐH FPT</option>
                            <option value="Bách Khoa">ĐH Bách Khoa</option>
                            <option value="RMIT">RMIT</option>
                        </select>
                        <select value={minMatch} onChange={(e) => setMinMatch(Number(e.target.value))} className="h-8 px-2.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-700">
                            <option value={0}>Độ phù hợp: Tất cả</option>
                            <option value={85}>Độ phù hợp ≥ 85%</option>
                        </select>
                        <div className="ml-auto text-xs text-slate-400 font-medium">Hiển thị {filteredCandidates.length} ứng viên hợp lệ</div>
                    </div>
                </div>

                {/* Kanban Columns + Slide-over Drawer (Có nút X để tắt) */}
                <div className="flex-1 flex overflow-hidden relative">
                    {viewMode === 'kanban' && (
                        <div className="flex-1 overflow-x-auto p-6 bg-slate-100 flex gap-4 select-none">
                            {kanbanColumns.map(col => {
                                const colCandidates = filteredCandidates.filter(c => c.status === col.key);
                                return (
                                    <div key={col.key} className="w-80 shrink-0 flex flex-col bg-slate-200/60 rounded-xl border border-slate-200 h-full max-h-full">
                                        <div className={`p-3 bg-white rounded-t-xl border-b border-slate-200 border-t-4 ${col.color} flex items-center justify-between`}>
                                            <div className="flex items-center gap-2">
                                                <span className="font-bold text-xs uppercase tracking-wider text-slate-800">{col.label}</span>
                                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">{col.count}</span>
                                            </div>
                                        </div>
                                        <div className="flex-1 overflow-y-auto p-2.5 flex flex-col gap-2.5">
                                            {colCandidates.map(c => (
                                                <div 
                                                    key={c.id} 
                                                    onClick={() => {
                                                        setSelectedCandidateId(c.id);
                                                        setIsDrawerOpen(true);
                                                    }}
                                                    className={`bg-white rounded-lg p-3.5 border transition-all cursor-pointer group ${selectedCandidateId === c.id && isDrawerOpen ? 'border-2 border-[#1e40af] shadow-md ring-2 ring-blue-500/20' : 'border-slate-200 hover:border-blue-400'}`}
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div>
                                                            <h4 className="font-bold text-sm text-slate-900 group-hover:text-[#1e40af]">{c.name}</h4>
                                                            <p className="text-xs text-slate-500 mt-0.5">{c.university}</p>
                                                        </div>
                                                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">GPA: {c.gpa}</span>
                                                    </div>
                                                    <div className="flex flex-wrap gap-1 mt-2.5">
                                                        {c.skills.map((s, idx) => (
                                                            <span key={idx} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-medium rounded">{s}</span>
                                                        ))}
                                                    </div>
                                                    {c.interviewNote && (
                                                        <div className="mt-2 p-2 bg-amber-50 rounded border border-amber-200 text-[11px] text-amber-900">
                                                            <strong>Lịch PV:</strong> {c.interviewNote}
                                                        </div>
                                                    )}
                                                    <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-2.5 mt-2.5">
                                                        <span>Match: {c.matchScore}%</span>
                                                        <span className="text-[#1e40af] font-semibold hover:underline">Xem chi tiết &rarr;</span>
                                                    </div>
                                                </div>
                                            ))}
                                            <button onClick={() => alert('Đã tải thêm danh sách ứng viên trong cột')} className="py-2 text-center text-xs text-slate-500 hover:text-[#1e40af] font-semibold border border-dashed border-slate-300 rounded-lg bg-white/50">
                                                + Tải thêm ứng viên trong cột
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {viewMode === 'table' && (
                        <div className="flex-1 p-6 bg-slate-100 flex flex-col justify-between overflow-y-auto">
                            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-slate-50 border-b border-slate-200 text-xs uppercase text-slate-500 font-bold">
                                            <th className="py-3 px-4">Ứng viên</th>
                                            <th className="py-3 px-4">Trường ĐH / GPA</th>
                                            <th className="py-3 px-4">Kỹ năng</th>
                                            <th className="py-3 px-4">Trạng thái</th>
                                            <th className="py-3 px-4 text-right">Thao tác</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 text-sm">
                                        {paginatedCandidates.map(c => (
                                            <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                                                <td className="py-3 px-4 flex items-center gap-3">
                                                    <div className="w-9 h-9 rounded-full bg-blue-100 text-[#1e40af] flex items-center justify-center font-bold text-xs">LH</div>
                                                    <div>
                                                        <div className="font-bold text-slate-900">{c.name}</div>
                                                        <div className="text-xs text-slate-400">{c.email}</div>
                                                    </div>
                                                </td>
                                                <td className="py-3 px-4 text-xs text-slate-700">
                                                    <div className="font-medium">{c.university}</div>
                                                    <div className="text-slate-400">GPA: {c.gpa}</div>
                                                </td>
                                                <td className="py-3 px-4">
                                                    <div className="flex flex-wrap gap-1">
                                                        {c.skills.slice(0, 2).map((s, i) => (
                                                            <span key={i} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[10px] rounded">{s}</span>
                                                        ))}
                                                    </div>
                                                </td>
                                                <td className="py-3 px-4">
                                                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">{c.status}</span>
                                                </td>
                                                <td className="py-3 px-4 text-right">
                                                    <button onClick={() => { setSelectedCandidateId(c.id); setIsDrawerOpen(true); }} className="px-3 py-1.5 bg-[#1e40af] text-white text-xs font-semibold rounded hover:bg-blue-800">
                                                        Mở Drawer
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* ==================== SLIDE-OVER DETAIL DRAWER (ĐÃ CÓ NÚT X ĐÓNG) ==================== */}
                    {isDrawerOpen && (
                        <aside className="w-[540px] shrink-0 h-full bg-white border-l border-slate-200 shadow-2xl flex flex-col z-20 overflow-hidden">
                            <div className="p-5 border-b border-slate-200 bg-white flex items-start justify-between">
                                <div className="flex items-start gap-3">
                                    <div className="w-12 h-12 rounded-xl bg-blue-100 border border-blue-200 flex items-center justify-center text-[#1e40af] font-bold">LH</div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-base font-bold text-slate-900">{currentCandidate.name}</h3>
                                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">SCREENING</span>
                                        </div>
                                        <p className="text-xs text-slate-600 mt-0.5">Vị trí: <strong>Frontend Intern (React/TypeScript)</strong></p>
                                        <p className="text-[11px] text-slate-400 mt-0.5">ID Ứng tuyển: {currentCandidate.appId} • Nộp lúc {currentCandidate.appliedDate}</p>
                                    </div>
                                </div>
                                {/* NÚT DẤU X ĐỂ TẮT BẢNG DRAWER */}
                                <button 
                                    onClick={() => setIsDrawerOpen(false)}
                                    className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 flex items-center justify-center transition-colors"
                                    title="Đóng bảng"
                                >
                                    <span className="material-symbols-outlined text-lg">close</span>
                                </button>
                            </div>

                            {/* Snapshot CV Download Bar */}
                            <div className="px-5 py-3 bg-blue-50 border-b border-blue-100 flex items-center justify-between">
                                <div className="flex items-center gap-2 text-xs text-[#1e40af] font-semibold">
                                    <span className="material-symbols-outlined text-base">description</span>
                                    <span>Snapshot CV: {currentCandidate.snapshotCvName}</span>
                                </div>
                                <button onClick={() => alert(`Đang tải đúng snapshot CV: ${currentCandidate.snapshotCvName}`)} className="px-3 py-1.5 bg-[#1e40af] text-white rounded text-xs font-semibold flex items-center gap-1 hover:bg-blue-800 shadow-xs">
                                    <span className="material-symbols-outlined text-sm">download</span>
                                    <span>Tải snapshot CV</span>
                                </button>
                            </div>

                            {/* Drawer Scrollable Content */}
                            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5 text-xs">
                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                                    <h4 className="font-bold uppercase tracking-wider text-slate-500 mb-2">Thông tin ứng viên & Học vấn</h4>
                                    <div className="grid grid-cols-2 gap-2 text-slate-700">
                                        <div>Email: <strong className="text-slate-900">{currentCandidate.email}</strong></div>
                                        <div>SĐT: <strong className="text-slate-900">{currentCandidate.phone}</strong></div>
                                        <div>Trường: <strong className="text-slate-900">{currentCandidate.university}</strong></div>
                                        <div>GPA: <strong className="text-emerald-700">{currentCandidate.gpa}</strong></div>
                                    </div>
                                </div>

                                {/* Lịch sử trạng thái */}
                                <div>
                                    <h4 className="font-bold uppercase tracking-wider text-slate-500 mb-3">Lịch sử thay đổi trạng thái (Status Log)</h4>
                                    <div className="relative pl-5 space-y-3 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-200">
                                        {currentCandidate.statusLogs.map((log, idx) => (
                                            <div key={idx} className="relative">
                                                <div className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-[#1e40af] ring-2 ring-white"></div>
                                                <div className="font-semibold text-slate-800">{log.title}</div>
                                                <div className="text-[11px] text-slate-400">{log.actor} • {log.time}</div>
                                                {log.note && <div className="mt-1 p-2 bg-slate-50 rounded border text-slate-600 italic">"{log.note}"</div>}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Form chuyển trạng thái & Thêm ghi chú */}
                                <div className="p-4 bg-white rounded-xl border-2 border-[#1e40af]/30 shadow-xs">
                                    <h4 className="font-bold uppercase tracking-wider text-[#1e40af] mb-3">Chuyển trạng thái & Thêm ghi chú mới</h4>
                                    <form onSubmit={handleUpdateStatus} className="flex flex-col gap-3">
                                        <div>
                                            <label className="block font-semibold text-slate-600 mb-1">Trạng thái kế tiếp:</label>
                                            <select 
                                                value={nextStatus}
                                                onChange={(e) => setNextStatus(e.target.value as Candidate['status'])}
                                                className="w-full h-9 px-3 bg-slate-50 border border-slate-300 rounded-lg font-semibold text-slate-900"
                                            >
                                                <option value="INTERVIEW">PHỎNG VẤN (INTERVIEW) - Vòng 1 Kỹ thuật</option>
                                                <option value="OFFER">ĐỀ NGHỊ (OFFER) - Gửi thư mời nhận việc</option>
                                                <option value="REJECTED">TỪ CHỐI (REJECTED) - Gửi thông báo từ chối</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block font-semibold text-slate-600 mb-1">Ghi chú phỏng vấn / Feedback nội bộ:</label>
                                            <textarea 
                                                rows={2} 
                                                value={statusNoteInput}
                                                onChange={(e) => setStatusNoteInput(e.target.value)}
                                                placeholder="Nhập ghi chú cho Interviewer hoặc thông tin phòng họp Meet..."
                                                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 resize-none"
                                            ></textarea>
                                        </div>
                                        <div className="flex items-center justify-between pt-1">
                                            <label className="flex items-center gap-2 cursor-pointer">
                                                <input defaultChecked className="rounded text-[#1e40af] h-3.5 w-3.5" type="checkbox" />
                                                <span className="text-[11px] text-slate-600 font-medium">Gửi email thông báo tự động cho sinh viên</span>
                                            </label>
                                            <button type="submit" className="px-4 py-2 bg-[#1e40af] text-white text-xs font-bold rounded-lg hover:bg-blue-800 shadow-sm">
                                                Lưu & Cập nhật
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>

                            {/* Drawer Footer Actions */}
                            <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
                                <button className="px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition-colors">Loại ứng viên</button>
                                <div className="flex items-center gap-2">
                                    <button className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">Chia sẻ hồ sơ</button>
                                    <button className="px-4 py-2 bg-[#1e40af] text-white text-xs font-bold rounded-lg hover:bg-blue-800 shadow-sm">Lên lịch phỏng vấn Meet</button>
                                </div>
                            </div>
                        </aside>
                    )}
                </div>
            </div>
        </div>
    );
};