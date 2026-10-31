// Mizan Monitor client: types, API calls and pure display helpers. Calculations stay on the server.
import { request } from "./api.ts";

export type Origin = "real" | "demo" | "user_provided" | "derived" | "detected" | "user" | null | undefined;
export type Grade = "high" | "medium" | "low";
export type Severity = "info" | "watch" | "warning" | "critical";
export type Rollup = { key: string; label: string; value: number; share_pct: number };
export type Priority = { score: number; band: "high" | "medium" | "low"; reasons: { points: number; reason: string }[] };
export type Alert = { id: string; asset_id: string | null; asset_name?: string | null; kind: string; severity: Severity; status: "open" | "investigating" | "accepted" | "resolved"; title: string; message: string; raised_on: string; note: string | null };
export type AssetRow = { id: string; property_id: string; name: string; city: string | null; district: string | null; property_type: string | null; ownership_pct: number; debt_sar: number | null; is_demo: boolean;
  value: number | null; low: number | null; high: number | null; valued_on: string | null; origin: Origin; official_value: number | null; official_on: string | null; change_vs_official_pct: number | null; change_pct: number | null;
  confidence: Grade | null; divergence_pct: number | null; ltv_pct: number | null; occupancy_pct: number | null; cap_rate_pct: number | null; noi: number | null; official_age_months: number | null; priority: Priority; next_formal_on: string | null; formal_requested_at: string | null; top_alert?: Alert };
export type Totals = { asset_count: number; value: number; official: number; like_official: number; compared_count: number; change: number | null; change_pct: number | null; cost: number; cost_count: number; book: number; book_count: number; unrealised: number | null;
  debt: number; debt_count: number; noi: number; noi_count: number; cap_rate_pct: number | null; occupancy_pct: number | null; occupancy_count: number; ltv_pct: number | null; nav: number | null; official_nav: number | null;
  indicative_count: number; official_only_count: number; unvalued_count: number; up: number; stable: number; down: number; not_comparable: number; move_count: number; confidence_share: Partial<Record<Grade, number>>; by_city: Rollup[]; by_type: Rollup[]; origin: Origin };
export type HistoryPoint = { date: string; indicative: number | null; official: number | null; assets: number };
export type Dashboard = { id: string; name: string; owner_entity: string | null; fund: string | null; asset_manager: string | null; is_demo: boolean; official_nav_sar: number | null; settings: Record<string, number>; last_checked_at: string | null;
  totals: Totals; attention: AssetRow[]; attention_count: number; alerts: Alert[]; alert_counts: Record<Severity, number>; priority: AssetRow[]; history: HistoryPoint[]; as_of: string };
export type Driver = { key: string; label: string; amount: number; pct: number | null };
export type Attribution = { total: number; drivers: Driver[]; exact: boolean; basis: string; note: string; from_date?: string; model_value_at_official?: number; official_value?: number; official_on?: string; gap_at_official?: number };
export type GradeDetail = { level: Grade; checks: { key: string; label: string; state: "good" | "fair" | "poor"; detail: string }[]; passed: number; total: number; basis: string };
export type InputMeta = { key: string; label: string; unit: string; value: number; source: string | null; as_of: string | null; status: string | null; override: boolean };
export type SnapshotRow = { id: string; kind: "official" | "indicative"; valued_on: string; value: number; low: number | null; high: number | null; confidence: Grade | null; trigger: string; origin: Origin; created_at: string };
export type AssetDetail = AssetRow & { portfolio: { id: string; name: string; is_demo: boolean }; summary: Record<string, any>; facts: Record<string, number | null>; acquisition_cost_sar: number | null; book_value_sar: number | null; acquisition_date: string | null;
  monitoring_frequency: string; formal_frequency: string; last_checked_at: string | null; method_weights: Record<string, number> | null; history: SnapshotRow[];
  methods: { key: string; label: string; value: number; weight?: number; limitations: string[]; inputs: InputMeta[] }[]; reconciliation: { basis: string; weights: Record<string, number> } | null; confidence_detail: GradeDetail | null;
  divergence: { spread_pct: number; low_method: string; high_method: string } | null; attribution: Attribution | null; attribution_since_official: Attribution | null; changes: { type: string; text: string }[]; gaps: string[];
  evidence: { id: string; title: string; date: string; price_per_sqm: number; area_sqm: number; distance_km: number | null; is_new: boolean; vs_implied_pct: number | null; origin: Origin }[]; alerts: Alert[];
  events: { id: string; type: string; category: string; occurred_on: string; summary: string; origin: Origin }[] };
