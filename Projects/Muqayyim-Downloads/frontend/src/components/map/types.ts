import type { MapRecord } from "@/lib/api";
import type { LatLng, SearchArea } from "@/lib/geo";
import type { Basemap, Camera, Subject } from "@/lib/map-workspace-state";

export type MapBounds = { south: number; west: number; north: number; east: number };
export type MapTool = "browse" | "place_subject" | "draw_area" | "draw_site" | "measure";
export type Draft = { tool: "draw_area" | "draw_site" | "measure"; points: LatLng[] } | null;

export type Capabilities = Record<Basemap | "geocoding", boolean>;
export type MapStatus = {
  provider: "esri" | "osm"; state: "loading" | "ready" | "error";
  message?: string; capabilities: Capabilities;
  /** Attribution/notes as reported by the provider; never invented (no imagery dates are exposed). */
  imageryNote: string;
};

export type RendererProps = {
  records: MapRecord[]; selectedId: string | null; groupIds: string[];
  basemap: Basemap; initialCamera: Camera | null;
  subject: Subject | null; subjectDraggable: boolean;
  searchArea: SearchArea | null; editArea: boolean; siteOutline: LatLng[] | null;
  /** Temporary search-result marker; never a subject or evidence. */
  placeMarker: LatLng | null;
  tool: MapTool; draft: Draft;
  onCamera: (camera: Camera, bounds: MapBounds) => void;
  onSelect: (id: string) => void; onGroup: (ids: string[]) => void;
  onMapClick: (point: LatLng) => void; onSubjectMove: (point: LatLng) => void;
  onAreaEdit: (area: SearchArea) => void; onStatus: (status: MapStatus) => void;
};
export type RendererHandle = {
  fit: (points: LatLng[], maxZoom?: number) => void;
  center: () => LatLng | null;
  zoomBy: (delta: number) => void;
};
