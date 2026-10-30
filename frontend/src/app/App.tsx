import React, { useState } from 'react';
import { JobPostingsPage } from '../features/company-jobs/components/JobPostingsPage';
import { CompanyProfilePage } from '../features/company-profile/components/CompanyProfilePage';
import { InvitedApplicationsPage } from '../features/company-invitations/components/InvitedApplicationsPage';
import { InternshipEvaluationPage } from '../features/company-evaluations/components/InternshipEvaluationPage';
import { KanbanApplicationsPage } from '../features/company-applications/components/KanbanApplicationsPage';

type TestView = 'jobs' | 'profile' | 'invitations' | 'evaluation' | 'applications';

export function App() {
  // Thanh chuyển trang dùng để kiểm thử nhanh các component.
  const [currentView, setCurrentView] = useState<TestView>('evaluation');

  // DỮ LIỆU TEST:
  // Đổi thành null để kiểm tra trạng thái thiếu result_id.
  // Đổi canEvaluate thành false để kiểm tra chặn quyền.
  // Trong dự án thật, lấy result_id từ route/API và quyền từ backend.
  const testResultId: string | null = 'RESULT-1001';
  const testCanEvaluate = true;

  const testButtonClass = (view: TestView) =>
    `whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
      currentView === view
        ? 'bg-[#00288e] text-white shadow-sm'
        : 'text-[#444653] hover:bg-[#eaedff]'
    }`;

  return (
    <div className="min-h-screen bg-[#faf8ff] font-sans antialiased text-[#131b2e]">
      {/* Thanh chuyển trang test nhanh */}
      <div className="fixed right-3 top-3 z-[10000] flex max-w-[calc(100vw-24px)] items-center gap-1 overflow-x-auto rounded-xl border border-[#c4c5d5]/80 bg-white/95 p-1.5 shadow-lg backdrop-blur-md sm:right-6">
        <span className="hidden pl-2 text-[11px] font-bold uppercase tracking-wider text-[#757684] md:inline">
          Test View:
        </span>
        <button type="button" onClick={() => setCurrentView('jobs')} className={testButtonClass('jobs')}>
          Tin tuyển dụng
        </button>
        <button type="button" onClick={() => setCurrentView('profile')} className={testButtonClass('profile')}>
          Hồ sơ công ty
        </button>
        <button type="button" onClick={() => setCurrentView('invitations')} className={testButtonClass('invitations')}>
          Lời mời đã gửi
        </button>
        <button type="button" onClick={() => setCurrentView('applications')} className={testButtonClass('applications')}>
          Quản lý ứng viên
        </button>
        <button type="button" onClick={() => setCurrentView('evaluation')} className={testButtonClass('evaluation')}>
          Đánh giá thực tập
        </button>
      </div>

      <div className="pt-16">
        {currentView === 'jobs' && <JobPostingsPage />}
        {currentView === 'profile' && <CompanyProfilePage />}
        {currentView === 'invitations' && <InvitedApplicationsPage />}
        {currentView === 'applications' && (
          <KanbanApplicationsPage 
            currentRoute="QLUV" 
            onRouteChange={(route) => {
              if (route === 'QLUV') setCurrentView('applications');
            }} 
          />
        )}
        {currentView === 'evaluation' && (
          <InternshipEvaluationPage
            resultId={testResultId}
            canEvaluate={testCanEvaluate}
            onSubmitEvaluation={async (payload) => {
              // DEMO: hiện payload trong console.
              // Khi tích hợp backend, thay đoạn này bằng API POST thật.
              console.log('Internship evaluation payload:', payload);
            }}
          />
        )}
      </div>
    </div>
  );
}

export default App;