export type AuditEntry = { at: string; on: string; kind: "valuation" | "official" | "event" | "action"; text: string; before?: number | null; after?: number; trigger?: string; model?: string; calculation_version?: string; origin?: Origin; details?: any; user_id?: string | null; snapshot_id?: string };
export type StressResult = { base_value: number; base_ltv_pct: number | null; asset_count: number; notice: string; scenarios: { key: string; label: string; value: number; change: number; change_pct: number | null; ltv_pct: number | null; affected: number; unaffected: number; worst: { id: string; name: string; before: number; after: number; change_pct: number; ltv_after: number | null }[] }[] };

const base = "/api/v1/monitor";
const json = (method: string, body?: unknown): RequestInit => ({ method, body: body === undefined ? undefined : JSON.stringify(body) });
export const listPortfolios = () => request<{ id: string; name: string; is_demo: boolean; asset_count: number; value: number; change_pct: number | null }[]>(`${base}/portfolios`);
export const createPortfolio = (body: { name: string; owner_entity?: string; fund?: string; asset_manager?: string }) => request<{ id: string }>(`${base}/portfolios`, json("POST", body));
export const createDemoPortfolio = () => request<{ id: string }>(`${base}/demo`, json("POST"));
export const removeDemoPortfolio = () => request<{ portfolios: number; properties: number }>(`${base}/demo`, json("DELETE"));
export const getDashboard = (id: string) => request<Dashboard>(`${base}/portfolios/${id}`);
export const patchPortfolio = (id: string, body: Record<string, unknown>) => request(`${base}/portfolios/${id}`, json("PATCH", body));
export const deletePortfolio = (id: string) => request(`${base}/portfolios/${id}`, json("DELETE"));
export const addAssets = (id: string, property_ids: string[]) => request<{ added: number }>(`${base}/portfolios/${id}/assets`, json("POST", { property_ids }));
export const listAssets = (id: string, params: Record<string, string>) => request<{ data: AssetRow[]; total: number; facets: { cities: string[]; types: string[] } }>(`${base}/portfolios/${id}/assets?${new URLSearchParams(Object.entries(params).filter(([, v]) => !!v))}`);
export const checkPortfolio = (id: string, onlyDue = false) => request<{ checked: number; updated: number; unchanged: number; skipped: number }>(`${base}/portfolios/${id}/check${onlyDue ? "?only_due=true" : ""}`, json("POST"));
export const getStress = (id: string) => request<StressResult>(`${base}/portfolios/${id}/stress`);
export const getAsset = (id: string) => request<AssetDetail>(`${base}/assets/${id}`);
export const patchAsset = (id: string, body: Record<string, unknown>) => request<AssetDetail>(`${base}/assets/${id}`, json("PATCH", body));
export const removeAsset = (id: string) => request(`${base}/assets/${id}`, json("DELETE"));
export const addOfficial = (id: string, body: { value_sar: number; valued_on: string; valuer: string; note?: string }) => request<AssetDetail>(`${base}/assets/${id}/official`, json("POST", body));
export const overrideInput = (id: string, body: { field: string; value: number | null; reason: string }) => request<AssetDetail>(`${base}/assets/${id}/override`, json("POST", body));
export const recordEvent = (id: string, body: { event_type: string; occurred_on: string; summary: string }) => request(`${base}/assets/${id}/events`, json("POST", body));
export const requestFormal = (id: string, reason: string) => request<AssetDetail>(`${base}/assets/${id}/formal-request`, json("POST", { reason }));
export const revalueAsset = (id: string) => request<{ changed: boolean; asset: AssetDetail }>(`${base}/assets/${id}/revalue`, json("POST"));
export const getAudit = (id: string) => request<{ entries: AuditEntry[] }>(`${base}/assets/${id}/audit`);
export const setAlertStatus = (id: string, status: Alert["status"], note?: string) => request<Alert>(`${base}/alerts/${id}`, json("PATCH", { status, note }));
export const getCatalog = () => request<{ event_types: Record<string, string>; frequencies: string[] }>(`${base}/catalog`);

