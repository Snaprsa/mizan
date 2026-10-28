import { MapRecord } from "@/lib/api";
export type MapBounds = { south: number; west: number; north: number; east: number };
export const COLORS = { property: "#2563eb", transaction: "#15803d", listing: "#b45309", other: "#64748b", market: "#7c3aed" };
export function inBounds(r: MapRecord, b: MapBounds | null) {
  if (!r.coordinates || !b) return false;
  const [lat, lng] = r.coordinates;
  return lat >= b.south && lat <= b.north && (b.west <= b.east ? lng >= b.west && lng <= b.east : lng >= b.west || lng <= b.east);
}
export function googleMapsUrl(r: MapRecord) {
  const query = r.coordinates ? r.coordinates.join(",") : [r.district, r.city, "Saudi Arabia"].filter(Boolean).join(", ");
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

