"use client";
// The single map renderer (Leaflet). Imagery: Esri free tier when a key is configured, otherwise
// OpenStreetMap road tiles. Leaflet uses [latitude, longitude], the same order as Mizan map records.
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type React from "react";
import L from "leaflet";
import type { MapRecord } from "@/lib/api";
import { clusterProjected } from "@/lib/map-clustering";
import type { LatLng } from "@/lib/geo";
import { BASEMAP_LAYERS, getImageryStatus, imageryTileUrl, readOsmConfig, type ImageryStatus } from "@/lib/map-provider";
import { DEFAULT_CENTER, type Basemap } from "@/lib/map-workspace-state";
import { arrowDelta, evidenceMarker, subjectMarker, vertexDot } from "./markers";
import type { Capabilities, RendererHandle, RendererProps } from "./types";

const icon = (html: HTMLElement, size = 34) => L.divIcon({ className: "mizan-leaflet-icon", html, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
const OSM_CAPS: Capabilities = { satellite: false, hybrid: false, roadmap: true, terrain: false, geocoding: false };
const NO_IMAGERY: ImageryStatus = { configured: false, provider: "osm", message: null, capabilities: OSM_CAPS, esri_streets: false, attribution: null };

const MapRenderer = forwardRef<RendererHandle, RendererProps>(function MapRenderer(props, ref) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layers = useRef<{ evidence?: L.LayerGroup; shapes?: L.LayerGroup; subject?: L.LayerGroup; tiles?: L.LayerGroup }>({});
  const live = useRef(props); live.current = props;
  const imagery = useRef<ImageryStatus>(NO_IMAGERY);
  const attribution = useRef("");
  const osm = useRef(readOsmConfig());

  useEffect(() => {
    if (!container.current) return;
    const cam = live.current.initialCamera;
    const m = L.map(container.current, { center: cam?.center || DEFAULT_CENTER, zoom: Math.min(cam?.zoom ?? 11, 19), zoomControl: false, keyboard: true });
    map.current = m;
    m.attributionControl.setPosition("bottomright");
    layers.current = { tiles: L.layerGroup().addTo(m), shapes: L.layerGroup().addTo(m), evidence: L.layerGroup().addTo(m), subject: L.layerGroup().addTo(m) };
    L.control.scale({ imperial: false, position: "bottomright" }).addTo(m);
    const report = () => { const c = m.getCenter(); const b = m.getBounds();
      live.current.onCamera({ center: [c.lat, c.lng], zoom: m.getZoom(), heading: 0, tilt: 0 }, { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() });
      drawEvidence(); };
    m.on("moveend zoomend resize", report);
    m.on("click", e => live.current.onMapClick([e.latlng.lat, e.latlng.lng]));
    const resize = new ResizeObserver(() => m.invalidateSize()); resize.observe(container.current);
    const controller = new AbortController();
    drawTiles(); // Standard map straight away; satellite replaces it once the server confirms it.
    getImageryStatus(controller.signal).then(status => { imagery.current = status; drawTiles(); })
      .catch(() => { if (!controller.signal.aborted) live.current.onStatus({ provider: "osm", state: "error", configured: false, activeBasemap: "roadmap", esri_streets: false, capabilities: OSM_CAPS, imageryNote: "", message: "The imagery service is unavailable." }); });
    report(); drawShapes(); drawSubject();
    return () => { controller.abort(); resize.disconnect(); m.remove(); map.current = null; layers.current = {}; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function drawTiles() {
    const m = map.current; const group = layers.current.tiles; if (!m || !group) return;
    group.clearLayers(); if (attribution.current) m.attributionControl.removeAttribution(attribution.current);
    const status = imagery.current; const caps = status.capabilities;
    const wanted = live.current.basemap;
    const basemap: Basemap = caps[wanted] ? wanted : (["hybrid", "satellite", "roadmap"] as Basemap[]).find(b => caps[b]) || "roadmap";
    const usesEsri = status.provider === "esri" && (basemap !== "roadmap" || status.esri_streets);
    let failures = 0;
    const report = (state: "ready" | "error", message: string | undefined, imageryNote: string) =>
      live.current.onStatus({ provider: status.provider, state, configured: status.configured, activeBasemap: basemap, esri_streets: status.esri_streets, capabilities: caps, imageryNote, message });
    const onError = () => { if (++failures === 4) report("error", usesEsri ? "Esri tiles stopped loading (monthly free allowance, key or network)." : "Map tiles aren’t loading. Your evidence list still works.", ""); };
    if (usesEsri) {
      const style = BASEMAP_LAYERS[basemap];
      L.tileLayer(imageryTileUrl(style.base), { maxZoom: 19 }).on("tileerror", onError).addTo(group);
      if (style.overlay) L.tileLayer(imageryTileUrl(style.overlay), { maxZoom: 19 }).addTo(group);
      attribution.current = `Powered by Esri${status.attribution ? ` | ${status.attribution}` : ""}`;
      report("ready", status.message || undefined, `${attribution.current}. Esri doesn’t report capture dates for these tiles, so none are shown.`);
    } else {
      L.tileLayer(osm.current.url, { maxZoom: 19 }).on("tileerror", onError).addTo(group);
      attribution.current = osm.current.attribution;
      report("ready", status.message || undefined, "");
    }
    m.attributionControl.addAttribution(attribution.current);
  }

  function drawEvidence() {
    const m = map.current; const group = layers.current.evidence; if (!m || !group) return;
    const p = live.current; group.clearLayers();
    const items = p.records.filter(r => r.coordinates).map(r => { const px = m.project(r.coordinates!, m.getZoom()); return { record: r, coordinates: r.coordinates as LatLng, x: px.x, y: px.y }; });
    for (const cluster of clusterProjected<MapRecord>(items)) {
      const el = evidenceMarker(cluster, p.selectedId, p.groupIds, m.getZoom() >= 15);
      L.marker(cluster.center, { icon: icon(el), keyboard: false }).addTo(group);
      L.DomEvent.disableClickPropagation(el);
      el.addEventListener("click", () => {
        if (cluster.records.length === 1) { live.current.onGroup([]); live.current.onSelect(cluster.records[0].id); }
        else { live.current.onGroup(cluster.records.map(r => r.id)); fit(cluster.records.map(r => r.coordinates as LatLng), Math.min(m.getZoom() + 3, 19)); }
      });
    }
  }
  function drawShapes() {
    const m = map.current; const group = layers.current.shapes; if (!m || !group) return;
    const p = live.current; group.clearLayers();
    const area = p.searchArea; const style = { color: "#0A84FF", weight: 2, fillOpacity: 0.08 };
    if (area?.kind === "radius") {
      const circle = L.circle(area.center, { ...style, radius: area.radius_m, dashArray: p.editArea ? undefined : "6 6" }).addTo(group);
      if (p.editArea) {
        const edge = L.latLng(area.center).toBounds(area.radius_m * 2).getEast();
        const handle = L.marker([area.center[0], edge], { draggable: true, icon: icon(vertexDot(0, "Radius handle"), 16), title: "Drag to change radius" }).addTo(group);
        handle.on("drag", () => circle.setRadius(m.distance(area.center, handle.getLatLng())));
        handle.on("dragend", () => live.current.onAreaEdit({ kind: "radius", center: area.center, radius_m: Math.max(10, Math.min(50000, m.distance(area.center, handle.getLatLng()))) }));
      }
    }
    if (area?.kind === "polygon") {
      const poly = L.polygon(area.ring, style).addTo(group);
      if (p.editArea) area.ring.forEach((pt, i) => {
        const handle = L.marker(pt, { draggable: true, icon: icon(vertexDot(i, "Vertex"), 16), title: `Corner ${i + 1} · drag to edit` }).addTo(group);
        handle.on("drag", () => { const ring = area.ring.slice(); const q = handle.getLatLng(); ring[i] = [q.lat, q.lng]; poly.setLatLngs(ring); });
        handle.on("dragend", () => { const ring = area.ring.slice(); const q = handle.getLatLng(); ring[i] = [q.lat, q.lng]; live.current.onAreaEdit({ kind: "polygon", ring }); });
      });
    }
    if (p.siteOutline) L.polygon(p.siteOutline, { color: "#FF9F0A", weight: 2.5, fillOpacity: 0.15, interactive: false }).addTo(group);
    if (p.draft?.points.length) {
      L.polyline([...p.draft.points, ...(p.draft.tool !== "measure" && p.draft.points.length > 2 ? [p.draft.points[0]] : [])],
        { color: p.draft.tool === "measure" ? "#ffffff" : "#0A84FF", weight: 2.5, dashArray: "4 6", interactive: false }).addTo(group);
      p.draft.points.forEach((pt, i) => L.marker(pt, { icon: icon(vertexDot(i, "Point"), 12), interactive: false }).addTo(group));
    }
    if (p.placeMarker) {
      const el = document.createElement("span"); el.className = "mizan-place"; el.setAttribute("aria-hidden", "true");
      L.marker(p.placeMarker, { icon: icon(el, 22), interactive: false }).addTo(group);
    }
  }
  function drawSubject() {
    const m = map.current; const group = layers.current.subject; if (!m || !group) return;
    const p = live.current; group.clearLayers(); if (!p.subject) return;
    const el = subjectMarker(p.subject, p.subjectDraggable);
    const marker = L.marker(p.subject.coordinates, { icon: L.divIcon({ className: "mizan-leaflet-icon", html: el, iconSize: [34, 44], iconAnchor: [17, 43] }), draggable: p.subjectDraggable, keyboard: false, zIndexOffset: 1000 }).addTo(group);
    L.DomEvent.disableClickPropagation(el);
    marker.on("dragend", () => { const q = marker.getLatLng(); live.current.onSubjectMove([q.lat, q.lng]); });
    if (p.subjectDraggable) el.addEventListener("keydown", e => { const d = arrowDelta(e); if (!d) return; e.preventDefault();
      const px = m.latLngToContainerPoint(p.subject!.coordinates).add(L.point(d[0], d[1])); const q = m.containerPointToLatLng(px);
      live.current.onSubjectMove([q.lat, q.lng]); requestAnimationFrame(() => (container.current?.querySelector(".mizan-subject") as HTMLElement | null)?.focus()); });
  }
  // Frame inside the part of the map not covered by the card (side card on desktop, bottom sheet on phones).
  function visibleInsets() {
    const size = map.current!.getSize();
    return size.x < 768 ? { tl: L.point(40, 56), br: L.point(40, Math.round(size.y * 0.55)) } : { tl: L.point(Math.min(420, size.x * 0.6), 64), br: L.point(72, 48) };
  }
  function fit(points: LatLng[], maxZoom = 17) {
    const m = map.current; if (!m || !points.length) return;
    const { tl, br } = visibleInsets();
    if (points.length > 1) { m.fitBounds(L.latLngBounds(points), { paddingTopLeft: tl, paddingBottomRight: br, maxZoom }); return; }
    const zoom = Math.max(m.getZoom(), Math.min(maxZoom, 17));
    const shift = tl.subtract(br).divideBy(2);
    m.setView(m.unproject(m.project(points[0], zoom).subtract(shift), zoom), zoom);
  }

  useEffect(() => { drawTiles(); }, [props.basemap]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { drawEvidence(); }, [props.records, props.selectedId, props.groupIds]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { drawShapes(); }, [props.searchArea, props.editArea, props.siteOutline, props.draft, props.placeMarker]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { drawSubject(); }, [props.subject, props.subjectDraggable]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const m = map.current; if (!m) return; m.getContainer().style.cursor = props.tool === "browse" ? "" : "crosshair";
    if (props.tool === "browse") m.doubleClickZoom.enable(); else m.doubleClickZoom.disable(); }, [props.tool]);

  useImperativeHandle(ref, () => ({
    fit, center: () => { const c = map.current?.getCenter(); return c ? [c.lat, c.lng] : null; },
    zoomBy: delta => { const m = map.current; if (m) m.setZoom(m.getZoom() + delta); },
  }));
  return <div ref={container} className="absolute inset-0 bg-[#e8e6e1]" role="application" aria-label="Map of the subject and saved evidence" />;
});
// next/dynamic does not forward refs, so the page passes its handle ref as a prop.
export default function MapRendererWithHandle({ handleRef, ...props }: RendererProps & { handleRef: React.MutableRefObject<RendererHandle | null> }) {
  return <MapRenderer ref={handleRef} {...props} />;
}
