/* eslint-disable @typescript-eslint/no-explicit-any */
const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export const evaluationsApi = {
    async evaluateIntern(resultId: string, payload: { score: number; evaluation: string; recommendation: string }) {
        const res = await fetch(`${API_BASE}/internship-terms/results/${resultId}/evaluation`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return res.json();
    }
};