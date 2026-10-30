/* eslint-disable @typescript-eslint/no-explicit-any */
const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export const profileApi = {
    async getProfile() {
        const res = await fetch(`${API_BASE}/companies/me`);
        return res.json();
    },
    async updateProfile(data: any) {
        const res = await fetch(`${API_BASE}/companies/me`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.json();
    }
};