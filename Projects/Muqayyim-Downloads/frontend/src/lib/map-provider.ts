// Map imagery provider. Free by design:
// - Esri ArcGIS Location Platform free tier (account, no card; pay-as-you-go stays off, so usage stops
//   at the monthly allowance instead of billing). Satellite, labels, streets and outdoor tiles.
// - Without a key: OpenStreetMap road tiles, clearly labelled, no satellite imagery.
// NEXT_PUBLIC_* values are inlined at build time: rebuild after changing them.
import type { Basemap } from "./map-workspace-state.ts";

export const ESRI_TILES = "https://static-map-tiles-api.arcgis.com/arcgis/rest/services/static-basemap-tiles-service/v1/";
export const ESRI_GEOCODE = "https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates";

/** Esri style per basemap; hybrid = imagery + label overlay. */
export const ESRI_STYLES: Record<Basemap, { base: string; overlay?: string }> = {
  satellite: { base: "arcgis/imagery" },
  hybrid: { base: "arcgis/imagery", overlay: "arcgis/imagery/labels" },
  roadmap: { base: "arcgis/streets" },
  terrain: { base: "arcgis/outdoor" },
};

export type ProviderConfig = { esriKey: string | null; keySource: "build" | "browser" | null; osmUrl: string; osmAttribution: string };
type KeyStore = Pick<Storage, "getItem">;

/** A key pasted into the map style panel lives only in this browser's storage. */
export const ESRI_KEY_STORAGE = "mizan.arcgisKey";
const browserStore = (): Storage | undefined => { try { return typeof window === "undefined" ? undefined : window.localStorage; } catch { return undefined; } };
const usableKey = (k: string | null | undefined) => { const v = (k || "").trim(); return v && !/^YOUR_/i.test(v) ? v : null; };

export function readProviderConfig(store: KeyStore | undefined = browserStore()): ProviderConfig {
  const built = usableKey(process.env.NEXT_PUBLIC_ARCGIS_API_KEY);
  let stored: string | null = null;
  try { stored = usableKey(store?.getItem(ESRI_KEY_STORAGE)); } catch { /* storage unavailable */ }
  return {
    esriKey: built || stored, keySource: built ? "build" : stored ? "browser" : null,
    osmUrl: process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    osmAttribution: process.env.NEXT_PUBLIC_MAP_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  };
}
export function storeEsriKey(key: string | null): void {
  try { if (key) browserStore()?.setItem(ESRI_KEY_STORAGE, key.trim()); else browserStore()?.removeItem(ESRI_KEY_STORAGE); } catch { /* storage unavailable */ }
}

export const esriTileUrl = (style: string, key: string) => `${ESRI_TILES}${style}/static/tile/{z}/{y}/{x}?token=${encodeURIComponent(key)}`;

/** Styles the key can use, from the service's own /self listing; null when the listing has no style paths. */
export async function esriAvailableStyles(key: string, signal?: AbortSignal): Promise<Set<string> | null> {
  const r = await fetch(`${ESRI_TILES}self?f=json&token=${encodeURIComponent(key)}`, { signal });
  const body = await r.json();
  if (body.error) throw new Error(body.error.code === 498 || body.error.code === 499
    ? "Esri rejected the API key (invalid, expired, or missing the basemap privilege)." : body.error.message || "Esri basemap service error");
  const styles = new Set<string>();
  for (const s of body.styles || []) if (typeof s.path === "string") styles.add(s.path.replace(/^\//, ""));
  // Only trust the listing if it names styles the way we request them; otherwise let the tiles decide.
  return styles.has(ESRI_STYLES.satellite.base) || styles.has(ESRI_STYLES.roadmap.base) ? styles : null;
}

/** Provider copyright text for a style; never invented. */
export async function esriAttribution(style: string, key: string): Promise<string | null> {
  try {
    const r = await fetch(`${ESRI_TILES}${style}/static?f=json&token=${encodeURIComponent(key)}`);
    const body = await r.json();
    return typeof body.copyrightText === "string" ? body.copyrightText : null;
  } catch { return null; }
}

export type PlaceResult = { label: string; coordinates: [number, number]; precision: string; score: number };

/**
 * Esri World Geocoding (free tier, results not stored). Results only move the map;
 * the user places and confirms the subject pin themselves.
 */
export async function esriGeocode(query: string, key: string, signal?: AbortSignal): Promise<PlaceResult[]> {
  const params = new URLSearchParams({ f: "json", singleLine: query, countryCode: "SAU", maxLocations: "6",
    outFields: "Addr_type,Match_addr", token: key });
  const r = await fetch(`${ESRI_GEOCODE}?${params}`, { signal });
  const body = await r.json();
  if (body.error) throw new Error(body.error.code === 498 || body.error.code === 499 || body.error.code === 403
    ? "Address search is not enabled for this Esri key (add the geocoding privilege)." : body.error.message || "Address search failed");
  return (body.candidates || []).map((c: { address: string; location: { x: number; y: number }; score: number; attributes?: { Addr_type?: string } }) => ({
    label: c.address, coordinates: [c.location.y, c.location.x] as [number, number], score: c.score,
    precision: c.attributes?.Addr_type || "unknown",
  }));
}
