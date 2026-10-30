const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export const applicationsApi = {
    async getApplications(jobId: string, status?: string) {
        const res = await fetch(`${API_BASE}/company/applications?job_id=${jobId}${status ? `&status=${status}` : ''}`);
        return res.json();
    },
    async updateApplicationStatus(appId: string, status: string, note?: string) {
        const res = await fetch(`${API_BASE}/company/applications/${appId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status, note })
        });
        return res.json();
    }
};