// Coordinate conventions are explicit. Mizan's API and Leaflet use [latitude, longitude];
// GeoJSON (RFC 7946) uses [longitude, latitude]. Convert only through these helpers.

/** Mizan API / Leaflet order: [latitude, longitude]. */
export type LatLng = [number, number];
/** GeoJSON order: [longitude, latitude]. */
export type LngLat = [number, number];
export type GeoJSONPolygon = { type: "Polygon"; coordinates: LngLat[][] };

export type SearchArea =
  | { kind: "radius"; center: LatLng; radius_m: number }
  | { kind: "polygon"; ring: LatLng[] };

export const EARTH_RADIUS_M = 6371008.8;
const rad = (d: number) => (d * Math.PI) / 180;
const deg = (r: number) => (r * 180) / Math.PI;

export function isLatLng(value: unknown): value is LatLng {
  return Array.isArray(value) && value.length === 2 && value.every(n => typeof n === "number" && Number.isFinite(n))
    && Math.abs(value[0]) <= 90 && Math.abs(value[1]) <= 180;
}
export const toGeoJSONPosition = ([lat, lng]: LatLng): LngLat => [lng, lat];
export const fromGeoJSONPosition = ([lng, lat]: LngLat): LatLng => [lat, lng];

/** Closes the ring as GeoJSON requires (first position repeated last). */
export function polygonFromLatLngs(points: LatLng[]): GeoJSONPolygon {
  if (points.length < 3) throw new Error("A polygon needs at least three vertices");
  const ring = points.map(toGeoJSONPosition);
  const [first, last] = [ring[0], ring[ring.length - 1]];
  if (first[0] !== last[0] || first[1] !== last[1]) ring.push([first[0], first[1]]);
  return { type: "Polygon", coordinates: [ring] };
}
/** Returns open [lat, lng] vertices (closing duplicate removed). */
export function latLngsFromPolygon(polygon: GeoJSONPolygon): LatLng[] {
  const ring = polygon.coordinates[0].map(fromGeoJSONPosition);
  const [first, last] = [ring[0], ring[ring.length - 1]];
  return ring.length > 1 && first[0] === last[0] && first[1] === last[1] ? ring.slice(0, -1) : ring;
}

/** Great-circle distance on a spherical earth; approximate (±0.5%). */
export function haversineMeters(a: LatLng, b: LatLng): number {
  const dLat = rad(b[0] - a[0]); const dLng = rad(b[1] - a[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(h)));
}
export function pathLengthMeters(points: LatLng[]): number {
  let total = 0;
  for (let i = 1; i < points.length; i++) total += haversineMeters(points[i - 1], points[i]);
  return total;
}
/** Spherical-excess polygon area (same approach as common GIS libraries); approximate. */
export function geodesicAreaSqm(points: LatLng[]): number {
  if (points.length < 3) return 0;
  let sum = 0;
  for (let i = 0; i < points.length; i++) {
    const [lat1, lng1] = points[i]; const [lat2, lng2] = points[(i + 1) % points.length];
    sum += rad(lng2 - lng1) * (2 + Math.sin(rad(lat1)) + Math.sin(rad(lat2)));
  }
  return Math.abs((sum * EARTH_RADIUS_M * EARTH_RADIUS_M) / 2);
}
export function destination(origin: LatLng, bearingDeg: number, distanceM: number): LatLng {
  const d = distanceM / EARTH_RADIUS_M; const b = rad(bearingDeg);
  const lat1 = rad(origin[0]); const lng1 = rad(origin[1]);
  const lat2 = Math.asin(Math.sin(lat1) * Math.cos(d) + Math.cos(lat1) * Math.sin(d) * Math.cos(b));
  const lng2 = lng1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(lat1), Math.cos(d) - Math.sin(lat1) * Math.sin(lat2));
  return [deg(lat2), ((deg(lng2) + 540) % 360) - 180];
}
export function circleRing(center: LatLng, radiusM: number, steps = 64): LatLng[] {
  return Array.from({ length: steps }, (_, i) => destination(center, (360 * i) / steps, radiusM));
}
/** Ray casting in planar lat/lng; adequate for site/search areas at city scale. */
export function pointInRing(point: LatLng, ring: LatLng[]): boolean {
  const [y, x] = point; let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [yi, xi] = ring[i]; const [yj, xj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
export function inSearchArea(point: LatLng | null, area: SearchArea | null): boolean {
  if (!point || !area) return false;
  return area.kind === "radius" ? haversineMeters(point, area.center) <= area.radius_m : pointInRing(point, area.ring);
}
export function boundsOf(points: LatLng[]): { south: number; west: number; north: number; east: number } | null {
  if (!points.length) return null;
  return { south: Math.min(...points.map(p => p[0])), north: Math.max(...points.map(p => p[0])),
    west: Math.min(...points.map(p => p[1])), east: Math.max(...points.map(p => p[1])) };
}
export function areaPoints(area: SearchArea | null): LatLng[] {
  if (!area) return [];
  return area.kind === "radius" ? circleRing(area.center, area.radius_m, 16) : area.ring;
}

export type CoordinateParse =
  | { ok: true; value: LatLng; warning?: string }
  | { ok: false; error: string; swapped?: LatLng };

// Saudi Arabia roughly spans latitude 16–33 N and longitude 34–56 E.
const inSaudiLat = (n: number) => n >= 16 && n <= 33;
const inSaudiLng = (n: number) => n >= 34 && n <= 56;

/** Parses "lat, lng" decimal degrees. Never swaps silently: a likely swap is returned as a suggestion. */
export function parseCoordinates(text: string): CoordinateParse | null {
  const m = text.trim().match(/^(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([NS])?\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([EW])?$/i);
  if (!m) return null;
  let a = Number(m[1]); let b = Number(m[3]);
  if (m[2]?.toUpperCase() === "S") a = -Math.abs(a);
  if (m[4]?.toUpperCase() === "W") b = -Math.abs(b);
  if (Math.abs(a) > 90) {
    return Math.abs(b) <= 90 ? { ok: false, error: "The first value must be latitude (−90 to 90). These look like longitude, latitude.", swapped: [b, a] }
      : { ok: false, error: "Latitude must be between −90 and 90." };
  }
  if (Math.abs(b) > 180) return { ok: false, error: "Longitude must be between −180 and 180." };
  if (inSaudiLng(a) && inSaudiLat(b) && !(inSaudiLat(a) && inSaudiLng(b)))
    return { ok: false, error: "These values look like longitude, latitude. Mizan expects latitude first.", swapped: [b, a] };
  const value: LatLng = [a, b];
  return inSaudiLat(a) && inSaudiLng(b) ? { ok: true, value } : { ok: true, value, warning: "This location is outside Saudi Arabia." };
}

export function formatDistance(m: number): string {
  return m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(m < 10000 ? 2 : 1)} km`;
}
export function formatArea(sqm: number): string {
  return sqm < 100000 ? `${Math.round(sqm).toLocaleString("en-SA")} m²` : `${(sqm / 1e6).toFixed(3)} km²`;
}
