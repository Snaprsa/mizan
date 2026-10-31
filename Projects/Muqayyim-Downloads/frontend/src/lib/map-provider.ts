// Map imagery through Mizan's own API. The Esri key stays in the server's Keychain: this file, the browser
// bundle and tile URLs never contain it. Without a working key the map uses OpenStreetMap road tiles.
import type { Basemap } from "./map-workspace-state.ts";

export type Capabilities = Record<Basemap | "geocoding", boolean>;
export type ImageryStatus = { configured: boolean; provider: "esri" | "osm"; message: string | null; capabilities: Capabilities;
  esri_streets: boolean; attribution: string | null };
export type PlaceResult = { label: string; coordinates: [number, number]; precision: string; score: number | null };

const BASE = "/api/v1/imagery";
/** Layers per basemap; hybrid = imagery + label overlay. Paths are {z}/{y}/{x}. */
export const BASEMAP_LAYERS: Record<Basemap, { base: string; overlay?: string }> = {
  satellite: { base: "imagery" }, hybrid: { base: "imagery", overlay: "labels" },
  roadmap: { base: "streets" }, terrain: { base: "outdoor" },
};
export const imageryTileUrl = (layer: string) => `${BASE}/tiles/${layer}/{z}/{y}/{x}`;

export const readOsmConfig = () => ({
  url: process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
  attribution: process.env.NEXT_PUBLIC_MAP_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
});

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, init);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The imagery service is unavailable.");
  return body as T;
}
export const getImageryStatus = (signal?: AbortSignal) => json<ImageryStatus>("/status", { signal });
export const geocodePlaces = async (q: string, signal?: AbortSignal) => (await json<{ data: PlaceResult[] }>(`/geocode?q=${encodeURIComponent(q)}`, { signal })).data;
/** Sends the key once to the local API, which checks it with Esri and stores it encrypted. It is never returned. */
export const saveImageryKey = (key: string) => json<ImageryStatus>("/key", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key }) });
export const removeImageryKey = () => json<{ configured: boolean }>("/key", { method: "DELETE" });
