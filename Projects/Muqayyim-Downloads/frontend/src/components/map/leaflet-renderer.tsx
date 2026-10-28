"use client";
// Labelled road-map fallback (OpenStreetMap via Leaflet). It never claims satellite imagery.
// Leaflet uses [latitude, longitude], the same order as Mizan map records.
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import L from "leaflet";
import type { MapRecord } from "@/lib/api";
import { clusterProjected } from "@/lib/map-clustering";
import type { LatLng } from "@/lib/geo";
import { DEFAULT_CENTER } from "@/lib/map-workspace-state";
import { arrowDelta, evidenceMarker, subjectMarker, vertexDot } from "./markers";
import { NO_CAPABILITIES, type RendererHandle, type RendererProps } from "./types";

type Props = RendererProps & { tileUrl: string; attribution: string };
const icon = (html: HTMLElement, size = 34) => L.divIcon({ className: "mizan-leaflet-icon", html, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
const CAPS = { ...NO_CAPABILITIES, roadmap: true };

const LeafletRenderer = forwardRef<RendererHandle, Props>(function LeafletRenderer(props, ref) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layers = useRef<{ evidence?: L.LayerGroup; shapes?: L.LayerGroup; subject?: L.LayerGroup }>({});
  const live = useRef(props); live.current = props;

  useEffect(() => {
    if (!container.current) return;
    const cam = live.current.initialCamera;
    const m = L.map(container.current, { center: cam?.center || DEFAULT_CENTER, zoom: Math.min(cam?.zoom ?? 11, 19), zoomControl: true, keyboard: true });
    map.current = m;
    layers.current = { shapes: L.layerGroup().addTo(m), evidence: L.layerGroup().addTo(m), subject: L.layerGroup().addTo(m) };
    let failed = 0;
    const tiles = L.tileLayer(props.tileUrl, { attribution: props.attribution, maxZoom: 19 }).addTo(m);
    tiles.on("tileerror", () => { if (++failed === 3) live.current.onStatus({ provider: "leaflet", state: "error", capabilities: CAPS, imageryNote: "",
      message: "Road-map tiles are failing to load. Evidence lists and saved work remain available." }); });
    L.control.scale({ imperial: false }).addTo(m);
    const report = () => { const c = m.getCenter(); const b = m.getBounds();
      live.current.onCamera({ center: [c.lat, c.lng], zoom: m.getZoom(), heading: 0, tilt: 0 }, { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() });
      drawEvidence(); };
    m.on("moveend resize", report); m.on("zoomend", drawEvidence);
    m.on("click", e => live.current.onMapClick([e.latlng.lat, e.latlng.lng]));
    const resize = new ResizeObserver(() => m.invalidateSize()); resize.observe(container.current);
    live.current.onStatus({ provider: "leaflet", state: "ready", capabilities: CAPS,
      imageryNote: "Road-map fallback (OpenStreetMap). No satellite or aerial imagery is shown." });
    report(); drawShapes(); drawSubject();
    return () => { resize.disconnect(); m.remove(); map.current = null; layers.current = {}; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function drawEvidence() {
    const m = map.current; const group = layers.current.evidence; if (!m || !group) return;
    const p = live.current; group.clearLayers();
    const items = p.records.filter(r => r.coordinates).map(r => { const px = m.project(r.coordinates!, m.getZoom()); return { record: r, coordinates: r.coordinates as LatLng, x: px.x, y: px.y }; });
    for (const cluster of clusterProjected<MapRecord>(items)) {
      const el = evidenceMarker(cluster, p.selectedId, p.groupIds);
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
    const area = p.searchArea; const style = { color: "#0284c7", weight: 2, fillOpacity: 0.06 };
    if (area?.kind === "radius") {
      const circle = L.circle(area.center, { ...style, radius: area.radius_m }).addTo(group);
      if (p.editArea) { // Edge handle on the east side changes the radius.
        const edge = L.latLng(area.center).toBounds(area.radius_m * 2).getEast();
        const handle = L.marker([area.center[0], edge], { draggable: true, icon: icon(vertexDot(0, "Radius handle"), 14), title: "Drag to change radius" }).addTo(group);
        handle.on("drag", () => circle.setRadius(m.distance(area.center, handle.getLatLng())));
        handle.on("dragend", () => live.current.onAreaEdit({ kind: "radius", center: area.center, radius_m: Math.max(10, Math.min(50000, m.distance(area.center, handle.getLatLng()))) }));
      }
    }
    if (area?.kind === "polygon") {
      const poly = L.polygon(area.ring, style).addTo(group);
      if (p.editArea) area.ring.forEach((pt, i) => {
        const handle = L.marker(pt, { draggable: true, icon: icon(vertexDot(i, "Vertex"), 14), title: `Vertex ${i + 1} · drag to edit` }).addTo(group);
        handle.on("drag", () => { const ring = area.ring.slice(); const q = handle.getLatLng(); ring[i] = [q.lat, q.lng]; poly.setLatLngs(ring); });
        handle.on("dragend", () => { const ring = area.ring.slice(); const q = handle.getLatLng(); ring[i] = [q.lat, q.lng]; live.current.onAreaEdit({ kind: "polygon", ring }); });
      });
    }
    if (p.siteOutline) L.polygon(p.siteOutline, { color: "#d97706", weight: 2, fillOpacity: 0.12, interactive: false }).addTo(group);
    if (p.draft?.points.length) {
      L.polyline([...p.draft.points, ...(p.draft.tool !== "measure" && p.draft.points.length > 2 ? [p.draft.points[0]] : [])],
        { color: p.draft.tool === "measure" ? "#0f172a" : "#0284c7", weight: 2, dashArray: "4 4", interactive: false }).addTo(group);
      p.draft.points.forEach((pt, i) => L.marker(pt, { icon: icon(vertexDot(i, "Point"), 12), interactive: false }).addTo(group));
    }
  }
  function drawSubject() {
    const m = map.current; const group = layers.current.subject; if (!m || !group) return;
    const p = live.current; group.clearLayers(); if (!p.subject) return;
    const el = subjectMarker(p.subject, p.subjectDraggable);
    const marker = L.marker(p.subject.coordinates, { icon: icon(el, 38), draggable: p.subjectDraggable, keyboard: false, zIndexOffset: 1000 }).addTo(group);
    L.DomEvent.disableClickPropagation(el);
    marker.on("dragend", () => { const q = marker.getLatLng(); live.current.onSubjectMove([q.lat, q.lng]); });
    if (p.subjectDraggable) el.addEventListener("keydown", e => { const d = arrowDelta(e); if (!d) return; e.preventDefault();
      const px = m.latLngToContainerPoint(p.subject!.coordinates).add(L.point(d[0], d[1])); const q = m.containerPointToLatLng(px);
      live.current.onSubjectMove([q.lat, q.lng]); requestAnimationFrame(() => (container.current?.querySelector(".mizan-subject") as HTMLElement | null)?.focus()); });
  }
  function fit(points: LatLng[], maxZoom = 17) {
    const m = map.current; if (!m || !points.length) return;
    if (points.length === 1) m.setView(points[0], Math.max(m.getZoom(), Math.min(maxZoom, 17)));
    else m.fitBounds(L.latLngBounds(points), { padding: [56, 56], maxZoom });
  }

  useEffect(() => { drawEvidence(); }, [props.records, props.selectedId, props.groupIds]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { drawShapes(); }, [props.searchArea, props.editArea, props.siteOutline, props.draft]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { drawSubject(); }, [props.subject, props.subjectDraggable]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const m = map.current; if (!m) return; m.getContainer().style.cursor = props.tool === "browse" ? "" : "crosshair";
    if (props.tool === "browse") m.doubleClickZoom.enable(); else m.doubleClickZoom.disable(); }, [props.tool]);

  useImperativeHandle(ref, () => ({
    fit, center: () => { const c = map.current?.getCenter(); return c ? [c.lat, c.lng] : null; },
    resetNorth: () => undefined, rotate: () => false, tilt: () => false,
    streetView: async () => ({ ok: false, message: "Street View requires the Google Maps provider." }),
    geocode: async () => { throw new Error("Address search requires the Google provider with the Geocoding API enabled. Enter coordinates instead."); },
  }));
  return <div ref={container} className="absolute inset-0" role="application" aria-label="Road map of the subject and saved evidence (fallback, no satellite imagery)" />;
});
export default LeafletRenderer;
