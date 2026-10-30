export interface JobPosting {
    id: string;
    title: string;
    term: string;
    quota: string;
    status: string;
    status_code: 'DRAFT' | 'PENDING' | 'OPEN' | 'CLOSED';
    applicants_count: number;
    deadline: string;
    skills: string[];
}