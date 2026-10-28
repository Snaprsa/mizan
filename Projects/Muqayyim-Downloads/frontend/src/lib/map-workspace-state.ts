// Persisted map workspace state. Everything is validated on load; unknown or malformed values are dropped.
import { isLatLng, type LatLng, type SearchArea } from "./geo.ts";

export type Basemap = "satellite" | "hybrid" | "roadmap" | "terrain";
export const BASEMAPS: { key: Basemap; label: string }[] = [
  { key: "satellite", label: "Satellite" }, { key: "hybrid", label: "Hybrid" },
  { key: "roadmap", label: "Road" }, { key: "terrain", label: "Terrain" },
];
export type Camera = { center: LatLng; zoom: number; heading: number; tilt: number };
export type CoordinateSource = "map_pin" | "coordinate_entry" | "geocoded" | "imported" | "manual";
export type CoordinatePrecision = "user_selected" | "rooftop" | "range_interpolated" | "geometric_center" | "approximate";
export type Subject = { coordinates: LatLng; source: CoordinateSource; precision: CoordinatePrecision; confirmed: boolean; label?: string };
export type InspectorTab = "evidence" | "subject" | "valuation" | "coverage";

export type WorkspaceState = {
  version: 1;
  basemap: Basemap;
  camera: Camera | null;
  subject: Subject | null;
  searchArea: SearchArea | null;
  /** Restrict the evidence list to the search area (map filter only; not a valuation input). */
  filterToArea: boolean;
  siteOutline: LatLng[] | null;
  selectedId: string | null;
  layers: Record<string, boolean>;
  filters: { q: string; city: string; type: string; from: string; to: string;
    statuses: string[]; sources: string[]; precisions: string[]; minReliability: number | null; withinView: boolean };
  subjectType: string;
  approach: string;
  panels: { left: boolean; right: boolean; rightWidth: number; table: boolean; tab: InspectorTab };
};

export const STORAGE_KEY = "mizan.mapWorkspace.v1";
export const DEFAULT_CENTER: LatLng = [24.7136, 46.6753]; // Riyadh; navigation default only, not evidence.

export function defaultState(): WorkspaceState {
  return { version: 1, basemap: "hybrid", camera: null, subject: null, searchArea: null, filterToArea: false, siteOutline: null,
    selectedId: null, layers: { property: true, transaction: true, listing: true, other: true, market: true },
    filters: { q: "", city: "", type: "", from: "", to: "", statuses: [], sources: [], precisions: [], minReliability: null, withinView: false },
    subjectType: "", approach: "sales_comparison",
    panels: { left: true, right: true, rightWidth: 400, table: false, tab: "evidence" } };
}

const str = (v: unknown, max = 300) => typeof v === "string" && v.length <= max ? v : null;
const strs = (v: unknown) => Array.isArray(v) ? v.filter((x): x is string => typeof x === "string" && x.length <= 300).slice(0, 50) : [];
const num = (v: unknown, lo: number, hi: number) => typeof v === "number" && Number.isFinite(v) && v >= lo && v <= hi ? v : null;
const isDate = (v: unknown) => typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v);
const oneOf = <T extends string>(v: unknown, options: readonly T[]) => (options as readonly unknown[]).includes(v) ? v as T : null;

export function sanitizeArea(v: unknown): SearchArea | null {
  const a = v as Record<string, unknown> | null;
  if (!a || typeof a !== "object") return null;
  if (a.kind === "radius" && isLatLng(a.center) && num(a.radius_m, 10, 50000) != null) return { kind: "radius", center: a.center, radius_m: a.radius_m as number };
  if (a.kind === "polygon" && Array.isArray(a.ring) && a.ring.length >= 3 && a.ring.length <= 500 && a.ring.every(isLatLng)) return { kind: "polygon", ring: a.ring as LatLng[] };
  return null;
}

export function sanitizeState(raw: unknown): WorkspaceState {
  const d = defaultState(); const s = raw as Record<string, any> | null;
  if (!s || typeof s !== "object" || s.version !== 1) return d;
  const cam = s.camera;
  const camera: Camera | null = cam && isLatLng(cam.center) && num(cam.zoom, 1, 22) != null
    ? { center: cam.center, zoom: cam.zoom, heading: num(cam.heading, 0, 360) ?? 0, tilt: num(cam.tilt, 0, 90) ?? 0 } : null;
  const sub = s.subject;
  const subject: Subject | null = sub && isLatLng(sub.coordinates) ? { coordinates: sub.coordinates,
    source: oneOf(sub.source, ["map_pin", "coordinate_entry", "geocoded", "imported", "manual"] as const) ?? "map_pin",
    precision: oneOf(sub.precision, ["user_selected", "rooftop", "range_interpolated", "geometric_center", "approximate"] as const) ?? "approximate",
    confirmed: sub.confirmed === true, ...(str(sub.label) ? { label: sub.label } : {}) } : null;
  const f = s.filters || {}; const p = s.panels || {};
  return {
    version: 1,
    basemap: oneOf(s.basemap, ["satellite", "hybrid", "roadmap", "terrain"] as const) ?? d.basemap,
    camera, subject, searchArea: sanitizeArea(s.searchArea), filterToArea: s.filterToArea === true,
    siteOutline: Array.isArray(s.siteOutline) && s.siteOutline.length >= 3 && s.siteOutline.every(isLatLng) ? s.siteOutline : null,
    selectedId: str(s.selectedId),
    layers: Object.fromEntries(Object.keys(d.layers).map(k => [k, typeof s.layers?.[k] === "boolean" ? s.layers[k] : true])),
    filters: { q: str(f.q) ?? "", city: str(f.city) ?? "", type: str(f.type) ?? "", from: isDate(f.from) ? f.from : "", to: isDate(f.to) ? f.to : "",
      statuses: strs(f.statuses), sources: strs(f.sources), precisions: strs(f.precisions), minReliability: num(f.minReliability, 0, 5), withinView: f.withinView === true },
    subjectType: str(s.subjectType, 100) ?? "", approach: str(s.approach, 100) || d.approach,
    panels: { left: p.left !== false, right: p.right !== false, rightWidth: num(p.rightWidth, 300, 900) ?? d.panels.rightWidth,
      table: p.table === true, tab: oneOf(p.tab, ["evidence", "subject", "valuation", "coverage"] as const) ?? "evidence" },
  };
}

export function loadState(storage: Pick<Storage, "getItem"> | undefined): WorkspaceState {
  try { const raw = storage?.getItem(STORAGE_KEY); return raw ? sanitizeState(JSON.parse(raw)) : defaultState(); }
  catch { return defaultState(); }
}
export function saveState(storage: Pick<Storage, "setItem"> | undefined, state: WorkspaceState): void {
  try { storage?.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* Private mode / quota: state stays in memory. */ }
}
