/**
 * Typed API client for the Muqayyim backend.
 * All endpoints from Stage 1.
 */

import type {
  Case, CaseCreate, CaseListResponse,
  Source, SourceAddURL,
  ExtractionJob, StartExtractionResponse,
  Comparable, ComparableListResponse, ComparableStatusUpdate,
  FieldOverrideRequest,
} from "./types";

// Use empty string so all API calls are relative (proxied through Next.js → localhost:8000)
// This lets the browser reach the VM-side API via the single exposed port (3000).
const API_BASE = "";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body);
  }

  // Handle empty responses (204, etc.)
  const text = await res.text();
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}

// ──────────────────────────────────────────────
// Cases
// ──────────────────────────────────────────────

export async function createCase(data: CaseCreate): Promise<Case> {
  return request<Case>("/api/v1/cases", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listCases(): Promise<CaseListResponse> {
  return request<CaseListResponse>("/api/v1/cases");
}

export async function getCase(caseId: string): Promise<Case> {
  return request<Case>(`/api/v1/cases/${caseId}`);
}

// ──────────────────────────────────────────────
// Sources
// ──────────────────────────────────────────────

export async function addUrlSource(caseId: string, data: SourceAddURL): Promise<Source> {
  return request<Source>(`/api/v1/cases/${caseId}/sources/url`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function uploadPdfSource(caseId: string, file: File): Promise<Source> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE}/api/v1/cases/${caseId}/sources/pdf`;
  const res = await fetch(url, { method: "POST", body: formData });

  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}

export async function listSources(caseId: string): Promise<Source[]> {
  return request<Source[]>(`/api/v1/cases/${caseId}/sources`);
}

// ──────────────────────────────────────────────
// Extractions
// ──────────────────────────────────────────────

export async function startExtraction(sourceId: string): Promise<StartExtractionResponse> {
  return request<StartExtractionResponse>(`/api/v1/sources/${sourceId}/extract`, {
    method: "POST",
  });
}

export async function getExtractionJob(jobId: string): Promise<ExtractionJob> {
  return request<ExtractionJob>(`/api/v1/extraction-jobs/${jobId}`);
}

// ──────────────────────────────────────────────
// Comparables
// ──────────────────────────────────────────────

export async function listComparables(caseId: string): Promise<ComparableListResponse> {
  return request<ComparableListResponse>(`/api/v1/cases/${caseId}/comparables`);
}

export async function overrideField(
  compId: string,
  fieldId: string,
  data: FieldOverrideRequest
): Promise<{ status: string; message: string }> {
  return request(`/api/v1/comparables/${compId}/fields/${fieldId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function updateComparableStatus(
  compId: string,
  data: ComparableStatusUpdate
): Promise<{ status: string; new_status: string }> {
  return request(`/api/v1/comparables/${compId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ──────────────────────────────────────────────
// Exports
// ──────────────────────────────────────────────

export function getExportUrl(caseId: string, format: "csv" | "xlsx" | "pdf"): string {
  return `${API_BASE}/api/v1/cases/${caseId}/export/${format}`;
}

export async function downloadExport(caseId: string, format: "csv" | "xlsx" | "pdf"): Promise<void> {
  const url = getExportUrl(caseId, format);
  const link = document.createElement("a");
  link.href = url;
  link.download = `comps_export.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Mizan foundation: durable property workspaces and source-backed market evidence.
export type PropertyInput = {
  name: string; case_id: string | null; country: string; currency: string;
  locale: "en-SA" | "ar-SA"; property_type: string | null;
  analysis?: { method: string | null; as_of: string | null; radius_km: number; lookback_days: number };
  location: Record<string, unknown>; land: Record<string, unknown>;
  planning: Record<string, unknown>; building: Record<string, unknown>;
  financial: Record<string, unknown>; provenance: Record<string, unknown>;
};
export type Assumption = {
  name: string; value: number | string | boolean; unit: string; category: string;
  source: string; as_of: string; status: string; user_override: number | string | boolean | null;
  notes: string | null; effective_value?: number | string | boolean;
};
export type PropertyWorkspace = {
  id: string; revision: number; property: PropertyInput;
  assumptions: Record<string, Assumption>; created_at: string; updated_at: string;
};
export type PropertySummary = { id: string; name: string; city: string | null; district: string | null;
  property_type: string | null; revision: number; case_id: string | null; updated_at: string };
export const listProperties = (q = "", offset = 0) => request<{ data: PropertySummary[]; total: number }>(`/api/v1/properties?q=${encodeURIComponent(q)}&offset=${offset}`);
export const createProperty = (property: PropertyInput) => request<PropertyWorkspace>("/api/v1/properties", { method: "POST", body: JSON.stringify(property) });
export const getProperty = (id: string) => request<PropertyWorkspace>(`/api/v1/properties/${id}`);
export const saveProperty = (id: string, property: PropertyInput, expected_revision: number, reason: string) => request<PropertyWorkspace>(`/api/v1/properties/${id}`, { method: "PUT", body: JSON.stringify({ property, expected_revision, reason }) });
export const saveAssumption = (id: string, key: string, assumption: Assumption, expected_revision: number, reason: string) => request<PropertyWorkspace>(`/api/v1/properties/${id}/assumptions/${key}`, { method: "PUT", body: JSON.stringify({ assumption, expected_revision, reason }) });
export type Revision = { revision: number; reason: string; created_at: string };
export const listRevisions = (id: string) => request<Revision[]>(`/api/v1/properties/${id}/revisions`);
export const getRevision = (id: string, revision: number) => request<{ snapshot: { property: PropertyInput; assumptions: Record<string, Assumption> }; reason: string }>(`/api/v1/properties/${id}/revisions/${revision}`);
export type MarketSource = { id: string; name: string; provider: string; source_type: string; uri: string | null; notes: string | null };
export type Observation = { id: string; source: string; observed_on: string; city: string; district: string | null; property_type: string;
  metric: string; unit: string; raw_value: unknown; normalized_value: unknown; reliability: number; metadata: Record<string, unknown> };
export const listMarketSources = () => request<MarketSource[]>("/api/v1/market/sources");
export const createMarketSource = (source: Omit<MarketSource, "id">) => request<MarketSource>("/api/v1/market/sources", { method: "POST", body: JSON.stringify(source) });
export const listObservations = (city = "", offset = 0) => request<{ data: Observation[]; total: number }>(`/api/v1/market/observations?city=${encodeURIComponent(city)}&offset=${offset}`);
export async function importMarketCsv(sourceId: string, file: File) {
  const data = new FormData(); data.append("file", file);
  const res = await fetch(`/api/v1/market/sources/${sourceId}/csv`, { method: "POST", body: data });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json() as Promise<{ inserted: number; duplicates: number }>;
}
export type LocalDataset = { name: string; path: string; bytes: number; status: string };
export const listLocalDatasets = () => request<LocalDataset[]>("/api/v1/market/local-datasets");

export type MapRecord = {
  id: string; entity_id: string; kind: "property" | "transaction" | "listing" | "other" | "market";
  title: string; city: string | null; district: string | null; property_type: string | null;
  coordinates: [number, number] | null; date: string | null; date_basis: string;
  evidence_type: string | null; status: string; price: number | null; currency: string;
  area_sqm: number | null; price_per_sqm: number | null; source: string;
  reliability_score: number | null; case_id: string | null; href: string;
  metric?: string; value?: unknown; unit?: string; reliability_percent?: number;
  /** source_reported | user_selected | rooftop | approximate | area | missing | … — never upgraded by the UI. */
  location_precision?: string; coordinate_source?: string | null; has_site_outline?: boolean;
};
export type MapResponse = { data: MapRecord[]; total: number; truncated: boolean;
  returned?: number; matching_filters?: number; bbox?: { south: number; west: number; north: number; east: number } | null;
  /** Records use [latitude, longitude]; GeoJSON geometry uses [longitude, latitude]. */
  coordinate_order?: string;
  coverage?: { properties: number; comparables: number; market_observations: number; missing_location: number; unverified_datasets: number; datasets: LocalDataset[] };
  available: { cities: string[]; property_types: string[] };
  counts: { mapped: number; missing_location: number; transactions: number; listings: number; properties: number };
  scope: string };
export const getMapRecords = (filters: Record<string, string>, init?: { signal?: AbortSignal }) => request<MapResponse>(`/api/v1/map/records?${new URLSearchParams(Object.entries(filters).filter(([, value]) => !!value))}`, init);

export type ValuationField = { key: string; label: string; unit: string; minimum: number; maximum: number | null; positive: boolean;
  value: number | null; source: string | null; as_of: string | null; origin: string | null; assumption_status?: string; state: string; error: string | null };
export type ValuationMethod = { key: string; label: string; implemented: boolean; description: string; fields: ValuationField[] };
export type Candidate = MapRecord & { distance_km: number; eligible: boolean; exclusion_reasons: string[] };
export type PreparedAnalysis = { property_id: string; property_name: string; revision: number; property_type: string; calculation_version: string;
  coordinates: [number, number] | null; method: string; method_label: string; description: string; as_of: string;
  radius_km: number; lookback_days: number; fields: ValuationField[]; candidates: Candidate[]; eligible_comparables: Candidate[]; gaps: string[]; ready: boolean };
export type AnalysisResult = { inputs?: ValuationField[]; comparables?: Candidate[]; property?: PropertyInput; id: string; property_revision: number; data_date: string; method: string; created_at: string;
  outputs: { value: number; currency: string; confidence: number | null; calculation_version: string; evidence: Record<string, unknown>; limitations: string[]; sensitivity?: { x: { label: string; unit: string; values: number[] }; y: { label: string; unit: string; values: number[] }; cells: { value: number | null; reason: string | null }[][]; notice: string } | null } };
export type AnalysisInput = { value: number; source: string; as_of: string; notes?: string; status?: string };
export const getValuationCatalog = () => request<{ methods: ValuationMethod[]; property_types: string[] }>("/api/v1/analysis/catalog");
export const startMapAnalysis = (body: { latitude: number; longitude: number; property_type: string; method: string; name?: string; city?: string; district?: string;
  coordinate_source?: "map_pin" | "coordinate_entry" | "geocoded" | "imported" | "manual"; coordinate_precision?: "user_selected" | "rooftop" | "range_interpolated" | "geometric_center" | "approximate" }) => request<PreparedAnalysis>("/api/v1/analysis/start", { method: "POST", body: JSON.stringify(body) });
export const prepareAnalysis = (id: string, method?: string) => request<PreparedAnalysis>(`/api/v1/analysis/${id}${method ? `?method=${encodeURIComponent(method)}` : ""}`);
export const saveAnalysisInputs = (id: string, body: { expected_revision: number; method: string; inputs: Record<string, AnalysisInput>; as_of: string; radius_km: number; lookback_days: number }) => request<PreparedAnalysis>(`/api/v1/analysis/${id}/inputs`, { method: "PUT", body: JSON.stringify(body) });
export const calculateAnalysis = (id: string, expected_revision: number) => request<AnalysisResult>(`/api/v1/analysis/${id}/runs`, { method: "POST", body: JSON.stringify({ expected_revision }) });
export const getAnalysisRuns = (id: string) => request<{ id: string; created_at: string; data: AnalysisResult }[]>(`/api/v1/analysis/${id}/runs`);
