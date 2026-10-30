export interface ApplicationItem {
    application_id: string;
    student_name: string;
    mssv: string;
    university: string;
    gpa: number | null; // Null xử lý thành "Không chia sẻ"
    match_score: number;
    status: 'APPLIED' | 'SCREENING' | 'INTERVIEW' | 'OFFER' | 'HIRED' | 'REJECTED';
    cv_download_url: string; // Tải đúng snapshot CV theo phản hồi API
    history: Array<{ time: string; action: string }>;
    notes: string;
}