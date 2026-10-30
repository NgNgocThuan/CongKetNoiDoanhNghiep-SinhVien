const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export const invitationsApi = {
    async sendInvitation(payload: { job_id: string; student_id: string; message: string }) {
        const res = await fetch(`${API_BASE}/invitations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return res.json();
    },
    async getSentInvitations() {
        const res = await fetch(`${API_BASE}/invitations/company`);
        return res.json();
    }
};