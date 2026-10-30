/* eslint-disable @typescript-eslint/no-explicit-any */
const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export const jobsApi = {
    async getJobs(params?: { term?: string; status?: string }) {
        const query = new URLSearchParams(params as any).toString();
        const res = await fetch(`${API_BASE}/jobs/me?${query}`);
        return res.json();
    },
    async createJob(jobData: any) {
        const res = await fetch(`${API_BASE}/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        return res.json();
    },
    async updateJob(id: string, jobData: any) {
        const res = await fetch(`${API_BASE}/jobs/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        return res.json();
    },
    async submitJob(id: string) {
        const res = await fetch(`${API_BASE}/jobs/${id}/submit`, { method: 'POST' });
        return res.json();
    },
    async closeJob(id: string) {
        const res = await fetch(`${API_BASE}/jobs/${id}/close`, { method: 'POST' });
        return res.json();
    },
    async getJobStats(id: string) {
        const res = await fetch(`${API_BASE}/jobs/${id}/stats`);
        return res.json();
    }
};