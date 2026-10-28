import type { MapRecord } from "@/lib/api";
import type { LatLng, SearchArea } from "@/lib/geo";
import type { Basemap, Camera, Subject } from "@/lib/map-workspace-state";
import type { ProviderKey } from "@/lib/map-provider";

export type MapBounds = { south: number; west: number; north: number; east: number };
export type MapTool = "browse" | "place_subject" | "draw_area" | "draw_site" | "measure";
export type Draft = { tool: "draw_area" | "draw_site" | "measure"; points: LatLng[] } | null;

export type Capabilities = Record<"satellite" | "hybrid" | "roadmap" | "terrain" | "rotate" | "tilt" | "streetView" | "geocoding", boolean>;
export type MapStatus = {
  provider: ProviderKey; state: "loading" | "ready" | "error";
  message?: string; capabilities: Capabilities;
  /** What the provider tells us about imagery; never invented. */
  imageryNote: string;
};
export const NO_CAPABILITIES: Capabilities = { satellite: false, hybrid: false, roadmap: false, terrain: false,
  rotate: false, tilt: false, streetView: false, geocoding: false };

export type GeocodeResult = { label: string; coordinates: LatLng;
  precision: "rooftop" | "range_interpolated" | "geometric_center" | "approximate"; types: string[] };
export type StreetViewResult = { ok: boolean; message: string };

export type RendererProps = {
  records: MapRecord[]; selectedId: string | null; groupIds: string[];
  basemap: Basemap; initialCamera: Camera | null;
  subject: Subject | null; subjectDraggable: boolean;
  searchArea: SearchArea | null; editArea: boolean; siteOutline: LatLng[] | null;
  tool: MapTool; draft: Draft;
  onCamera: (camera: Camera, bounds: MapBounds) => void;
  onSelect: (id: string) => void; onGroup: (ids: string[]) => void;
  onMapClick: (point: LatLng) => void; onSubjectMove: (point: LatLng) => void;
  onAreaEdit: (area: SearchArea) => void; onStatus: (status: MapStatus) => void;
};
export type RendererHandle = {
  fit: (points: LatLng[], maxZoom?: number) => void;
  center: () => LatLng | null;
  resetNorth: () => void;
  rotate: (deltaDeg: number) => boolean;
  tilt: (deg: number) => boolean;
  streetView: (at: LatLng) => Promise<StreetViewResult>;
  geocode: (query: string) => Promise<GeocodeResult[]>;
};
