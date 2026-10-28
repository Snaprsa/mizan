/**
 * API client for Qaim backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchAPI(path: string, options?: RequestInit) {
    const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });
    if (!res.ok) {
        const error = await res.text();
        throw new Error(`API Error ${res.status}: ${error}`);
    }
    return res.json();
}

// Cases
export async function createCase(data: { title: string; description?: string; city?: string }) {
    return fetchAPI('/cases', { method: 'POST', body: JSON.stringify(data) });
}

export async function listCases() {
    return fetchAPI('/cases');
}

export async function getCase(caseId: string) {
    return fetchAPI(`/cases/${caseId}`);
}

// Sources
export async function addUrlSource(caseId: string, url: string) {
    return fetchAPI(`/cases/${caseId}/sources/url`, {
        method: 'POST',
        body: JSON.stringify({ url }),
    });
}

export async function uploadPdfSource(caseId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/cases/${caseId}/sources/pdf`, {
        method: 'POST',
        body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
}

export async function listSources(caseId: string) {
    return fetchAPI(`/cases/${caseId}/sources`);
}

// Extraction
export async function startExtraction(caseId: string, sourceId: string) {
    return fetchAPI(`/cases/${caseId}/sources/${sourceId}/extract`, { method: 'POST' });
}

export async function listJobs(caseId: string) {
    return fetchAPI(`/cases/${caseId}/jobs`);
}

export async function getJob(jobId: string) {
    return fetchAPI(`/jobs/${jobId}`);
}

// Comparables
export async function getComps(caseId: string) {
    return fetchAPI(`/cases/${caseId}/comps`);
}

export async function getComp(compId: string) {
    return fetchAPI(`/comps/${compId}`);
}

export async function updateCompStatus(compId: string, data: { is_invalid?: boolean; is_outlier?: boolean }) {
    return fetchAPI(`/comps/${compId}/status`, { method: 'PATCH', body: JSON.stringify(data) });
}

// Overrides
export async function overrideField(compId: string, data: { field_name: string; new_value: string; reason: string }) {
    return fetchAPI(`/comps/${compId}/override`, { method: 'POST', body: JSON.stringify(data) });
}

// Export
export function getExportCSVUrl(caseId: string) {
    return `${API_BASE}/cases/${caseId}/export/csv`;
}

export function getExportXLSXUrl(caseId: string) {
    return `${API_BASE}/cases/${caseId}/export/xlsx`;
}