/** Compact money: SAR 9.38bn, SAR 53.2m, SAR 840k. Missing stays visibly missing, never zero. */
export function sar(value: number | null | undefined, signed = false): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const a = Math.abs(value); const sign = value < 0 ? "−" : signed && value > 0 ? "+" : "";
  const body = a >= 1e9 ? `${(a / 1e9).toFixed(2)}bn` : a >= 1e6 ? `${(a / 1e6).toFixed(a >= 1e8 ? 0 : 1)}m` : a >= 1e3 ? `${Math.round(a / 1e3)}k` : a.toFixed(0);
  return `${sign}SAR ${body}`;
}
export function pct(value: number | null | undefined, digits = 1, signed = true): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const sign = value < 0 ? "−" : signed && value > 0 ? "+" : "";
  return `${sign}${Math.abs(value).toFixed(digits)}%`;
}
export const titleCase = (s: string | null | undefined) => (s ?? "").replaceAll("_", " ").replace(/^./, c => c.toUpperCase());
const TRIGGERS: Record<string, string> = { baseline: "First valuation", new_comparable: "New comparable sale", comparable_dropped: "Comparable aged out", rent_change: "Rent changed", occupancy_change: "Occupancy changed",
  operating_cost_change: "Operating costs changed", cap_rate_movement: "Cap rate moved", discount_rate_movement: "Discount rate moved", construction_cost_movement: "Construction cost moved", user_override: "Assumption overridden",
  weights_changed: "Method weights changed", official_valuation: "Official valuation", method_added: "Method became available", method_removed: "Method lost its evidence", input_change: "Input changed" };
export const triggerLabel = (t: string | null | undefined) => (t && TRIGGERS[t]) || titleCase(t);
export const ageLabel = (day: string | null | undefined, today: string) => {
  if (!day) return "Unknown";
  const d = Math.round((Date.parse(today) - Date.parse(day)) / 86400000);
  if (Number.isNaN(d)) return "Unknown";
  if (d <= 0) return "Today"; if (d === 1) return "Yesterday"; if (d < 60) return `${d} days ago`; if (d < 730) return `${Math.round(d / 30.4)} months ago`; return `${(d / 365).toFixed(1)} years ago`;
};
export const RANGES = [{ value: "1m", label: "1M", months: 1 }, { value: "3m", label: "3M", months: 3 }, { value: "6m", label: "6M", months: 6 }, { value: "1y", label: "1Y", months: 12 }, { value: "3y", label: "3Y", months: 36 }, { value: "all", label: "All", months: null }] as const;
export type RangeKey = (typeof RANGES)[number]["value"];
/** Keep points inside the window ending at `today`. ISO dates compare correctly as text. */
export function inRange<T extends { date: string }>(points: T[], range: RangeKey, today: string): T[] {
  const months = RANGES.find(r => r.value === range)?.months;
  if (!months) return points;
  const d = new Date(`${today}T00:00:00Z`); d.setUTCMonth(d.getUTCMonth() - months);
  const start = d.toISOString().slice(0, 10);
  return points.filter(p => p.date >= start);
}
export function assetsCsv(rows: AssetRow[]): string {
  const quote = (v: unknown) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const header = ["Asset", "City", "Type", "Ownership %", "Indicative value SAR", "Low SAR", "High SAR", "Official value SAR", "Official date", "Change vs official %", "Confidence", "Method spread %", "LTV %", "Priority", "Data origin"];
  const body = rows.map(r => [r.name, r.city, r.property_type, r.ownership_pct, r.value, r.low, r.high, r.official_value, r.official_on, r.change_vs_official_pct?.toFixed(2), r.confidence, r.divergence_pct?.toFixed(1), r.ltv_pct?.toFixed(1), r.priority.band, r.origin].map(quote).join(","));
  return [header.map(quote).join(","), ...body].join("\n");
}
export const errorText = (e: unknown) => { const raw = (e as Error)?.message ?? "Something went wrong"; try { const d = JSON.parse(raw).detail; return typeof d === "string" ? d : Array.isArray(d) ? d.map((x: { msg: string }) => x.msg).join("; ") : d?.message ?? raw; } catch { return raw; } };
