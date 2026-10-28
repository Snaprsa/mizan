"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { MapRecord } from "@/lib/api";

import { MapBounds, COLORS } from "@/lib/map-utils";

type Props = { records: MapRecord[]; selected: string | null; fitKey: number;
  onSelect: (id: string) => void; onBounds: (bounds: MapBounds) => void;
  onCluster: (ids: string[]) => void; pickMode?: boolean; subject?: [number, number] | null; radiusKm?: number; onPick?: (coordinates: [number, number]) => void };
export default function IntelligenceMap({ records, selected, fitKey, onSelect, onBounds, onCluster, pickMode = false, subject = null, radiusKm = 3, onPick }: Props) {
  const container = useRef<HTMLDivElement>(null); const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null); const live = useRef({ records, onSelect, onBounds, onCluster, selected, pickMode, onPick });
  const [tileError, setTileError] = useState(false);
  const initialFit = useRef(false);
  const subjectLayer = useRef<L.LayerGroup | null>(null);
  live.current = { records, onSelect, onBounds, onCluster, selected, pickMode, onPick };
  useEffect(() => {
    if (!container.current) return;
    const m = L.map(container.current, { center: [24.7136, 46.6753], zoom: 6, scrollWheelZoom: true });
    map.current = m; layer.current = L.layerGroup().addTo(m);
    subjectLayer.current = L.layerGroup().addTo(m);
    m.on("click", e => { if (live.current.pickMode) live.current.onPick?.([e.latlng.lat, e.latlng.lng]); });
    const tile = L.tileLayer(process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: process.env.NEXT_PUBLIC_MAP_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors', maxZoom: 19,
    }).addTo(m);
    tile.on("tileerror", () => setTileError(true));
    L.control.scale({ imperial: false }).addTo(m);
    function refresh() {
      const bounds = m.getBounds();
      live.current.onBounds({ south: bounds.getSouth(), west: bounds.getWest(), north: bounds.getNorth(), east: bounds.getEast() });
      draw(m, layer.current!, live.current.records, live.current.selected, live.current.onSelect, live.current.onCluster);
    }
    m.on("moveend zoomend", refresh); refresh();
    const resize = new ResizeObserver(() => m.invalidateSize()); resize.observe(container.current);
    return () => { resize.disconnect(); m.remove(); map.current = null; layer.current = null; initialFit.current = false; };
  }, []);
  useEffect(() => {
    const m = map.current; if (!m || !layer.current) return;
    const points = records.filter(r => r.coordinates).map(r => r.coordinates!);
    if (!initialFit.current && points.length) { m.fitBounds(L.latLngBounds(points), { padding: [45, 45], maxZoom: 14 }); initialFit.current = true; }
    draw(m, layer.current, records, selected, onSelect, onCluster);
  }, [records, selected, onSelect, onCluster]);
  useEffect(() => {
    const m = map.current; if (!m) return;
    const r = records.find(r => r.id === selected);
    if (r?.coordinates) m.flyTo(r.coordinates, Math.max(m.getZoom(), 15), { duration: 0.4 });
    // Selection follows the adjacent list; changing filters must not reset the user's map view.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);
  useEffect(() => {
    const points = live.current.records.filter(r => r.coordinates).map(r => r.coordinates!);
    if (points.length) map.current?.fitBounds(L.latLngBounds(points), { padding: [45, 45], maxZoom: 15 });
  }, [fitKey]);
  useEffect(() => {
    const m = map.current; const group = subjectLayer.current;
    if (!m || !group) return;
    group.clearLayers();
    m.getContainer().style.cursor = pickMode ? "crosshair" : "";
    if (subject) {
      L.circle(subject, { radius: radiusKm * 1000, color: "#2563eb", weight: 1, dashArray: "5 5", fillOpacity: 0.025 }).addTo(group);
      const marker = L.marker(subject, { title: "Subject location", draggable: pickMode,
        icon: L.divIcon({ className: "mizan-map-icon", iconSize: [38, 38], iconAnchor: [19, 19],
          html: '<span style="background:#1d4ed8;width:38px;height:38px;border:3px solid white;outline:2px solid #1d4ed8">S</span>' }) }).addTo(group);
      marker.bindTooltip("Subject property · selected location");
      marker.on("dragend", () => { const point = marker.getLatLng(); live.current.onPick?.([point.lat, point.lng]); });
    }
  }, [subject, pickMode, radiusKm]);
  return <div className="relative h-full min-h-[440px]">
    <div ref={container} className="h-full min-h-[440px] w-full rounded-lg z-0" aria-label="Map of Mizan properties and comparable evidence" />
    {tileError && <div role="status" className="absolute top-3 left-14 right-3 z-[500] bg-white border border-amber-300 px-3 py-2 rounded text-xs text-amber-900">Some map tiles could not load. Your evidence list and Google Maps links remain available.</div>}
  </div>;
}

// Cluster nearby markers at the current zoom. Counts always refer to saved evidence records.
function draw(map: L.Map, layer: L.LayerGroup, records: MapRecord[], selected: string | null,
  onSelect: (id: string) => void, onCluster: (ids: string[]) => void) {
  layer.clearLayers();
  const buckets = new Map<string, MapRecord[]>();
  for (const r of records) {
    if (!r.coordinates) continue;
    const p = map.project(r.coordinates, map.getZoom());
    const cell = `${Math.floor(p.x / 55)},${Math.floor(p.y / 55)}`;
    buckets.set(cell, [...(buckets.get(cell) || []), r]);
  }
  for (const group of Array.from(buckets.values())) {
    const coords: [number, number] = [group.reduce((s, r) => s + r.coordinates![0], 0) / group.length,
      group.reduce((s, r) => s + r.coordinates![1], 0) / group.length];
    const hasSelected = group.some(r => r.id === selected);
    const color = group.length === 1 ? COLORS[group[0].kind] : "#0f172a";
    const icon = L.divIcon({ className: "mizan-map-icon", iconSize: [34, 34], iconAnchor: [17, 17],
      html: `<span style="background:${color};${hasSelected ? 'outline:3px solid #60a5fa;outline-offset:2px;' : ''}">${group.length > 1 ? group.length : group[0].kind === 'property' ? 'P' : group[0].kind === 'transaction' ? 'T' : group[0].kind === 'listing' ? 'L' : group[0].kind === 'market' ? 'M' : '?'}</span>` });
    const marker = L.marker(coords, { icon, title: group.length > 1 ? `${group.length} evidence records` : group[0].title, keyboard: true }).addTo(layer);
    const label = document.createElement("div");
    label.textContent = group.length > 1 ? `${group.length} saved records · ${group.filter(r => r.kind === 'transaction').length} recorded transactions · click to inspect` : group[0].title;
    marker.bindTooltip(label);
    marker.on("click", () => {
      if (group.length === 1) { onCluster([]); onSelect(group[0].id); }
      else { onCluster(group.map(r => r.id));
        const bounds = L.latLngBounds(group.map(r => r.coordinates!));
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: Math.min(map.getZoom() + 2, 19) }); }
    });
  }
}
