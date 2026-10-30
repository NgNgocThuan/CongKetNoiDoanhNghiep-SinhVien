export interface CompanyProfile {
    name: string;
    tax_id: string;
    verified: boolean;
    industry: string[];
    scale: string;
    address: string;
    website: string;
    email: string;
    documents: Array<{ id: number; name: string; size: string; status: string }>;
    mou_schools: string[];
}