// Evidence layers, filters and summaries for the map workspace. Pure functions; no rendering.
import type { MapRecord } from "./api";

export type EvidenceKind = MapRecord["kind"];
export type LayerDef = { key: EvidenceKind; label: string; short: string; color: string; glyph: string; description: string };

export const LAYERS: LayerDef[] = [
  { key: "property", label: "Subject & saved properties", short: "Properties", color: "#1d4ed8", glyph: "P", description: "Properties saved in Mizan, including valuation subjects." },
  { key: "transaction", label: "Achieved sales", short: "Sales", color: "#15803d", glyph: "T", description: "Recorded transaction type, achieved price and transaction date." },
  { key: "listing", label: "Asking listings", short: "Listings", color: "#b45309", glyph: "L", description: "Asking prices. Not achieved sales." },
  { key: "other", label: "Other comparables", short: "Other", color: "#64748b", glyph: "?", description: "Comparables without a confirmed sale or listing classification." },
  { key: "market", label: "Market observations", short: "Market", color: "#7c3aed", glyph: "M", description: "Registered source observations with exact locations; area-level values stay in the list." },
];
export const LAYER = Object.fromEntries(LAYERS.map(l => [l.key, l])) as Record<EvidenceKind, LayerDef>;

/** Layers that need a connected source before they can be shown. Never rendered as data. */
export const UNAVAILABLE_LAYERS = [
  { label: "Rental evidence", reason: "No rental evidence type is recorded yet. Rents will not be mixed with sale prices." },
  { label: "Parcel boundaries", reason: "No authorised cadastral source is connected." },
  { label: "District / municipality boundaries", reason: "No sourced boundary dataset is connected." },
  { label: "Planning & zoning", reason: "No authorised planning source is connected." },
  { label: "Amenities & projects", reason: "No sourced amenities or projects dataset is connected." },
];

export type EvidenceFilters = { statuses: string[]; sources: string[]; precisions: string[]; minReliability: number | null };
export const EMPTY_FILTERS: EvidenceFilters = { statuses: [], sources: [], precisions: [], minReliability: null };

export function sourceLabel(source: string): string {
  try { return /^https?:\/\//i.test(source) ? new URL(source).hostname.replace(/^www\./, "") : source; } catch { return source; }
}
export function applyEvidenceFilters(records: MapRecord[], f: EvidenceFilters): MapRecord[] {
  return records.filter(r => (!f.statuses.length || f.statuses.includes(r.status))
    && (!f.sources.length || f.sources.includes(sourceLabel(r.source)))
    && (!f.precisions.length || f.precisions.includes(r.location_precision || (r.coordinates ? "unspecified" : "missing")))
    && (f.minReliability == null || (r.reliability_score != null && r.reliability_score >= f.minReliability)));
}
export function facetValues(records: MapRecord[]) {
  const count = (values: string[]) => Array.from(values.reduce((m, v) => m.set(v, (m.get(v) || 0) + 1), new Map<string, number>()))
    .sort((a, b) => b[1] - a[1]);
  return { statuses: count(records.map(r => r.status)), sources: count(records.map(r => sourceLabel(r.source))),
    precisions: count(records.map(r => r.location_precision || (r.coordinates ? "unspecified" : "missing"))) };
}

export function quantile(sorted: number[], q: number): number {
  const pos = (sorted.length - 1) * q; const lo = Math.floor(pos); const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}
export const MIN_SUMMARY_SAMPLE = 3;
export type Summary = { key: string; label: string; unit: string; n: number; withValue: number;
  median: number | null; p25: number | null; p75: number | null; min: number | null; max: number | null;
  from: string | null; to: string | null; insufficient: boolean };

function summarize(key: string, label: string, unit: string, rows: { value: number | null; date: string | null }[]): Summary {
  const values = rows.map(r => r.value).filter((v): v is number => v != null && Number.isFinite(v)).sort((a, b) => a - b);
  const dates = rows.map(r => r.date).filter((d): d is string => !!d).sort();
  const enough = values.length >= MIN_SUMMARY_SAMPLE;
  return { key, label, unit, n: rows.length, withValue: values.length, insufficient: !enough,
    median: enough ? quantile(values, 0.5) : null, p25: enough ? quantile(values, 0.25) : null, p75: enough ? quantile(values, 0.75) : null,
    min: values.length ? values[0] : null, max: values.length ? values[values.length - 1] : null,
    from: dates[0] || null, to: dates[dates.length - 1] || null };
}

/** Separate summaries per evidence type and unit. Sales, listings and observations are never pooled. */
export function evidenceSummaries(records: MapRecord[]): Summary[] {
  const out: Summary[] = [];
  for (const kind of ["transaction", "listing"] as const) {
    const byCurrency = new Map<string, MapRecord[]>();
    for (const r of records) if (r.kind === kind) byCurrency.set(r.currency, [...(byCurrency.get(r.currency) || []), r]);
    for (const [currency, rows] of Array.from(byCurrency)) out.push(summarize(`${kind}:${currency}`,
      kind === "transaction" ? "Achieved sale price" : "Asking price", `${currency}/m²`,
      rows.map(r => ({ value: r.price_per_sqm, date: r.date }))));
  }
  const byMetric = new Map<string, MapRecord[]>();
  for (const r of records) if (r.kind === "market" && typeof r.value === "number") {
    const key = `${r.metric}|${r.unit || ""}`; byMetric.set(key, [...(byMetric.get(key) || []), r]);
  }
  for (const [key, rows] of Array.from(byMetric)) out.push(summarize(`market:${key}`, rows[0].title, rows[0].unit || "unit not recorded",
    rows.map(r => ({ value: r.value as number, date: r.date }))));
  return out;
}

/** Record counts per evidence type in trailing windows ending on `today` (YYYY-MM-DD, Riyadh). */
export function activityCounts(records: MapRecord[], today: string, windows = [30, 90, 365]) {
  const end = new Date(`${today}T12:00:00Z`).getTime();
  return windows.map(days => {
    const start = end - days * 86400000;
    const inWindow = records.filter(r => r.date && new Date(`${r.date}T12:00:00Z`).getTime() >= start && new Date(`${r.date}T12:00:00Z`).getTime() <= end);
    return { days, transactions: inWindow.filter(r => r.kind === "transaction").length,
      listings: inWindow.filter(r => r.kind === "listing").length, other: inWindow.filter(r => r.kind !== "transaction" && r.kind !== "listing").length };
  });
}
export function riyadhToday(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Riyadh", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}
