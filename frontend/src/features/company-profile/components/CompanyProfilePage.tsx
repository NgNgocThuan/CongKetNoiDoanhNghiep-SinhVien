import React, { useState } from 'react';

interface DocumentItem {
    id: string;
    name: string;
    size: string;
    date: string;
    status: string;
}

export const CompanyProfilePage: React.FC = () => {
    // State quản lý form Hồ sơ doanh nghiệp
    const [scale, setScale] = useState('10000+');
    const [industryTags, setIndustryTags] = useState([
        'Công nghệ thông tin & Phần mềm',
        'Viễn thông & Dịch vụ Cloud',
        'Trí tuệ nhân tạo (AI & Data Science)'
    ]);
    const [newTagInput, setNewTagInput] = useState('');
    const [isAddingTag, setIsAddingTag] = useState(false);

    const [address, setAddress] = useState('Tòa nhà FPT, Phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Hà Nội');
    const [website, setWebsite] = useState('https://fptsoftware.com');
    const [email, setEmail] = useState('hr-internship@fpt.com');
    const [hotline, setHotline] = useState('024 7300 7300 (Ext: 104)');
    const [chatContact, setChatContact] = useState('Zalo OA: FPT Software Talent Hub');
    const [cultureText, setCultureText] = useState(
        `FPT Software là công ty dẫn đầu Đông Nam Á về chuyển đổi số và công nghệ thông tin toàn cầu với hơn 30,000 cán bộ nhân viên tại 30 quốc gia.\n\nChương trình Global Internship tại FPT Software cam kết:\n1. Mô hình Huấn luyện Mentor 1-on-1: Mỗi thực tập sinh được kèm cặp bởi một Senior Solution Architect hoặc Tech Lead trong suốt kỳ thực tập 3-6 tháng.\n2. Tham gia dự án thực chiến chuẩn quốc tế: Trực tiếp làm việc cùng các đối tác Fortune 500 thuộc lĩnh vực Automotive, Banking, Fintech và Cloud Computing.\n3. Môi trường Campus chuẩn xanh: Trải nghiệm không gian làm việc hiện đại, tổ hợp tiện ích thể thao, phòng gym và cafeteria tiêu chuẩn tại F-Town, Hola Park.`
    );

    // Danh sách tài liệu pháp lý
    const [documents, setDocuments] = useState<DocumentItem[]>([
        {
            id: '1',
            name: 'Giấy chứng nhận đăng ký DN (GPKD).pdf',
            size: '2.4 MB',
            date: '12/01/2024',
            status: 'Đã duyệt bởi Nhà trường'
        },
        {
            id: '2',
            name: 'Giấy ủy quyền người đại diện ký thỏa thuận hợp tác thực tập.pdf',
            size: '1.1 MB',
            date: '15/01/2024',
            status: 'Đã duyệt hợp tác'
        }
    ]);

    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Xóa lĩnh vực hoạt động (Tag)
    const handleRemoveTag = (tagToRemove: string) => {
        setIndustryTags(industryTags.filter(tag => tag !== tagToRemove));
    };

    // Thêm lĩnh vực mới
    const handleAddTag = () => {
        if (newTagInput.trim() && !industryTags.includes(newTagInput.trim())) {
            setIndustryTags([...industryTags, newTagInput.trim()]);
            setNewTagInput('');
            setIsAddingTag(false);
        }
    };

    // Xóa tài liệu pháp lý
    const handleDeleteDoc = (docName: string) => {
        if (window.confirm(`Bạn có chắc chắn muốn xóa tài liệu "${docName}" không? Tài liệu đã xóa sẽ yêu cầu xét duyệt lại từ Ban Quản lý Đại học.`)) {
            setDocuments(documents.filter(doc => doc.name !== docName));
            alert(`Đã xóa tài liệu "${docName}" thành công.`);
        }
    };

    // Tải lên tài liệu mới
    const handleUploadDoc = () => {
        const docName = prompt("Nhập tên tài liệu bổ sung (ví dụ: Giấy chứng nhận ISO.pdf):");
        if (docName) {
            const newDoc: DocumentItem = {
                id: String(Date.now()),
                name: docName.endsWith('.pdf') ? docName : docName + '.pdf',
                size: '1.8 MB',
                date: new Date().toLocaleDateString('vi-VN'),
                status: 'Chờ kiểm duyệt'
            };
            setDocuments([...documents, newDoc]);
            alert("Tải lên tài liệu thành công! Đang chờ Ban Quản lý Đại học thẩm định.");
        }
    };

    // Lưu thông tin hồ sơ
    const handleSaveProfile = () => {
        setIsSaving(true);
        setTimeout(() => {
            setIsSaving(false);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 2000);
        }, 800);
    };

    return (
        <div className="h-full font-sans text-slate-900 antialiased bg-slate-50 selection:bg-blue-100 selection:text-blue-900">
            {/* ========================================== */}
            {/* LEFT SIDEBAR NAVIGATION                    */}
            {/* ========================================== */}
            <aside className="fixed left-0 top-0 h-full w-[260px] z-40 flex flex-col justify-between p-4 bg-white border-r border-slate-200 shadow-sm">
                <div className="shrink-0 pb-3 border-b border-slate-200">
                    <div className="flex items-center gap-3 px-1 py-1.5 mb-3">
                        <div className="w-10 h-10 rounded-xl bg-[#00288e] flex items-center justify-center text-white shadow-sm ring-2 ring-primary/10">
                            <span className="material-symbols-outlined text-[24px]">school</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="font-bold text-[#00288e] text-base tracking-tight">Student Connect</span>
                            <span className="text-xs text-slate-400 font-medium">Enterprise Portal</span>
                        </div>
                    </div>
                    <button className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-[#00288e] hover:bg-blue-800 text-white font-semibold transition-all shadow-sm cursor-pointer text-sm">
                        <span className="material-symbols-outlined text-[18px]">add</span>
                        <span>Đăng tin mới</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scroll py-3 space-y-4 pr-1">
                    {/* SINH VIÊN */}
                    <div>
                        <div className="text-[11px] font-bold text-slate-400 uppercase px-2 mb-1.5 tracking-wider flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-[14px]">person</span>
                            <span>Sinh viên</span>
                        </div>
                        <nav className="space-y-0.5 text-sm">
                            <a href="#tim-viec" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">search</span><span>Tìm việc làm</span></a>
                            <a href="#goi-y" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">recommend</span><span>Gợi ý việc làm</span></a>
                            <a href="#viec-da-luu" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">bookmark_border</span><span>Việc đã lưu</span></a>
                            <a href="#ho-so" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">account_box</span><span>Hồ sơ cá nhân</span></a>
                            <a href="#cv" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">description</span><span>Quản lý CV</span></a>
                            <a href="#don" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">assignment</span><span>Đơn ứng tuyển</span></a>
                            <a href="#phong-van" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">event_available</span><span>Lời mời phỏng vấn</span></a>
                            <a href="#thuc-tap" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">trending_up</span><span>Theo dõi thực tập</span></a>
                        </nav>
                    </div>

                    {/* DOANH NGHIỆP */}
                    <div className="pt-2 border-t border-slate-200">
                        <div className="text-[11px] font-bold text-slate-400 uppercase px-2 mb-1.5 tracking-wider flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-[14px]">apartment</span>
                            <span>Doanh nghiệp</span>
                        </div>
                        <nav className="space-y-0.5 text-sm">
                            <a href="#tin-tuyen-dung" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">work_outline</span><span>Tin tuyển dụng</span></a>
                            <a href="#quan-ly-ung-vien" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">groups</span><span>Quản lý ứng viên</span></a>
                            <a href="#goi-y-ung-vien" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">person_search</span><span>Gợi ý ứng viên</span></a>
                            <a href="#loi-moi" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">outgoing_mail</span><span>Lời mời đã gửi</span></a>
                            <a href="#ho-so-cong-ty" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg bg-blue-50 text-[#00288e] font-semibold border-l-4 border-[#00288e] cursor-pointer">
                                <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>domain</span>
                                <span>Hồ sơ công ty</span>
                            </a>
                        </nav>
                    </div>

                    {/* NHÀ TRƯỜNG / ADMIN */}
                    <div className="pt-2 border-t border-slate-200">
                        <div className="text-[11px] font-bold text-slate-400 uppercase px-2 mb-1.5 tracking-wider flex items-center gap-1.5">
                            <span className="material-symbols-outlined text-[14px]">admin_panel_settings</span>
                            <span>Nhà trường / Admin</span>
                        </div>
                        <nav className="space-y-0.5 text-sm">
                            <a href="#tong-quan" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">dashboard</span><span>Tổng quan hệ thống</span></a>
                            <a href="#quan-ly-sv" className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"><span className="material-symbols-outlined text-[18px]">school</span><span>Quản lý sinh viên</span></a>
                        </nav>
                    </div>
                </div>

                <div className="shrink-0 pt-2 border-t border-slate-200 space-y-1">
                    <a className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#settings">
                        <span className="material-symbols-outlined text-[18px]">settings</span>
                        <span>Cài đặt hệ thống</span>
                    </a>
                    <a className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-slate-600 text-sm hover:bg-slate-100 transition-colors cursor-pointer" href="#help">
                        <span className="material-symbols-outlined text-[18px]">help_outline</span>
                        <span>Hỗ trợ & Trợ giúp</span>
                    </a>
                    <div className="mt-2 p-2 bg-slate-50 rounded-lg border border-slate-200 flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-[#00288e] shrink-0 shadow-sm">
                            <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>verified_user</span>
                        </div>
                        <div className="leading-tight">
                            <p className="text-xs font-semibold text-slate-900">Đối tác đào tạo</p>
                            <p className="text-[11px] text-slate-400">ĐHQG & Bách Khoa</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* ========================================== */}
            {/* TOP NAVBAR HEADER                          */}
            {/* ========================================== */}
            <header className="sticky top-0 right-0 z-30 flex items-center justify-between w-[calc(100%-260px)] ml-[260px] h-16 px-6 bg-white border-b border-slate-200 shadow-sm">
                <div className="flex items-center gap-6">
                    <nav className="flex items-center space-x-2 text-sm text-slate-400">
                        <span>Doanh nghiệp</span>
                        <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                        <span className="text-[#00288e] font-semibold">Hồ sơ công ty</span>
                    </nav>
                    <div className="relative w-72">
                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400">search</span>
                        <input className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-[#00288e] text-sm" placeholder="Tìm kiếm tài liệu, nhân sự..." type="text" />
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-semibold transition-colors cursor-pointer">
                        <span className="material-symbols-outlined text-[18px] text-[#00288e]">calendar_month</span>
                        <span>Tạo phỏng vấn</span>
                    </button>
                    <button className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-600 hover:bg-slate-100 transition-colors relative cursor-pointer" title="Thông báo">
                        <span className="material-symbols-outlined text-[20px]">notifications</span>
                        <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-600"></span>
                    </button>
                    <button className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer" title="Trợ giúp">
                        <span className="material-symbols-outlined text-[20px]">help_outline</span>
                    </button>
                    <div className="h-6 w-px bg-slate-200 mx-1"></div>
                    <div className="flex items-center gap-3 pl-1 cursor-pointer">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-semibold text-slate-900 leading-snug">Khôi Nguyễn</p>
                            <p className="text-xs text-slate-400">Lead HR Campus • FPT</p>
                        </div>
                        <div className="relative">
                            <img className="w-9 h-9 rounded-full object-cover ring-2 ring-blue-950/10" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCD2DKHfHzqu2-cZGSB820ar2fsuX2p6QWUryAp2RhGLWRYRP5pfGcZ7o9Fv1tbd-Pfn-MtmdPHkpEdcVPGSgN0cfVr0iHApRt-QFK1RA-YDib_jF_Ummn2bUrBK8thbp-d0HaaXvH8hs5SaU6VsLjNAf0Z9PE4b8R3jHSghrRgaL9R_zHj4J8NKRvFkLjq4JN5MsBttsOlSemE2LV4MxPPsvLbj9aEBnAwiEK8SHo" alt="Khôi Nguyễn" />
                            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
                        </div>
                    </div>
                </div>
            </header>

            {/* ========================================== */}
            {/* MAIN WORKSPACE CONTENT CANVAS              */}
            {/* ========================================== */}
            <main className="w-[calc(100%-260px)] ml-[260px] min-h-[calc(100vh-64px)] p-6 pb-28 space-y-6 bg-slate-50">
                {/* 1. BANNER & VERIFICATION STATE HEADER */}
                <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="relative h-44 w-full bg-slate-100 overflow-hidden">
                        <div className="w-full h-full bg-cover bg-center" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuClwngymaXZ5SoDOhS4YEHIvsoAHlnDD62m0csqnZLYl8m-qFqIlMjAbWidS3eBIcx4UpODWaUJ5kSYFCAlU6Mb4ZJSMm5P-tUH7cbsHYnl_qUTNzou4mVdigcdVGC26cw044yo1lO7whCpQexFLOKp0zBu6qVN02LCWKqpzP9GElyre9km7PqZYItnz8i85JbrS9yzI06YFER0VnPh0nIfylInOEix_gZFswpHNb0')" }}></div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/10 to-transparent"></div>
                        <div className="absolute top-4 right-4 flex items-center gap-2">
                            <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/90 backdrop-blur-sm hover:bg-white text-slate-900 text-sm transition-all shadow-xs cursor-pointer font-medium">
                                <span className="material-symbols-outlined text-[16px]">photo_camera</span>
                                <span>Thay đổi ảnh bìa</span>
                            </button>
                        </div>
                    </div>

                    <div className="px-6 pb-6 pt-0">
                        <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-4 -mt-12">
                            <div className="flex items-end gap-4">
                                <div className="w-24 h-24 rounded-xl bg-white p-2 border-2 border-white shadow-md ring-1 ring-slate-200 flex items-center justify-center shrink-0">
                                    <img className="w-full h-full object-contain" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAjslBFCIWTwvQAkYuDYFBn0y7yDPlW31MDRcTUygBKW7bxP64lcP-Nkyu6ulIcttvHsQ72P9dT9TbRYHTRM5YNp0LCiNeaKc_yqgcJFqFbRrXvUWvMY1cyjJksZD8e4wO8ihrJdhfb3wQWXSvEIYeyfley9DsAhvb0by0OCGvmiRhXg1Zwr_RRrzaUqMrGB87L21riih_gwiYFkGk91ObUEJ1c_-HflzGz_yEZB00" alt="Logo FPT" />
                                </div>
                                <div className="mb-1">
                                    <div className="flex flex-wrap items-center gap-3">
                                        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                                            Công ty Cổ phần Phần mềm FPT (FPT Software)
                                        </h1>
                                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs bg-teal-50 text-teal-700 border border-teal-200 font-semibold shadow-xs">
                                            <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>verified</span>
                                            Đã xác thực doanh nghiệp
                                        </span>
                                    </div>
                                    <p className="text-xs text-slate-400 flex items-center gap-2 mt-1">
                                        <span>Mã đối tác: <strong className="text-slate-900 font-semibold">SC-VN-2024-FPT01</strong></span>
                                        <span>•</span>
                                        <span className="flex items-center gap-1 text-teal-700 font-medium">
                                            <span className="material-symbols-outlined text-[14px]">event_available</span>
                                            Phê duyệt bởi Ban Hợp tác Đại học ngày 15/01/2024
                                        </span>
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center gap-3 mb-1">
                                <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-sm font-semibold transition-colors cursor-pointer">
                                    <span className="material-symbols-outlined text-[18px]">close</span>
                                    <span>Hủy thay đổi</span>
                                </button>
                                <button onClick={handleSaveProfile} className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-[#00288e] hover:bg-blue-800 text-white font-semibold shadow-sm transition-all active:scale-95 cursor-pointer">
                                    <span className="material-symbols-outlined text-[18px]">save</span>
                                    <span>Lưu thông tin hồ sơ</span>
                                </button>
                            </div>
                        </div>

                        <div className="mt-5 p-3 rounded-lg bg-blue-50/50 border border-blue-100 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm text-slate-700">
                                <span className="material-symbols-outlined text-[18px] text-[#00288e]">shield</span>
                                <span>Hồ sơ doanh nghiệp đã liên kết trực tiếp với cổng thực tập của 12 trường đại học trọng điểm quốc gia. Các dữ liệu đăng kiểm được mã hóa an toàn.</span>
                            </div>
                            <span className="text-xs text-slate-400 shrink-0">Phiên bản dữ liệu: v3.2.0</span>
                        </div>
                    </div>
                </section>

                {/* 2. TWO-COLUMN HIGH-DENSITY BENTO WORKSPACE */}
                <div className="grid grid-cols-12 gap-6 items-start">
                    {/* LEFT COLUMN (8 COLUMNS) */}
                    <div className="col-span-12 lg:col-span-8 space-y-6">
                        {/* 2.1 Basic Info & Read-Only Locks */}
                        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                            <div className="flex items-center justify-between pb-4 mb-5 border-b border-slate-200">
                                <div>
                                    <h2 className="text-lg font-semibold text-slate-900">Thông tin doanh nghiệp & Pháp lý định danh</h2>
                                    <p className="text-xs text-slate-500">Dữ liệu cốt lõi phục vụ ký hợp đồng thực tập 3 bên và xác thực sinh viên</p>
                                </div>
                                <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-semibold">
                                    <span className="material-symbols-outlined text-[14px]">verified_user</span>
                                    Chuẩn ISO/IEC 27001
                                </span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                {/* READ-ONLY: Tên doanh nghiệp */}
                                <div className="col-span-2">
                                    <div className="flex items-center justify-between mb-1.5">
                                        <label className="font-semibold text-slate-900 flex items-center gap-1.5">
                                            Tên doanh nghiệp chính thức
                                            <span className="material-symbols-outlined text-[15px] text-slate-400">lock</span>
                                        </label>
                                        <span className="text-xs text-red-600 font-medium flex items-center gap-1">
                                            <span className="material-symbols-outlined text-[13px]">info</span>
                                            Chỉ đọc (Cố định theo GPKD)
                                        </span>
                                    </div>
                                    <div className="relative">
                                        <input 
                                            className="w-full px-3.5 py-2 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 font-semibold cursor-not-allowed select-all" 
                                            readOnly 
                                            type="text" 
                                            value="Công ty Cổ phần Phần mềm FPT (FPT Software)" 
                                        />
                                        <div className="absolute right-3 top-2.5 text-slate-400">
                                            <span className="material-symbols-outlined text-[18px]">lock</span>
                                        </div>
                                    </div>
                                    <p className="mt-1 text-xs text-slate-400">Tên công ty được cố định theo hồ sơ đăng ký kinh doanh đã kiểm duyệt, liên hệ Admin nếu cần thay đổi.</p>
                                </div>

                                {/* READ-ONLY: Mã số thuế */}
                                <div>
                                    <div className="flex items-center justify-between mb-1.5">
                                        <label className="font-semibold text-slate-900 flex items-center gap-1.5">
                                            Mã số thuế (MST)
                                            <span className="material-symbols-outlined text-[15px] text-slate-400">lock</span>
                                        </label>
                                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-teal-50 text-teal-700">
                                            Đã đối soát Tổng cục Thuế
                                        </span>
                                    </div>
                                    <div className="relative">
                                        <input 
                                            className="w-full px-3.5 py-2 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 font-semibold font-mono tracking-wider cursor-not-allowed select-all" 
                                            readOnly 
                                            type="text" 
                                            value="0101248141" 
                                        />
                                        <div className="absolute right-3 top-2.5 text-slate-400">
                                            <span className="material-symbols-outlined text-[18px]">shield_lock</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Quy mô nhân sự (Editable) */}
                                <div>
                                    <label className="block font-semibold text-slate-900 mb-1.5">
                                        Quy mô nhân sự doanh nghiệp <span className="text-red-500">*</span>
                                    </label>
                                    <div className="relative">
                                        <select 
                                            value={scale} 
                                            onChange={(e) => setScale(e.target.value)}
                                            className="w-full px-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e] appearance-none cursor-pointer"
                                        >
                                            <option value="10000+">10,000+ nhân viên (Tập đoàn đa quốc gia)</option>
                                            <option value="5000-10000">5,000 - 10,000 nhân viên</option>
                                            <option value="1000-5000">1,000 - 5,000 nhân viên</option>
                                            <option value="500-1000">500 - 1,000 nhân viên</option>
                                            <option value="100-500">100 - 500 nhân viên</option>
                                        </select>
                                        <div className="pointer-events-none absolute right-3 top-2.5 text-slate-400">
                                            <span className="material-symbols-outlined text-[20px]">expand_more</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Lĩnh vực hoạt động (Tags - Editable) */}
                                <div className="col-span-2">
                                    <label className="block font-semibold text-slate-900 mb-1.5">
                                        Lĩnh vực hoạt động chính (Industry Tags) <span className="text-red-500">*</span>
                                    </label>
                                    <div className="p-2.5 rounded-lg border border-slate-300 bg-white flex flex-wrap items-center gap-2">
                                        {industryTags.map((tag) => (
                                            <span key={tag} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-[#00288e] border border-blue-200 text-xs font-medium">
                                                {tag}
                                                <button onClick={() => handleRemoveTag(tag)} className="hover:text-red-600 transition-colors cursor-pointer" title="Xóa tag">
                                                    <span className="material-symbols-outlined text-[14px]">close</span>
                                                </button>
                                            </span>
                                        ))}
                                        {isAddingTag ? (
                                            <div className="flex items-center gap-1">
                                                <input 
                                                    type="text" 
                                                    value={newTagInput} 
                                                    onChange={(e) => setNewTagInput(e.target.value)} 
                                                    placeholder="Nhập lĩnh vực mới..." 
                                                    className="px-2 py-1 text-xs border border-[#00288e] rounded focus:outline-none"
                                                    autoFocus
                                                />
                                                <button onClick={handleAddTag} className="px-2 py-1 bg-[#00288e] text-white rounded text-xs">Thêm</button>
                                                <button onClick={() => setIsAddingTag(false)} className="px-1 text-xs text-slate-400">Hủy</button>
                                            </div>
                                        ) : (
                                            <button onClick={() => setIsAddingTag(true)} className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-dashed border-slate-300 text-slate-500 hover:text-[#00288e] hover:border-[#00288e] text-xs transition-all cursor-pointer">
                                                <span className="material-symbols-outlined text-[16px]">add</span>
                                                Thêm lĩnh vực
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* Trụ sở chính */}
                                <div className="col-span-2">
                                    <label className="block font-semibold text-slate-900 mb-1.5">
                                        Địa chỉ trụ sở chính <span className="text-red-500">*</span>
                                    </label>
                                    <div className="relative">
                                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400">location_on</span>
                                        <input 
                                            type="text" 
                                            value={address} 
                                            onChange={(e) => setAddress(e.target.value)}
                                            className="w-full pl-9 pr-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e]" 
                                        />
                                    </div>
                                </div>

                                {/* Chi nhánh tiếp nhận */}
                                <div className="col-span-2">
                                    <label className="block font-semibold text-slate-900 mb-1.5">
                                        Chi nhánh tiếp nhận sinh viên thực tập
                                    </label>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                                        <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50">
                                            <span className="flex items-center gap-2">
                                                <span className="w-2 h-2 rounded-full bg-[#00288e]"></span>
                                                <strong>F-Town TP.HCM:</strong> Khu Công nghệ cao TP. Thủ Đức
                                            </span>
                                            <span className="text-[11px] text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded font-medium">Đang mở đợt</span>
                                        </div>
                                        <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50">
                                            <span className="flex items-center gap-2">
                                                <span className="w-2 h-2 rounded-full bg-[#00288e]"></span>
                                                <strong>F-Complex Đà Nẵng:</strong> Nam Kỳ Khởi Nghĩa
                                            </span>
                                            <span className="text-[11px] text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded font-medium">Đang mở đợt</span>
                                        </div>
                                        <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50">
                                            <span className="flex items-center gap-2">
                                                <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                                                <strong>FPT Quy Nhơn:</strong> Trung tâm AI Long Vân
                                            </span>
                                            <span className="text-[11px] text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">Đợt sau</span>
                                        </div>
                                        <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-slate-50">
                                            <span className="flex items-center gap-2">
                                                <span className="w-2 h-2 rounded-full bg-[#00288e]"></span>
                                                <strong>FPT Cần Thơ:</strong> Nguyễn Văn Cừ Nối Dài
                                            </span>
                                            <span className="text-[11px] text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded font-medium">Đang mở đợt</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Website & Email */}
                                <div>
                                    <label className="block font-semibold text-slate-900 mb-1.5">Website chính thức</label>
                                    <div className="relative">
                                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400">language</span>
                                        <input 
                                            type="url" 
                                            value={website} 
                                            onChange={(e) => setWebsite(e.target.value)}
                                            className="w-full pl-9 pr-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e]" 
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block font-semibold text-slate-900 mb-1.5">Email nhận hồ sơ ứng tuyển <span className="text-red-500">*</span></label>
                                    <div className="relative">
                                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400">mail</span>
                                        <input 
                                            type="email" 
                                            value={email} 
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="w-full pl-9 pr-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e]" 
                                        />
                                    </div>
                                </div>

                                {/* Hotline & Chat */}
                                <div className="col-span-2 sm:col-span-1">
                                    <label className="block font-semibold text-slate-900 mb-1.5">Hotline Tuyển dụng & Quản trị thực tập sinh</label>
                                    <div className="relative">
                                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400">call</span>
                                        <input 
                                            type="tel" 
                                            value={hotline} 
                                            onChange={(e) => setHotline(e.target.value)}
                                            className="w-full pl-9 pr-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e]" 
                                        />
                                    </div>
                                </div>
                                <div className="col-span-2 sm:col-span-1">
                                    <label className="block font-semibold text-slate-900 mb-1.5">Kênh liên hệ hỗ trợ nhanh (Zalo/Teams)</label>
                                    <div className="relative">
                                        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-slate-400">chat</span>
                                        <input 
                                            type="text" 
                                            value={chatContact} 
                                            onChange={(e) => setChatContact(e.target.value)}
                                            className="w-full pl-9 pr-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-900 focus:border-[#00288e] focus:ring-1 focus:ring-[#00288e]" 
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 2.2 Rich Text Editor - Company Culture */}
                        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200">
                                <div>
                                    <h2 className="text-lg font-semibold text-slate-900">Văn hóa doanh nghiệp & Môi trường đào tạo</h2>
                                    <p className="text-xs text-slate-500">Nội dung hiển thị trực tiếp trên Portal cho sinh viên và Nhà trường theo dõi</p>
                                </div>
                                <button className="px-2.5 py-1 text-xs rounded border border-slate-200 hover:bg-slate-100 text-slate-700 cursor-pointer">Xem trước hiển thị</button>
                            </div>

                            <div className="border border-slate-300 rounded-t-lg bg-slate-50 p-1.5 flex flex-wrap items-center gap-1">
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700 font-bold" title="Bold"><span className="material-symbols-outlined text-[18px]">format_bold</span></button>
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700 italic" title="Italic"><span className="material-symbols-outlined text-[18px]">format_italic</span></button>
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700" title="Underline"><span className="material-symbols-outlined text-[18px]">format_underlined</span></button>
                                <div className="h-4 w-px bg-slate-300 mx-1"></div>
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700" title="Bullet List"><span className="material-symbols-outlined text-[18px]">format_list_bulleted</span></button>
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700" title="Numbered List"><span className="material-symbols-outlined text-[18px]">format_list_numbered</span></button>
                                <div className="h-4 w-px bg-slate-300 mx-1"></div>
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700" title="Insert Link"><span className="material-symbols-outlined text-[18px]">link</span></button>
                                <button className="p-1.5 rounded hover:bg-slate-200 text-slate-700" title="Insert Image"><span className="material-symbols-outlined text-[18px]">image</span></button>
                            </div>

                            <textarea 
                                value={cultureText} 
                                onChange={(e) => setCultureText(e.target.value)}
                                className="w-full p-4 rounded-b-lg border-t-0 border border-slate-300 bg-white text-sm text-slate-900 focus:border-[#00288e] focus:ring-0 leading-relaxed custom-scroll" 
                                rows={7} 
                            />
                            <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
                                <span>Hỗ trợ định dạng Markdown và HTML tiêu chuẩn</span>
                                <span>{cultureText.length} / 2,000 ký tự</span>
                            </div>
                        </div>

                        {/* 2.3 Benefits & Allowances */}
                        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200">
                                <div>
                                    <h2 className="text-lg font-semibold text-slate-900">Chế độ đãi ngộ & Phúc lợi thực tập sinh</h2>
                                    <p className="text-xs text-slate-500">Chính sách thu hút tài năng sinh viên công khai với nhà trường</p>
                                </div>
                                <button className="inline-flex items-center gap-1 text-xs font-semibold text-[#00288e] hover:underline cursor-pointer">
                                    <span className="material-symbols-outlined text-[16px]">edit</span>
                                    Chỉnh sửa phúc lợi
                                </button>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
                                    <div>
                                        <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center text-[#00288e] mb-3 shadow-xs border border-slate-200">
                                            <span className="material-symbols-outlined text-[20px]">payments</span>
                                        </div>
                                        <h3 className="font-semibold text-slate-900">Trợ cấp cạnh tranh</h3>
                                        <p className="text-xs text-slate-500 mt-1">Từ 6.000.000 - 12.000.000 VNĐ/tháng dựa trên kết quả bài test kỹ thuật đầu vào.</p>
                                    </div>
                                    <span className="mt-3 text-xs text-[#00288e] font-semibold">Thanh toán đúng ngày 05</span>
                                </div>
                                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
                                    <div>
                                        <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center text-indigo-600 mb-3 shadow-xs border border-slate-200">
                                            <span className="material-symbols-outlined text-[20px]">trending_up</span>
                                        </div>
                                        <h3 className="font-semibold text-slate-900">Fast-track Full-time</h3>
                                        <p className="text-xs text-slate-500 mt-1">Hơn 85% thực tập sinh xuất sắc nhận Offer trở thành Nhân viên chính thức trước khi tốt nghiệp.</p>
                                    </div>
                                    <span className="mt-3 text-xs text-indigo-600 font-semibold">Miễn thử việc sau bảo vệ đồ án</span>
                                </div>
                                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
                                    <div>
                                        <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center text-teal-700 mb-3 shadow-xs border border-slate-200">
                                            <span className="material-symbols-outlined text-[20px]">workspace_premium</span>
                                        </div>
                                        <h3 className="font-semibold text-slate-900">Tài trợ Chứng chỉ Quốc tế</h3>
                                        <p className="text-xs text-slate-500 mt-1">Được đài thọ 100% lệ phí thi chứng chỉ Cloud quốc tế (AWS Certified, Microsoft Azure, Google Cloud).</p>
                                    </div>
                                    <span className="mt-3 text-xs text-teal-700 font-semibold">Ngân sách 1,000 USD/bạn</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN (4 COLUMNS) - LEGAL & UPLOAD */}
                    <div className="col-span-12 lg:col-span-4 space-y-6">
                        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200">
                                <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[22px] text-[#00288e]">folder_managed</span>
                                    <h2 className="text-lg font-semibold text-slate-900">Hồ sơ pháp lý doanh nghiệp</h2>
                                </div>
                                <span className="px-2 py-0.5 rounded text-xs bg-teal-50 text-teal-700 font-bold border border-teal-200">{documents.length} Tệp hợp lệ</span>
                            </div>

                            {/* Danh sách tài liệu */}
                            <div className="space-y-3 mb-5 text-sm">
                                {documents.map((doc) => (
                                    <div key={doc.id} className="p-3.5 rounded-lg border border-slate-200 bg-white hover:border-[#00288e]/50 transition-all shadow-xs">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex items-start gap-3">
                                                <div className="w-9 h-9 rounded-lg bg-red-50 text-red-600 flex items-center justify-center shrink-0 border border-red-100">
                                                    <span className="material-symbols-outlined text-[20px]">picture_as_pdf</span>
                                                </div>
                                                <div>
                                                    <h4 className="font-semibold text-slate-900 leading-tight line-clamp-1">{doc.name}</h4>
                                                    <p className="text-xs text-slate-400 mt-0.5">{doc.size} • Tải lên: {doc.date}</p>
                                                    <div className="inline-flex items-center gap-1 mt-1 text-[11px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                                                        <span className="material-symbols-outlined text-[13px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                                                        {doc.status}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-end gap-2 text-xs">
                                            <button className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer" title="Xem trước">
                                                <span className="material-symbols-outlined text-[16px]">visibility</span>
                                                <span>Xem</span>
                                            </button>
                                            <button className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer" title="Tải xuống">
                                                <span className="material-symbols-outlined text-[16px]">download</span>
                                                <span>Tải về</span>
                                            </button>
                                            <button onClick={() => handleDeleteDoc(doc.name)} className="inline-flex items-center gap-1 px-2 py-1 rounded text-red-600 hover:bg-red-50 transition-colors cursor-pointer" title="Xóa">
                                                <span className="material-symbols-outlined text-[16px]">delete</span>
                                                <span>Xóa</span>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Upload Zone */}
                            <div onClick={handleUploadDoc} className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center bg-slate-50 hover:bg-slate-100/80 transition-colors cursor-pointer group">
                                <div className="w-12 h-12 rounded-full bg-white mx-auto flex items-center justify-center text-[#00288e] group-hover:scale-110 transition-transform shadow-xs border border-slate-200">
                                    <span className="material-symbols-outlined text-[24px]">cloud_upload</span>
                                </div>
                                <p className="font-semibold text-slate-900 mt-3 text-sm">Kéo thả tài liệu bổ sung vào đây</p>
                                <p className="text-xs text-slate-400 mt-1">Hỗ trợ PDF, DOCX, JPG hoặc PNG (Tối đa 10MB/tệp)</p>
                                <div className="mt-4">
                                    <button className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white border border-slate-300 hover:border-[#00288e] text-[#00288e] text-xs font-semibold shadow-xs transition-all" type="button">
                                        <span className="material-symbols-outlined text-[18px]">add_circle</span>
                                        Tải lên tài liệu mới
                                    </button>
                                </div>
                            </div>

                            {/* Compliance Checklist */}
                            <div className="mt-5 p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                                <h5 className="font-semibold text-slate-900 mb-2">Quy định thẩm định hồ sơ:</h5>
                                <ul className="text-slate-500 space-y-1.5">
                                    <li className="flex items-start gap-1.5">
                                        <span className="material-symbols-outlined text-[16px] text-teal-700 shrink-0">check</span>
                                        <span>Bản scan màu rõ nét, đầy đủ con dấu pháp nhân.</span>
                                    </li>
                                    <li className="flex items-start gap-1.5">
                                        <span className="material-symbols-outlined text-[16px] text-teal-700 shrink-0">check</span>
                                        <span>Thời hạn hiệu lực tối thiểu 06 tháng kể từ kỳ tiếp nhận.</span>
                                    </li>
                                    <li className="flex items-start gap-1.5">
                                        <span className="material-symbols-outlined text-[16px] text-teal-700 shrink-0">check</span>
                                        <span>Mọi thay đổi hồ sơ sẽ kích hoạt lại quy trình xét duyệt.</span>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        {/* University Partner Integration */}
                        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm text-sm">
                            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
                                <h3 className="font-semibold text-slate-900">Đại học trọng điểm kết nối</h3>
                                <span className="material-symbols-outlined text-[18px] text-slate-400">school</span>
                            </div>
                            <p className="text-xs text-slate-400 mb-3">Hồ sơ đã tự động đồng bộ hóa với hệ thống quản lý thực tập sinh của:</p>
                            <div className="space-y-2 text-xs">
                                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 rounded bg-blue-900 text-white flex items-center justify-center text-[10px] font-bold">BK</div>
                                        <span className="font-medium text-slate-900">Đại học Bách Khoa Hà Nội</span>
                                    </div>
                                    <span className="text-teal-700 font-semibold">Đã ký MOU</span>
                                </div>
                                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 rounded bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold">VNU</div>
                                        <span className="font-medium text-slate-900">ĐHQG TP. Hồ Chí Minh</span>
                                    </div>
                                    <span className="text-teal-700 font-semibold">Đã ký MOU</span>
                                </div>
                                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100">
                                    <div className="flex items-center gap-2">
                                        <div className="w-6 h-6 rounded bg-teal-800 text-white flex items-center justify-center text-[10px] font-bold">RM</div>
                                        <span className="font-medium text-slate-900">RMIT University Vietnam</span>
                                    </div>
                                    <span className="text-teal-700 font-semibold">Đã ký MOU</span>
                                </div>
                            </div>
                        </div>

                        {/* Audit Log */}
                        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm text-xs">
                            <div className="flex items-center gap-2 text-slate-400 mb-2">
                                <span className="material-symbols-outlined text-[16px]">history</span>
                                <span className="font-semibold">Lịch sử cập nhật gần nhất</span>
                            </div>
                            <p className="text-slate-600 leading-snug">Hồ sơ được cập nhật lần cuối lúc <strong>14:28 - 24/02/2025</strong> bởi <strong>Khôi Nguyễn (Lead HR)</strong></p>
                        </div>
                    </div>
                </div>

                {/* 3. STICKY BOTTOM CONFIRMATION TRAY */}
                <div className="fixed bottom-4 left-[276px] right-6 z-20 bg-white/95 backdrop-blur-md border border-slate-200 p-4 rounded-xl shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-teal-500 animate-pulse"></div>
                        <div>
                            <span className="font-semibold text-slate-900 text-sm">Tất cả thay đổi nội dung đã được lưu nháp cục bộ</span>
                            <p className="text-xs text-slate-400">Bấm "Lưu thông tin hồ sơ" để gửi thông báo xác nhận cập nhật đến Nhà trường</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                        <button className="px-4 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100 text-sm font-semibold transition-colors cursor-pointer">
                            Đặt lại ban đầu
                        </button>
                        <button 
                            onClick={handleSaveProfile} 
                            disabled={isSaving}
                            className="px-6 py-2 rounded-lg bg-[#00288e] hover:bg-blue-800 text-white font-semibold shadow-md transition-all active:scale-95 cursor-pointer flex items-center gap-2 text-sm disabled:opacity-75"
                        >
                            {isSaving ? (
                                <>
                                    <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
                                    <span>Đang lưu hồ sơ...</span>
                                </>
                            ) : saveSuccess ? (
                                <>
                                    <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>check</span>
                                    <span>Đã lưu thành công!</span>
                                </>
                            ) : (
                                <>
                                    <span className="material-symbols-outlined text-[18px]">check_circle</span>
                                    <span>Lưu thông tin hồ sơ</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
};