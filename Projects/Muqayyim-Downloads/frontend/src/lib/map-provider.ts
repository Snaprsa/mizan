// Map provider configuration. NEXT_PUBLIC_* values are inlined at build time: rebuild after changing them.
// Google is the primary imagery provider; OpenStreetMap via Leaflet is a road-map-only labelled fallback.

export type ProviderKey = "google" | "leaflet";
export type ProviderConfig = {
  requested: ProviderKey;
  googleKey: string | null;
  googleMapId: string | null;
  fallbackTileUrl: string;
  fallbackAttribution: string;
  /** Why Google cannot be used, or null when configured. */
  googleBlocker: string | null;
};

export function readProviderConfig(): ProviderConfig {
  const requested = process.env.NEXT_PUBLIC_MAP_PROVIDER === "leaflet" ? "leaflet" : "google";
  const key = (process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "").trim();
  const placeholder = !key || /^YOUR_/i.test(key);
  const mapId = (process.env.NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID || "").trim();
  return {
    requested, googleKey: placeholder ? null : key, googleMapId: mapId && !/^YOUR_/i.test(mapId) ? mapId : null,
    fallbackTileUrl: process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    fallbackAttribution: process.env.NEXT_PUBLIC_MAP_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    googleBlocker: requested === "leaflet" ? "NEXT_PUBLIC_MAP_PROVIDER is set to leaflet."
      : placeholder ? "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is not configured. Add a restricted browser key and rebuild the frontend." : null,
  };
}

declare global {
  interface Window { gm_authFailure?: () => void; __mizanGoogleMapsReady?: () => void }
}

let loading: Promise<void> | null = null;
const authListeners = new Set<() => void>();
let authFailed = false;

export function onGoogleAuthFailure(listener: () => void): () => void {
  if (authFailed) listener();
  authListeners.add(listener);
  return () => { authListeners.delete(listener); };
}

/**
 * Loads the Maps JavaScript API with the documented async bootstrap (`loading=async` + `importLibrary`).
 * Does not use the retired Drawing library or 45° imagery.
 */
export function loadGoogleMaps(key: string, mapId: string | null): Promise<void> {
  if (typeof window === "undefined") return Promise.reject(new Error("Google Maps loads only in the browser"));
  if (typeof (window as { google?: { maps?: { importLibrary?: unknown } } }).google?.maps?.importLibrary === "function") return Promise.resolve();
  if (loading) return loading;
  // Google calls this global when the key is invalid, restricted or billing is not enabled.
  window.gm_authFailure = () => { authFailed = true; authListeners.forEach(l => l()); };
  loading = new Promise<void>((resolve, reject) => {
    window.__mizanGoogleMapsReady = () => resolve();
    const params = new URLSearchParams({ key, v: "weekly", loading: "async", callback: "__mizanGoogleMapsReady",
      language: document.documentElement.lang?.startsWith("ar") ? "ar" : "en", region: "SA" });
    if (mapId) params.set("map_ids", mapId);
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?${params}`;
    script.async = true;
    script.onerror = () => { loading = null; script.remove(); reject(new Error("The Google Maps script could not be loaded (network, blocker or firewall).")); };
    document.head.appendChild(script);
  });
  return loading;
}
