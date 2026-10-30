import { useEffect, useMemo, useRef, useState } from "react";

export type InternshipEvaluationPayload = {
  result_id: string;
  evaluation: string;
  score: number;
};

type InternshipEvaluationPageProps = {
  /** Mã kết quả thực tập đang được chọn. Thiếu mã thì form không được mở. */
  resultId?: string | number | null;
  /** Quyền đánh giá đã được xác minh từ backend/route guard. */
  canEvaluate?: boolean;
  /** Hàm gọi API lưu đánh giá từ component cha. */
  onSubmitEvaluation?: (payload: InternshipEvaluationPayload) => Promise<void> | void;
  /** Thông báo về component cha khi chọn kết quả trong danh sách. */
  onSelectResult?: (resultId: string) => void;
};

// Giữ nguyên toàn bộ nội dung giao diện DGTT gốc; chỉ bổ sung data-result-id
// cho các dòng sinh viên và name/required cho hai trường cần gửi backend.
const PAGE_BODY_HTML = String.raw`
<!-- LEFT NAVIGATION SIDEBAR (Exact 3-Role Section Architecture from Reference Image) -->
<aside class="fixed left-0 top-0 h-full w-[260px] z-40 flex flex-col justify-between p-4 bg-surface-container-lowest dark:bg-inverse-surface border-r border-outline-variant dark:border-outline overflow-y-auto custom-scrollbar">
<!-- Top Branding Anchor -->
<div class="flex flex-col gap-4">
<div class="flex items-center gap-3 px-2 py-1">
<div class="w-10 h-10 rounded-xl bg-primary-container text-on-primary flex items-center justify-center font-bold text-title-lg shadow-sm">
<span class="material-symbols-outlined text-white" style="font-size: 24px;">domain</span>
</div>
<div class="flex flex-col">
<span class="text-title-lg font-title-lg font-bold text-primary dark:text-primary-fixed leading-tight">Student Connect</span>
<span class="text-label-md font-label-md text-outline">Enterprise Portal</span>
</div>
</div>
<!-- Quick CTA Button -->
<button class="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-primary-container text-white text-label-lg font-label-lg font-semibold hover:bg-primary transition-all duration-150 shadow-sm active:scale-[0.99]">
<span class="material-symbols-outlined text-white" style="font-size: 18px;">add_circle</span>
<span>Đăng tin mới</span>
</button>
<!-- NAVIGATION ROLES BLOCK (EXACT HIERARCHY MATCHING REFERENCE IMAGE) -->
<div class="flex flex-col gap-4 mt-2">
<!-- BLOCK 1: SINH VIÊN -->
<div class="flex flex-col gap-1">
<div class="px-3 py-1 text-label-xs font-label-xs tracking-wider text-outline uppercase font-semibold">
            SINH VIÊN
          </div>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">search</span>
<span>Tìm việc làm</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">auto_awesome</span>
<span>Gợi ý việc làm</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">bookmark_border</span>
<span>Việc đã lưu</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">person_outline</span>
<span>Hồ sơ cá nhân</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">description</span>
<span>Quản lý CV</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">send</span>
<span>Đơn ứng tuyển</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">mail_outline</span>
<span>Lời mời phỏng vấn</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">school</span>
<span>Theo dõi thực tập</span>
</a>
</div>
<div class="h-px bg-surface-container-high mx-2"></div>
<!-- BLOCK 2: DOANH NGHIỆP (CURRENT PORTAL / CONTEXT) -->
<div class="flex flex-col gap-1">
<div class="px-3 py-1 text-label-xs font-label-xs tracking-wider text-outline uppercase font-semibold">
            DOANH NGHIỆP
          </div>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">post_add</span>
<span>Tin tuyển dụng</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">group</span>
<span>Quản lý ứng viên</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">person_search</span>
<span>Gợi ý ứng viên</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">mark_email_read</span>
<span>Lời mời đã gửi</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">apartment</span>
<span>Hồ sơ công ty</span>
</a>
<!-- Mandatory Active Screen for this flow: Đánh giá thực tập -->
<a class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-surface-container-low dark:bg-surface-container text-primary dark:text-primary-fixed font-title-md text-title-md border-l-4 border-primary dark:border-primary-fixed cursor-pointer transition-all duration-150" href="#">
<span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1;">rate_review</span>
<span class="font-semibold text-primary">Đánh giá thực tập</span>
</a>
</div>
<div class="h-px bg-surface-container-high mx-2"></div>
<!-- BLOCK 3: NHÀ TRƯỜNG / ADMIN -->
<div class="flex flex-col gap-1">
<div class="px-3 py-1 text-label-xs font-label-xs tracking-wider text-outline uppercase font-semibold">
            NHÀ TRƯỜNG / ADMIN
          </div>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">monitoring</span>
<span>Tổng quan hệ thống</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">badge</span>
<span>Quản lý sinh viên</span>
</a>
</div>
</div>
</div>
<!-- Footer System Actions -->
<div class="pt-4 border-t border-outline-variant flex flex-col gap-1">
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">settings</span>
<span>Cài đặt hệ thống</span>
</a>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors duration-150 font-body-md text-body-md" href="#">
<span class="material-symbols-outlined text-outline">help</span>
<span>Hỗ trợ &amp; Trợ giúp</span>
</a>
</div>
</aside>
<!-- TOP APP BAR -->
<header class="sticky top-0 right-0 z-30 flex items-center justify-between w-[calc(100%-260px)] ml-[260px] h-16 px-6 bg-surface-container-lowest dark:bg-inverse-surface border-b border-outline-variant dark:border-outline shadow-sm">
<!-- Left Search & Context Bar -->
<div class="flex items-center gap-4 w-96">
<div class="relative w-full">
<span class="material-symbols-outlined absolute left-3 top-2.5 text-outline pointer-events-none" style="font-size: 18px;">search</span>
<input class="w-full h-10 pl-9 pr-3 rounded-lg border border-outline-variant text-body-md placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-primary-container bg-surface-bright transition-all" placeholder="Tìm theo MSSV, tên thực tập sinh, result_id..." type="text"/>
</div>
</div>
<!-- Trailing Action Cluster -->
<div class="flex items-center gap-4">
<div class="flex items-center gap-2 border-r border-outline-variant pr-4">
<button class="relative p-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors">
<span class="material-symbols-outlined">notifications</span>
<span class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-error"></span>
</button>
<button class="p-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors">
<span class="material-symbols-outlined">help_outline</span>
</button>
</div>
<!-- Quick Action -->
<button class="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-surface-container text-primary font-title-md text-title-md hover:bg-surface-container-high transition-colors">
<span class="material-symbols-outlined" style="font-size: 18px;">video_call</span>
<span>Tạo phỏng vấn</span>
</button>
<!-- HR Profile Indicator -->
<div class="flex items-center gap-3 pl-2">
<div class="text-right">
<p class="font-title-md text-title-md text-on-surface font-semibold leading-none">Võ Minh Khôi</p>
<p class="text-label-md font-label-md text-outline mt-1">HR Lead / Mentor FPT Software</p>
</div>
<img alt="Company HR Administrator Profile Picture" class="w-10 h-10 rounded-full object-cover ring-2 ring-surface-variant" data-alt="Professional corporate headshot of a friendly Vietnamese HR manager wearing navy blue business casual attire with bright modern tech office background." src="https://lh3.googleusercontent.com/aida-public/AB6AXuB-ebbkJlUN4SEych7VwvsVdAmrI-mlVy-zKmqW6s2NOwv2CadbgW_eimtDcGjMAEUAr7nft3-fPhGJZuB2ZY-mNICWnhY4OTNu4Nb7eHGZbbkUgXfBtpd2lRM9XzXwLQwG4CuY4wQBKwuwoQG6Xk-aqSyEGkjewgFRPXQUKf966zyAqGHkR7eStPgnEnUPnMqtBfB8Xw93UJXxgpVhIvUGMF9Ar91RgYloikpNNhE"/>
</div>
</div>
</header>
<!-- MAIN CANVAS (12-column responsive workspace for Enterprise Review) -->
<main class="w-[calc(100%-260px)] ml-[260px] p-6 min-h-[calc(100vh-64px)] bg-background flex flex-col gap-6">
<!-- PAGE HEADER & COHORT SELECTOR -->
<div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-surface-container-lowest p-6 rounded-xl border border-outline-variant shadow-sm">
<div class="flex flex-col gap-1 max-w-2xl">
<div class="flex items-center gap-2">
<span class="px-2.5 py-0.5 rounded-full text-label-xs font-semibold bg-primary-container text-white">Doanh Nghiệp / Mentor Portal</span>
<span class="text-label-md text-outline">• Hợp đồng 3 bên (Nhà trường - Doanh nghiệp - Sinh viên)</span>
</div>
<h1 class="text-headline-lg font-headline-lg text-primary tracking-tight">Đánh giá kết quả thực tập</h1>
<p class="text-body-md text-on-surface-variant">
          Đánh giá năng lực chuyên môn, thái độ và chấm điểm cuối kỳ cho sinh viên hoàn thành đợt thực tập tại doanh nghiệp theo thỏa thuận 3 bên.
        </p>
</div>
<!-- Cohort Selector Box -->
<div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
<div class="flex flex-col">
<label class="text-label-md font-label-md text-outline mb-1 font-semibold">Đợt thực tập áp dụng:</label>
<div class="relative inline-block w-72">
<select class="w-full h-10 pl-3 pr-8 rounded-lg border border-outline-variant bg-surface text-body-md font-medium text-on-surface focus:ring-2 focus:ring-primary-container focus:outline-none">
<option selected="">Học kỳ Doanh nghiệp Fall 2026 (08/2026 - 12/2026)</option>
<option>Học kỳ Doanh nghiệp Summer 2026 (05/2026 - 08/2026)</option>
<option>Học kỳ Doanh nghiệp Spring 2026 (01/2026 - 04/2026)</option>
</select>
</div>
</div>
<button class="h-10 px-4 mt-auto rounded-lg border border-outline-variant bg-surface hover:bg-surface-container text-on-surface-variant flex items-center gap-2 text-label-lg font-label-lg font-medium transition-colors">
<span class="material-symbols-outlined" style="font-size: 18px;">download</span>
<span>Xuất báo cáo PDF</span>
</button>
</div>
</div>
<!-- METRICS & STATUS SUMMARY STRIP -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
<!-- Metric 1 -->
<div class="bg-surface-container-lowest p-5 rounded-xl border border-outline-variant shadow-sm flex flex-col justify-between">
<div class="flex items-center justify-between">
<span class="text-label-xs font-label-xs text-outline uppercase font-semibold">Tổng SV Tiếp nhận</span>
<span class="p-1.5 rounded-lg bg-surface-container text-primary">
<span class="material-symbols-outlined" style="font-size: 18px;">groups</span>
</span>
</div>
<div class="mt-2">
<span class="text-display-lg font-display-lg text-on-surface">18</span>
<span class="text-body-sm text-outline ml-1">sinh viên</span>
</div>
<div class="mt-2 flex items-center gap-1.5 text-body-sm text-outline">
<span class="w-2 h-2 rounded-full bg-primary-container"></span>
<span>Phân bổ 5 dự án nội bộ</span>
</div>
</div>
<!-- Metric 2 -->
<div class="bg-surface-container-lowest p-5 rounded-xl border border-outline-variant shadow-sm flex flex-col justify-between">
<div class="flex items-center justify-between">
<span class="text-label-xs font-label-xs text-outline uppercase font-semibold">Đã hoàn thành đánh giá</span>
<span class="p-1.5 rounded-lg bg-green-50 text-green-700">
<span class="material-symbols-outlined" style="font-size: 18px;">task_alt</span>
</span>
</div>
<div class="mt-2">
<span class="text-display-lg font-display-lg text-green-700">14</span>
<span class="text-body-sm text-outline ml-1">/ 18 hồ sơ</span>
</div>
<div class="mt-2 flex items-center gap-1.5 text-body-sm text-green-600 font-medium">
<span class="material-symbols-outlined" style="font-size: 16px;">trending_up</span>
<span>Đạt tiến độ 77.8%</span>
</div>
</div>
<!-- Metric 3 -->
<div class="bg-surface-container-lowest p-5 rounded-xl border border-outline-variant shadow-sm flex flex-col justify-between ring-1 ring-amber-300">
<div class="flex items-center justify-between">
<span class="text-label-xs font-label-xs text-amber-800 uppercase font-semibold">Chờ doanh nghiệp chấm điểm</span>
<span class="p-1.5 rounded-lg bg-amber-100 text-amber-800">
<span class="material-symbols-outlined" style="font-size: 18px;">pending_actions</span>
</span>
</div>
<div class="mt-2">
<span class="text-display-lg font-display-lg text-amber-700">04</span>
<span class="text-body-sm text-outline ml-1">sinh viên</span>
</div>
<div class="mt-2 flex items-center gap-1.5 text-body-sm text-amber-700 font-medium">
<span class="material-symbols-outlined" style="font-size: 16px;">alarm</span>
<span>Hạn nộp: 15/12/2026 (Còn 3 ngày)</span>
</div>
</div>
<!-- Metric 4 -->
<div class="bg-surface-container-lowest p-5 rounded-xl border border-outline-variant shadow-sm flex flex-col justify-between">
<div class="flex items-center justify-between">
<span class="text-label-xs font-label-xs text-outline uppercase font-semibold">Tỷ lệ Đề xuất Fulltime</span>
<span class="p-1.5 rounded-lg bg-surface-container text-secondary">
<span class="material-symbols-outlined" style="font-size: 18px;">workspace_premium</span>
</span>
</div>
<div class="mt-2">
<span class="text-display-lg font-display-lg text-secondary">64.3%</span>
<span class="text-body-sm text-outline ml-1">(9 / 14 đã đánh giá)</span>
</div>
<div class="mt-2 flex items-center gap-1.5 text-body-sm text-outline">
<span class="material-symbols-outlined text-outline" style="font-size: 16px;">person_add</span>
<span>Sẵn sàng ký hợp đồng thử việc</span>
</div>
</div>
</div>
<!-- MASTER-DETAIL WORKSPACE (Left: Student Cohort List | Right: Evaluation Form by result_id) -->
<div class="grid grid-cols-12 gap-6 items-start">
<!-- LEFT MASTER COLUMN: Cohort Student List (4 Cols) -->
<div class="col-span-12 lg:col-span-4 flex flex-col gap-4">
<div class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden flex flex-col">
<div class="p-4 border-b border-outline-variant flex items-center justify-between bg-surface-bright">
<div>
<h2 class="text-title-md font-title-md font-bold text-on-surface">Danh sách thực tập sinh</h2>
<p class="text-body-sm text-outline">Chọn hồ sơ để mở phiếu đánh giá theo <code class="bg-surface-container px-1 py-0.5 rounded text-primary font-mono text-label-xs">result_id</code></p>
</div>
<span class="px-2 py-0.5 rounded bg-surface-container text-primary font-semibold text-label-xs">18 SV</span>
</div>
<!-- Filter Search in Master Column -->
<div class="p-3 border-b border-outline-variant bg-surface-container-lowest">
<div class="relative">
<span class="material-symbols-outlined absolute left-2.5 top-2.5 text-outline text-body-md" style="font-size: 16px;">filter_list</span>
<input class="w-full h-8 pl-8 pr-3 text-body-sm rounded border border-outline-variant bg-surface focus:outline-none focus:ring-1 focus:ring-primary" placeholder="Lọc nhanh SV hoặc mã hồ sơ..." type="text"/>
</div>
</div>
<!-- Student Items List -->
<div class="divide-y divide-outline-variant overflow-y-auto max-h-[660px] custom-scrollbar">
<!-- Item 1: Active Target Candidate (Lê Hoàng Long - result_id #RES-2026-FPT-042) -->
<div data-result-id="RES-2026-FPT-042" role="button" tabindex="0" class="p-4 bg-surface-container-low border-l-4 border-primary transition-all cursor-pointer">
<div class="flex items-start justify-between gap-2">
<div class="flex items-center gap-2">
<span class="font-mono text-label-xs font-semibold text-primary px-1.5 py-0.5 rounded bg-surface-container">#RES-2026-FPT-042</span>
<span class="px-2 py-0.5 rounded-full text-label-xs font-semibold bg-amber-100 text-amber-800 flex items-center gap-1">
<span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                    Chờ đánh giá
                  </span>
</div>
<span class="text-label-xs text-outline font-medium">Hạn: 15/12</span>
</div>
<div class="mt-2.5 flex items-center gap-3">
<img alt="Student Avatar" class="w-10 h-10 rounded-full object-cover ring-2 ring-primary" data-alt="Young energetic Vietnamese male software engineering university student with glasses smiling confidently in a clean white campus backdrop." src="https://lh3.googleusercontent.com/aida-public/AB6AXuBY-5qcdHJ2YLQ9RCPsjpDC3UQtmTa3gBQmFluUBketfrkfkP_Ku94GUKqUYYQ1Hl9B8ehHHyyx3k2eMFiy-fz7XbpFX0gntKj99hOgC5WpDVmXTgaFm2bA4LLUvLMs0cPcSTAXpkU4jZnTr4cqTDrJ8fiWIoem-2kV29vIHhYWDxYgLBKgYeIdGRTMdv685kW3BOx2E_9eiJX8q9hsWfSXBxBmX35vwjqB6UTV8u0"/>
<div>
<h3 class="font-title-md text-title-md font-bold text-on-surface">Lê Hoàng Long</h3>
<p class="text-body-sm text-outline">Frontend React Intern • MSSV: SE160912</p>
</div>
</div>
<div class="mt-3 flex items-center justify-between text-body-sm text-on-surface-variant pt-2 border-t border-outline-variant/60">
<span class="text-outline text-label-xs">Đại học FPT Cần Thơ</span>
<span class="font-semibold text-primary text-label-xs">Mentor: Võ Minh Khôi</span>
</div>
</div>
<!-- Item 2: Another Pending Item -->
<div data-result-id="RES-2026-FPT-039" role="button" tabindex="0" class="p-4 hover:bg-surface-container transition-all cursor-pointer">
<div class="flex items-start justify-between gap-2">
<div class="flex items-center gap-2">
<span class="font-mono text-label-xs font-semibold text-outline px-1.5 py-0.5 rounded bg-surface-bright">#RES-2026-FPT-039</span>
<span class="px-2 py-0.5 rounded-full text-label-xs font-semibold bg-amber-100 text-amber-800">
                    Chờ đánh giá
                  </span>
</div>
<span class="text-label-xs text-outline font-medium">Hạn: 15/12</span>
</div>
<div class="mt-2.5 flex items-center gap-3">
<div class="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center font-bold text-primary">
                  TN
                </div>
<div>
<h3 class="font-title-md text-title-md font-semibold text-on-surface">Trần Ngọc Thảo</h3>
<p class="text-body-sm text-outline">UI/UX Product Design Intern</p>
</div>
</div>
<div class="mt-3 flex items-center justify-between text-body-sm text-outline pt-2 border-t border-outline-variant/60">
<span class="text-label-xs">RMIT Vietnam</span>
<span class="text-label-xs">Mentor: Nguyễn Anh Tuấn</span>
</div>
</div>
<!-- Item 3: Completed Item -->
<div data-result-id="RES-2026-FPT-031" role="button" tabindex="0" class="p-4 hover:bg-surface-container transition-all cursor-pointer opacity-85">
<div class="flex items-start justify-between gap-2">
<div class="flex items-center gap-2">
<span class="font-mono text-label-xs font-semibold text-outline px-1.5 py-0.5 rounded bg-surface-bright">#RES-2026-FPT-031</span>
<span class="px-2 py-0.5 rounded-full text-label-xs font-semibold bg-green-100 text-green-800 flex items-center gap-1">
<span class="material-symbols-outlined" style="font-size: 12px;">check</span>
                    Đã gửi (9.2/10)
                  </span>
</div>
<span class="text-label-xs text-outline font-medium">10/12/2026</span>
</div>
<div class="mt-2.5 flex items-center gap-3">
<div class="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center font-bold text-primary">
                  ĐM
                </div>
<div>
<h3 class="font-title-md text-title-md font-semibold text-on-surface">Đỗ Minh Quân</h3>
<p class="text-body-sm text-outline">Backend Golang Intern</p>
</div>
</div>
<div class="mt-3 flex items-center justify-between text-body-sm text-outline pt-2 border-t border-outline-variant/60">
<span class="text-label-xs">ĐH Bách Khoa HCM</span>
<span class="text-label-xs text-green-700 font-medium">Đề xuất Offer FTE</span>
</div>
</div>
<!-- Item 4: Completed Item -->
<div data-result-id="RES-2026-FPT-027" role="button" tabindex="0" class="p-4 hover:bg-surface-container transition-all cursor-pointer opacity-85">
<div class="flex items-start justify-between gap-2">
<div class="flex items-center gap-2">
<span class="font-mono text-label-xs font-semibold text-outline px-1.5 py-0.5 rounded bg-surface-bright">#RES-2026-FPT-027</span>
<span class="px-2 py-0.5 rounded-full text-label-xs font-semibold bg-green-100 text-green-800 flex items-center gap-1">
<span class="material-symbols-outlined" style="font-size: 12px;">check</span>
                    Đã gửi (8.5/10)
                  </span>
</div>
<span class="text-label-xs text-outline font-medium">08/12/2026</span>
</div>
<div class="mt-2.5 flex items-center gap-3">
<div class="w-10 h-10 rounded-full bg-surface-container-high flex items-center justify-center font-bold text-primary">
                  NL
                </div>
<div>
<h3 class="font-title-md text-title-md font-semibold text-on-surface">Nguyễn Linh Đan</h3>
<p class="text-body-sm text-outline">QA / Automation Tester Intern</p>
</div>
</div>
<div class="mt-3 flex items-center justify-between text-body-sm text-outline pt-2 border-t border-outline-variant/60">
<span class="text-label-xs">ĐH Công nghệ thông tin (VNU)</span>
<span class="text-label-xs text-outline">Tiêu chuẩn</span>
</div>
</div>
</div>
<div class="p-3 bg-surface border-t border-outline-variant text-center">
<span class="text-label-xs text-outline">Hiển thị 4 trên tổng số 18 sinh viên</span>
</div>
</div>
<!-- Quick Help Note / Policy Anchor -->
<div class="p-4 rounded-xl bg-surface-container-low border border-outline-variant text-body-sm text-on-surface-variant flex gap-3">
<span class="material-symbols-outlined text-primary" style="font-size: 22px;">info</span>
<div>
<p class="font-semibold text-primary">Quy định thẩm định kết quả</p>
<p class="text-outline text-label-md mt-1">
              Điểm số sau khi gửi qua hệ thống sẽ được khóa và gửi trực tiếp đến Cổng thông tin Khoa &amp; Giảng viên phụ trách. Doanh nghiệp có 24h để thu hồi sửa đổi nếu có sai sót kỹ thuật.
            </p>
</div>
</div>
</div>
<!-- RIGHT DETAIL COLUMN: INTERNSHIP EVALUATION FORM (8 Cols - Active by result_id) -->
<div class="col-span-12 lg:col-span-8 flex flex-col gap-6">
<form class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden flex flex-col">
<!-- Contract & Identity Ribbon (Tripartite Agreement Context) -->
<div class="p-6 bg-gradient-to-r from-surface-container-low via-surface-container to-surface-bright border-b border-outline-variant">
<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
<div>
<div class="flex items-center gap-2">
<span class="bg-primary text-white text-label-xs font-mono font-bold px-2 py-0.5 rounded">result_id: #RES-2026-FPT-042</span>
<span class="text-label-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-primary">Hợp đồng Thực tập Doanh nghiệp</span>
</div>
<h2 class="text-headline-md font-headline-md font-bold text-on-surface mt-2">Phiếu Đánh Giá Kết Quả Thực Tập Cuối Kỳ</h2>
<p class="text-body-sm text-on-surface-variant mt-0.5">Thời hạn thẩm định 3 bên: 01/08/2026 – 15/12/2026 (16 tuần thực tế tại doanh nghiệp)</p>
</div>
<div class="text-left sm:text-right bg-white p-3 rounded-lg border border-outline-variant/60 shadow-xs">
<span class="text-label-xs text-outline uppercase font-semibold">Trạng thái hồ sơ</span>
<p class="text-title-md font-bold text-amber-700 flex items-center sm:justify-end gap-1.5 mt-0.5">
<span class="material-symbols-outlined" style="font-size: 16px;">hourglass_top</span>
                  Chờ doanh nghiệp gửi điểm
                </p>
</div>
</div>
<!-- Bento Metadata Strip for Candidate & University Supervisor -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-5 pt-4 border-t border-outline-variant/60">
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/60">
<span class="text-label-xs text-outline font-semibold uppercase">Sinh viên thực tập</span>
<p class="text-title-md font-bold text-on-surface mt-0.5">Lê Hoàng Long</p>
<p class="text-label-md text-outline">MSSV: SE160912 • K16 CNTT</p>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/60">
<span class="text-label-xs text-outline font-semibold uppercase">Đơn vị Đào tạo &amp; GV Phụ trách</span>
<p class="text-title-md font-bold text-on-surface mt-0.5">ĐH FPT Cần Thơ</p>
<p class="text-label-md text-outline">GVHD: TS. Trần Văn Minh (Khoa CNTT)</p>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/60">
<span class="text-label-xs text-outline font-semibold uppercase">Bộ phận &amp; Mentor Phụ trách</span>
<p class="text-title-md font-bold text-on-surface mt-0.5">FPT Software (BU9 - Frontend)</p>
<p class="text-label-md text-outline">Mentor: Võ Minh Khôi (Tech Lead)</p>
</div>
</div>
</div>
<!-- EVALUATION RUBRIC & SCORING SECTION -->
<div class="p-6 flex flex-col gap-6">
<!-- SCORE HIGHLIGHT CONTAINER (Backend Score Mapping 0.0 - 10.0) -->
<div class="p-5 rounded-xl bg-surface-container-low border border-primary/20 flex flex-col md:flex-row md:items-center justify-between gap-6">
<div>
<label class="text-label-md font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
<span class="material-symbols-outlined" style="font-size: 18px;">grade</span>
                  Điểm số tổng kết cuối kỳ (Score 0.0 – 10.0)
                </label>
<p class="text-body-sm text-outline mt-1 max-w-md">
                  Điểm tổng hợp phản ánh toàn diện kết quả thực tập, sẽ được đồng bộ trực tiếp vào hệ thống bảng điểm đại học của sinh viên.
                </p>
</div>
<div class="flex items-center gap-4">
<div class="text-right">
<div class="flex items-baseline justify-end gap-1">
<input class="w-24 h-12 text-center text-display-lg font-display-lg font-bold text-primary rounded-lg border-2 border-primary bg-white focus:outline-none focus:ring-2 focus:ring-primary shadow-xs" id="finalScoreInput" name="score" max="10" min="0" step="0.1" type="number" value="9.0" required/>
<span class="text-headline-sm font-headline-sm text-outline">/ 10.0</span>
</div>
<span class="inline-block mt-1 text-label-md font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded" id="rankBadge">
                    Xếp loại: Xuất sắc (Excellent)
                  </span>
</div>
</div>
</div>
<!-- DETAILED EVALUATION CRITERIA (RUBRIC 3 TIÊU CHÍ CHÍNH) -->
<div class="flex flex-col gap-4">
<h3 class="text-title-lg font-title-lg font-bold text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-primary">checklist</span>
                Tiêu chí đánh giá năng lực chi tiết (Evaluation Rubrics)
              </h3>
<!-- Rubric 1 -->
<div class="p-4 rounded-lg border border-outline-variant bg-surface-bright flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
<div class="max-w-md">
<div class="flex items-center gap-2">
<span class="w-6 h-6 rounded-full bg-primary-container text-white text-label-xs flex items-center justify-center font-bold">1</span>
<h4 class="font-title-md text-title-md font-semibold text-on-surface">Kỹ năng chuyên môn &amp; Tiến độ dự án</h4>
</div>
<p class="text-body-sm text-outline mt-1 pl-8">
                    Năng lực lập trình React/TypeScript, xử lý state quản lý component, hoàn thành task Jira đúng sprint và tuân thủ Clean Code.
                  </p>
</div>
<div class="flex items-center gap-3 pl-8 sm:pl-0">
<span class="text-label-md text-outline font-medium">Trọng số 40%</span>
<select class="h-10 px-3 rounded-lg border border-outline-variant bg-white text-body-md font-semibold text-primary focus:ring-2 focus:ring-primary focus:outline-none">
<option>10.0 - Xuất sắc</option>
<option selected="">9.2 - Tốt vượt kỳ vọng</option>
<option>8.0 - Đạt yêu cầu</option>
<option>6.5 - Cần cải thiện</option>
<option>5.0 - Chưa đạt</option>
</select>
</div>
</div>
<!-- Rubric 2 -->
<div class="p-4 rounded-lg border border-outline-variant bg-surface-bright flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
<div class="max-w-md">
<div class="flex items-center gap-2">
<span class="w-6 h-6 rounded-full bg-primary-container text-white text-label-xs flex items-center justify-center font-bold">2</span>
<h4 class="font-title-md text-title-md font-semibold text-on-surface">Tính chủ động &amp; Tự học công nghệ mới</h4>
</div>
<p class="text-body-sm text-outline mt-1 pl-8">
                    Khả năng tự nghiên cứu tài liệu kỹ thuật, áp dụng Tailwind CSS &amp; Next.js vào dự án sản phẩm thực tế mà không cần chỉ dẫn liên tục.
                  </p>
</div>
<div class="flex items-center gap-3 pl-8 sm:pl-0">
<span class="text-label-md text-outline font-medium">Trọng số 30%</span>
<select class="h-10 px-3 rounded-lg border border-outline-variant bg-white text-body-md font-semibold text-primary focus:ring-2 focus:ring-primary focus:outline-none">
<option selected="">9.0 - Tốt vượt kỳ vọng</option>
<option>8.0 - Đạt yêu cầu</option>
<option>7.0 - Khá</option>
<option>5.0 - Thiếu chủ động</option>
</select>
</div>
</div>
<!-- Rubric 3 -->
<div class="p-4 rounded-lg border border-outline-variant bg-surface-bright flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
<div class="max-w-md">
<div class="flex items-center gap-2">
<span class="w-6 h-6 rounded-full bg-primary-container text-white text-label-xs flex items-center justify-center font-bold">3</span>
<h4 class="font-title-md text-title-md font-semibold text-on-surface">Kỷ luật, Giao tiếp &amp; Tinh thần đồng đội</h4>
</div>
<p class="text-body-sm text-outline mt-1 pl-8">
                    Đảm bảo tỷ lệ chuyên cần (attendance 98%), tham gia Daily Scrum đúng giờ, tích cực trao đổi và lắng nghe phản hồi từ Senior.
                  </p>
</div>
<div class="flex items-center gap-3 pl-8 sm:pl-0">
<span class="text-label-md text-outline font-medium">Trọng số 30%</span>
<select class="h-10 px-3 rounded-lg border border-outline-variant bg-white text-body-md font-semibold text-primary focus:ring-2 focus:ring-primary focus:outline-none">
<option selected="">8.8 - Rất tích cực</option>
<option>8.0 - Đạt chuẩn tác phong</option>
<option>7.0 - Chấp hành</option>
<option>5.0 - Vi phạm giờ giấc</option>
</select>
</div>
</div>
</div>
<!-- DETAILED REMARKS / EVALUATION TEXT AREA (Backend field: evaluation) -->
<div class="flex flex-col gap-2">
<div class="flex items-center justify-between">
<label class="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2" for="evaluationText">
<span class="material-symbols-outlined text-primary">edit_note</span>
                  Nhận xét chi tiết của Doanh nghiệp &amp; Mentor (evaluation)
                </label>
<span class="text-label-xs text-outline">Bắt buộc tối thiểu 50 từ</span>
</div>
<textarea class="w-full p-3.5 rounded-lg border border-outline-variant bg-surface-bright text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-primary-container leading-relaxed transition-all" id="evaluationText" name="evaluation" required placeholder="Nhập đánh giá cụ thể về thái độ, đóng góp thực tế trong dự án phần mềm, điểm mạnh và điểm cần cải thiện..." rows="4">Lê Hoàng Long thể hiện sự vượt trội về tư duy thuật toán và khả năng thích ứng với framework React/Next.js trong suốt 16 tuần thực tập tại BU9. Em hoàn thành xuất sắc module quản trị người dùng cho khách hàng APAC với chỉ số bug cực thấp (0.4 defect/KLOC). Thái độ chuyên nghiệp, hòa đồng và luôn sẵn sàng hỗ trợ các thành viên khác trong sprint. Đội ngũ kỹ thuật đánh giá rất cao tiềm năng phát triển thành Full-stack Developer.</textarea>
<p class="text-body-sm text-outline">Ghi chú: Nhận xét này sẽ hiển thị trực tiếp trên học bạ thực tập điện tử của Nhà trường.</p>
</div>
<!-- HIRING RECOMMENDATION RADIO (Next Step / Conversion) -->
<div class="p-4 rounded-xl border border-outline-variant bg-surface-bright flex flex-col gap-3">
<label class="text-title-md font-title-md font-bold text-on-surface flex items-center gap-2">
<span class="material-symbols-outlined text-secondary">handshake</span>
                Khuyến nghị tuyển dụng sau thực tập (Hiring Intent Recommendation)
              </label>
<div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-1">
<!-- Option 1 -->
<label class="relative flex flex-col p-3.5 rounded-lg border-2 border-primary bg-primary-fixed/20 cursor-pointer hover:bg-primary-fixed/30 transition-all">
<div class="flex items-center justify-between">
<span class="font-title-md text-title-md font-bold text-primary">Đề xuất Offer FTE</span>
<input checked="" class="text-primary focus:ring-primary w-4 h-4" name="recommendation" type="radio" value="fte"/>
</div>
<p class="text-body-sm text-on-surface-variant mt-1.5 leading-snug">
                    Đề xuất ký hợp đồng Nhân viên chính thức (Junior Fulltime) ngay khi tốt nghiệp.
                  </p>
</label>
<!-- Option 2 -->
<label class="relative flex flex-col p-3.5 rounded-lg border border-outline-variant bg-white cursor-pointer hover:bg-surface-container transition-all">
<div class="flex items-center justify-between">
<span class="font-title-md text-title-md font-semibold text-on-surface">Gia hạn Part-time</span>
<input class="text-primary focus:ring-primary w-4 h-4" name="recommendation" type="radio" value="parttime"/>
</div>
<p class="text-body-sm text-outline mt-1.5 leading-snug">
                    Tiếp tục làm việc bán thời gian trong thời gian sinh viên làm đồ án tốt nghiệp.
                  </p>
</label>
<!-- Option 3 -->
<label class="relative flex flex-col p-3.5 rounded-lg border border-outline-variant bg-white cursor-pointer hover:bg-surface-container transition-all">
<div class="flex items-center justify-between">
<span class="font-title-md text-title-md font-semibold text-on-surface">Hoàn thành thông thường</span>
<input class="text-primary focus:ring-primary w-4 h-4" name="recommendation" type="radio" value="complete"/>
</div>
<p class="text-body-sm text-outline mt-1.5 leading-snug">
                    Xác nhận hoàn thành kỳ thực tập tiêu chuẩn, không duy trì cam kết hợp đồng.
                  </p>
</label>
</div>
</div>
<!-- ATTACHMENT SECTION (Biên bản nghiệm thu thực tập ký kết) -->
<div class="p-4 rounded-xl border border-dashed border-outline-variant bg-surface flex flex-col sm:flex-row items-center justify-between gap-4">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center text-primary">
<span class="material-symbols-outlined" style="font-size: 24px;">attach_file</span>
</div>
<div>
<h4 class="font-title-md text-title-md font-semibold text-on-surface">Biên bản nghiệm thu &amp; Phiếu chấm điểm có chữ ký</h4>
<p class="text-body-sm text-outline">Đính kèm file PDF scan có chữ ký Mentor &amp; Dấu mộc Doanh nghiệp (tối đa 15MB)</p>
</div>
</div>
<div class="flex items-center gap-3">
<span class="text-body-sm text-green-700 bg-green-50 px-2.5 py-1 rounded-md border border-green-200 flex items-center gap-1">
<span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span>
                  Bien_ban_FPT_SE160912.pdf
                </span>
<button class="h-9 px-3 rounded-lg border border-outline-variant bg-white hover:bg-surface-container text-body-sm font-medium transition-colors" type="button">
                  Thay file
                </button>
</div>
</div>
</div>
<!-- FOOTER ACTION BAR -->
<div class="p-6 bg-surface-bright border-t border-outline-variant flex flex-col sm:flex-row items-center justify-between gap-4">
<div class="flex items-center gap-2 text-outline text-body-sm">
<span class="material-symbols-outlined" style="font-size: 18px;">lock</span>
<span>Dữ liệu được mã hóa xác thực bằng khóa ký điện tử Doanh nghiệp</span>
</div>
<div class="flex items-center gap-3 w-full sm:w-auto">
<button class="w-full sm:w-auto px-4 h-10 rounded-lg border border-outline-variant bg-white text-on-surface font-semibold hover:bg-surface-container transition-colors text-label-lg font-label-lg" type="button">
                Hủy bỏ
              </button>
<button class="w-full sm:w-auto px-4 h-10 rounded-lg border border-outline-variant bg-white text-primary font-semibold hover:bg-surface-container transition-colors text-label-lg font-label-lg flex items-center justify-center gap-1.5" type="button">
<span class="material-symbols-outlined" style="font-size: 18px;">save</span>
<span>Lưu nháp đánh giá</span>
</button>
<button class="w-full sm:w-auto px-5 h-10 rounded-lg bg-primary-container text-white font-semibold hover:bg-primary transition-all text-label-lg font-label-lg flex items-center justify-center gap-2 shadow-sm active:scale-95" type="submit">
<span class="material-symbols-outlined" style="font-size: 18px;">send</span>
<span>Xác nhận &amp; Gửi đánh giá cho Nhà trường</span>
</button>
</div>
</div>
</form>
</div>
</div>
</main>
`;
const PAGE_STYLE = String.raw`
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; font-size: 20px; display: inline-block; vertical-align: middle; line-height: 1; }
.custom-scrollbar::-webkit-scrollbar { width: 5px; height: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #f1f5f9; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
/* Bảng màu và typography gốc của Student Connect để giữ giao diện mẫu. */
.bg-background,.bg-surface,.bg-surface-bright { background-color:#faf8ff; }
.bg-surface-container-lowest { background-color:#fff; }
.bg-surface-container-low { background-color:#f2f3ff; }
.bg-surface-container { background-color:#eaedff; }
.bg-surface-container-high { background-color:#e2e7ff; }
.bg-primary { background-color:#00288e; }
.bg-primary-container { background-color:#1e40af; }
.text-primary { color:#00288e; }
.text-secondary { color:#4b41e1; }
.text-on-primary { color:#fff; }
.text-on-surface { color:#131b2e; }
.text-on-surface-variant { color:#444653; }
.text-outline { color:#757684; }
.border-outline-variant { border-color:#c4c5d5; }
.border-primary { border-color:#00288e; }
.text-body-md { font-size:14px; line-height:20px; }
.text-body-sm { font-size:12px; line-height:16px; }
.text-headline-lg { font-size:30px; line-height:38px; }
.text-headline-md { font-size:22px; line-height:30px; }
.text-headline-sm { font-size:18px; line-height:26px; }
.text-display-lg { font-size:36px; line-height:44px; }
.text-title-lg { font-size:16px; line-height:24px; }
.text-title-md { font-size:14px; line-height:20px; }
.text-label-lg { font-size:13px; line-height:18px; }
.text-label-md { font-size:12px; line-height:16px; }
.text-label-xs { font-size:11px; line-height:14px; }
.font-body-md,.font-display-lg,.font-headline-lg,.font-headline-md,.font-headline-sm,.font-label-lg,.font-label-md,.font-label-xs,.font-title-lg,.font-title-md { font-family:Inter,ui-sans-serif,system-ui,sans-serif; }
.hover\:bg-surface-container:hover { background-color:#eaedff; }
.hover\:bg-surface-container-high:hover { background-color:#e2e7ff; }
.hover\:bg-primary:hover { background-color:#00288e; }
.hover\:text-on-surface:hover { color:#131b2e; }
.focus\:border-primary-container:focus { border-color:#1e40af; }
.focus\:ring-primary:focus,.focus\:ring-primary-container:focus { --tw-ring-color:#1e40af; }
.border-outline-variant\/60 { border-color:rgba(196,197,213,.6); }
.bg-primary-fixed\/20 { background-color:rgba(221,225,255,.2); }
.border-primary\/20 { border-color:rgba(0,40,142,.2); }
.divide-outline-variant > :not([hidden]) ~ :not([hidden]) { border-color:#c4c5d5; }
`;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalizeResultId(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  return String(value).trim().replace(/^#/, "");
}

export function InternshipEvaluationPage({
  resultId,
  canEvaluate = false,
  onSubmitEvaluation,
  onSelectResult,
}: InternshipEvaluationPageProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [activeResultId, setActiveResultId] = useState(() => normalizeResultId(resultId));
  const [submitMessage, setSubmitMessage] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setActiveResultId(normalizeResultId(resultId));
  }, [resultId]);

  const hasValidAccess = Boolean(activeResultId) && canEvaluate;

  const pageMarkup = useMemo(() => {
    let markup = PAGE_BODY_HTML;
    const formStart = markup.indexOf("<form");
    const formEndTag = "</form>";
    const formEnd = markup.indexOf(formEndTag, formStart);

    // Form chỉ được render khi có result_id và quyền hợp lệ.
    if (formStart >= 0 && formEnd >= 0) {
      const fullFormEnd = formEnd + formEndTag.length;
      if (!hasValidAccess) {
        const notice = !activeResultId
          ? `<div class="col-span-12 lg:col-span-8 rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-900"><h2 class="font-bold">Chưa thể mở phiếu đánh giá</h2><p class="mt-2 text-sm">Không tìm thấy result_id. Vui lòng chọn một kết quả thực tập hợp lệ.</p></div>`
          : `<div class="col-span-12 lg:col-span-8 rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-900"><h2 class="font-bold">Bạn không có quyền đánh giá kết quả này</h2><p class="mt-2 text-sm">Phiếu đánh giá chỉ được mở khi quyền đánh giá đã được xác minh.</p></div>`;
        markup = markup.slice(0, formStart) + notice + markup.slice(fullFormEnd);
      } else {
        const safeId = escapeHtml(activeResultId);
        const formMarkup = markup.slice(formStart, fullFormEnd).replace(/#RES-2026-FPT-042/g, `#${safeId}`);
        markup = markup.slice(0, formStart) + formMarkup + markup.slice(fullFormEnd);
      }
    }

    return markup;
  }, [activeResultId, hasValidAccess]);

  useEffect(() => {
    // Font Inter và Material Symbols giống thiết kế gốc.
    const fontLinks = [
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
      "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap",
    ];
    const addedLinks: HTMLLinkElement[] = [];
    fontLinks.forEach((href) => {
      if (!document.querySelector(`link[href="${href}"]`)) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = href;
        document.head.appendChild(link);
        addedLinks.push(link);
      }
    });
    return () => addedLinks.forEach((link) => link.remove());
  }, []);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    // Chọn một thực tập sinh trong danh sách sẽ đổi result_id của phiếu.
    const rows = Array.from(root.querySelectorAll<HTMLElement>("[data-result-id]"));
    rows.forEach((row) => {
      row.classList.remove("bg-surface-container-low", "border-l-4", "border-primary");
      if (normalizeResultId(row.dataset.resultId) === activeResultId) {
        row.classList.add("bg-surface-container-low", "border-l-4", "border-primary");
      }
    });

    const selectResult = (row: HTMLElement) => {
      const nextId = normalizeResultId(row.dataset.resultId);
      if (!nextId) return;
      setActiveResultId(nextId);
      setSubmitMessage("");
      setSubmitError("");
      onSelectResult?.(nextId);
    };

    const handleClick = (event: Event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const row = target.closest<HTMLElement>("[data-result-id]");
      if (row) selectResult(row);
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const target = event.target;
      if (target instanceof HTMLElement && target.matches("[data-result-id]")) {
        event.preventDefault();
        selectResult(target);
      }
    };

    // Tự cập nhật xếp loại khi thay đổi điểm tổng kết.
    const scoreInput = root.querySelector<HTMLInputElement>("#finalScoreInput");
    const rankBadge = root.querySelector<HTMLElement>("#rankBadge");
    const handleScoreChange = () => {
      if (!scoreInput || !rankBadge || scoreInput.value === "") return;
      const value = Number(scoreInput.value);
      if (!Number.isFinite(value)) return;
      if (value >= 9) {
        rankBadge.textContent = "Xếp loại: Xuất sắc (Excellent)";
        rankBadge.className = "inline-block mt-1 text-label-md font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded";
      } else if (value >= 8) {
        rankBadge.textContent = "Xếp loại: Giỏi (Very Good)";
        rankBadge.className = "inline-block mt-1 text-label-md font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded";
      } else if (value >= 6.5) {
        rankBadge.textContent = "Xếp loại: Khá (Good)";
        rankBadge.className = "inline-block mt-1 text-label-md font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded";
      } else if (value >= 5) {
        rankBadge.textContent = "Xếp loại: Trung bình (Average)";
        rankBadge.className = "inline-block mt-1 text-label-md font-semibold text-slate-700 bg-slate-200 px-2 py-0.5 rounded";
      } else {
        rankBadge.textContent = "Xếp loại: Không đạt (Fail)";
        rankBadge.className = "inline-block mt-1 text-label-md font-semibold text-red-700 bg-red-100 px-2 py-0.5 rounded";
      }
    };

    const form = root.querySelector<HTMLFormElement>("form");
    const handleSubmit = async (event: Event) => {
      event.preventDefault();
      setSubmitMessage("");
      setSubmitError("");

      // Kiểm tra quyền lại lúc submit; backend vẫn phải xác minh quyền lần cuối.
      if (!activeResultId) {
        setSubmitError("Thiếu result_id nên không thể gửi đánh giá.");
        return;
      }
      if (!canEvaluate) {
        setSubmitError("Bạn không có quyền đánh giá kết quả này.");
        return;
      }

      const scoreElement = root.querySelector<HTMLInputElement>("#finalScoreInput");
      const evaluationElement = root.querySelector<HTMLTextAreaElement>("#evaluationText");
      const score = Number(scoreElement?.value);
      const evaluation = evaluationElement?.value.trim() ?? "";
      const wordCount = evaluation ? evaluation.split(/\s+/).filter(Boolean).length : 0;

      if (!scoreElement || scoreElement.value === "" || !Number.isFinite(score) || score < 0 || score > 10) {
        setSubmitError("Điểm đánh giá phải nằm trong khoảng từ 0 đến 10.");
        scoreElement?.focus();
        return;
      }
      if (!evaluation || wordCount < 50) {
        setSubmitError("Vui lòng nhập nhận xét chi tiết tối thiểu 50 từ.");
        evaluationElement?.focus();
        return;
      }

      setIsSubmitting(true);
      try {
        const payload: InternshipEvaluationPayload = {
          result_id: activeResultId,
          evaluation,
          score,
        };
        if (onSubmitEvaluation) {
          await onSubmitEvaluation(payload);
          setSubmitMessage("Đã gửi đánh giá thành công.");
        } else {
          console.info("Dữ liệu đánh giá (chưa kết nối API):", payload);
          setSubmitMessage("Dữ liệu hợp lệ. Chưa kết nối API nên chưa lưu vào cơ sở dữ liệu.");
        }
      } catch (error) {
        setSubmitError(error instanceof Error ? error.message : "Không thể gửi đánh giá. Vui lòng thử lại.");
      } finally {
        setIsSubmitting(false);
      }
    };

    root.addEventListener("click", handleClick);
    root.addEventListener("keydown", handleKeyDown);
    scoreInput?.addEventListener("input", handleScoreChange);
    form?.addEventListener("submit", handleSubmit);

    return () => {
      root.removeEventListener("click", handleClick);
      root.removeEventListener("keydown", handleKeyDown);
      scoreInput?.removeEventListener("input", handleScoreChange);
      form?.removeEventListener("submit", handleSubmit);
    };
  }, [activeResultId, canEvaluate, onSelectResult, onSubmitEvaluation]);

  return (
    <>
      <style>{PAGE_STYLE}</style>
      <div
        ref={rootRef}
        className="min-h-screen bg-background font-body-md text-body-md text-on-surface antialiased"
        dangerouslySetInnerHTML={{ __html: pageMarkup }}
      />
      {(submitMessage || submitError) && hasValidAccess && (
        <div className="fixed bottom-5 right-5 z-[100] max-w-xl rounded-xl border bg-white px-5 py-4 text-sm shadow-xl">
          <div className={submitError ? "font-semibold text-red-700" : "font-semibold text-emerald-700"}>
            {submitError || submitMessage}
          </div>
        </div>
      )}
      {isSubmitting && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-slate-900/20">
          <div className="rounded-xl bg-white px-6 py-4 text-sm font-semibold shadow-xl">Đang gửi đánh giá...</div>
        </div>
      )}
    </>
  );
}

export default InternshipEvaluationPage;
