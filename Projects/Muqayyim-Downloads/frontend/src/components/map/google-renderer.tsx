"use client";
// Google Maps JavaScript API renderer. Uses only current core APIs: Map, OverlayView, Circle, Polygon,
// Polyline, Geocoder and StreetViewService. No Drawing library, no legacy Marker, no 45° raster imagery.
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type { MapRecord } from "@/lib/api";
import { clusterProjected } from "@/lib/map-clustering";
import type { LatLng } from "@/lib/geo";
import { loadGoogleMaps, onGoogleAuthFailure } from "@/lib/map-provider";
import { DEFAULT_CENTER } from "@/lib/map-workspace-state";
import { arrowDelta, evidenceMarker, subjectMarker, vertexDot } from "./markers";
import type { Capabilities, GeocodeResult, RendererHandle, RendererProps } from "./types";

type Props = RendererProps & { apiKey: string; mapId: string | null };
const ll = (p: LatLng) => ({ lat: p[0], lng: p[1] });
const AREA_STYLE = { strokeColor: "#38bdf8", strokeWeight: 2, fillColor: "#38bdf8", fillOpacity: 0.08 };
const SITE_STYLE = { strokeColor: "#f59e0b", strokeWeight: 2, fillColor: "#f59e0b", fillOpacity: 0.12, clickable: false };

const GoogleRenderer = forwardRef<RendererHandle, Props>(function GoogleRenderer(props, ref) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<google.maps.Map | null>(null);
  const overlay = useRef<(google.maps.OverlayView & { redraw: () => void }) | null>(null);
  const shapes = useRef<{ circle?: google.maps.Circle; polygon?: google.maps.Polygon; site?: google.maps.Polygon; draft?: google.maps.Polyline;
    pathListeners?: google.maps.MapsEventListener[] }>({});
  const live = useRef(props); live.current = props;
  const syncing = useRef(false);
  const caps = useRef<Capabilities>({ satellite: true, hybrid: true, roadmap: true, terrain: true, rotate: false, tilt: false, streetView: true, geocoding: true });

  useEffect(() => {
    let disposed = false; const listeners: google.maps.MapsEventListener[] = [];
    const stopAuth = onGoogleAuthFailure(() => live.current.onStatus({ provider: "google", state: "error", capabilities: caps.current,
      imageryNote: "", message: "Google rejected the API key (invalid key, referrer/API restriction, or billing not enabled for the project)." }));
    live.current.onStatus({ provider: "google", state: "loading", capabilities: caps.current, imageryNote: "" });
    loadGoogleMaps(props.apiKey, props.mapId).then(async () => {
      const { Map, OverlayView } = await google.maps.importLibrary("maps") as google.maps.MapsLibrary;
      if (disposed || !container.current) return;
      const cam = live.current.initialCamera;
      const m = new Map(container.current, {
        center: ll(cam?.center || DEFAULT_CENTER), zoom: cam?.zoom ?? 11, heading: cam?.heading ?? 0, tilt: cam?.tilt ?? 0,
        mapTypeId: live.current.basemap, ...(props.mapId ? { mapId: props.mapId } : {}),
        mapTypeControl: false, fullscreenControl: false, streetViewControl: true, scaleControl: true, rotateControl: true,
        zoomControl: true, clickableIcons: false, gestureHandling: "greedy", isFractionalZoomEnabled: false,
      });
      map.current = m;
      // "Ready" is reported only after imagery tiles actually load; a loaded script alone proves nothing.
      let tilesLoaded = false;
      const IMAGERY_NOTE = "Imagery © Google and its data providers (attribution shown on the map). Google does not expose satellite capture dates through this API; dates are therefore not shown.";
      const updateCaps = () => {
        const vector = m.getRenderingType() === google.maps.RenderingType.VECTOR;
        caps.current = { ...caps.current, rotate: vector, tilt: vector };
        live.current.onStatus(tilesLoaded ? { provider: "google", state: "ready", capabilities: caps.current, imageryNote: IMAGERY_NOTE }
          : { provider: "google", state: "loading", capabilities: caps.current, imageryNote: "Waiting for Google imagery tiles…" });
      };
      listeners.push(m.addListener("renderingtype_changed", updateCaps));
      listeners.push(m.addListener("tilesloaded", () => { if (!tilesLoaded) { tilesLoaded = true; updateCaps(); } }));
      const slow = setTimeout(() => { if (!tilesLoaded && !disposed) live.current.onStatus({ provider: "google", state: "loading", capabilities: caps.current,
        imageryNote: "Google imagery tiles have not loaded yet (network, key restriction, billing or quota). Evidence and saved work remain available." }); }, 15000);
      listeners.push({ remove: () => clearTimeout(slow) } as google.maps.MapsEventListener);
      let cameraTimer: ReturnType<typeof setTimeout> | undefined;
      const reportCamera = () => { clearTimeout(cameraTimer); cameraTimer = setTimeout(() => {
        const c = m.getCenter(); const b = m.getBounds(); if (!c || !b) return;
        const ne = b.getNorthEast(); const sw = b.getSouthWest();
        live.current.onCamera({ center: [c.lat(), c.lng()], zoom: m.getZoom() ?? 11, heading: m.getHeading() ?? 0, tilt: m.getTilt() ?? 0 },
          { south: sw.lat(), west: sw.lng(), north: ne.lat(), east: ne.lng() }); }, 250); };
      // bounds_changed (debounced) works even when tiles fail, unlike "idle".
      listeners.push(m.addListener("bounds_changed", reportCamera), m.addListener("heading_changed", reportCamera), m.addListener("tilt_changed", reportCamera));
      listeners.push({ remove: () => clearTimeout(cameraTimer) } as google.maps.MapsEventListener);
      listeners.push(m.addListener("click", (e: google.maps.MapMouseEvent) => { if (e.latLng) live.current.onMapClick([e.latLng.lat(), e.latLng.lng()]); }));
      updateCaps();

      class EvidenceOverlay extends OverlayView {
        root = document.createElement("div");
        onAdd() { this.root.className = "mizan-overlay-root"; this.getPanes()!.overlayMouseTarget.appendChild(this.root); }
        onRemove() { this.root.remove(); }
        redraw() { this.draw(); }
        draw() {
          const projection = this.getProjection(); if (!projection) return;
          const p = live.current; this.root.replaceChildren();
          const place = (el: HTMLElement, at: LatLng) => { const px = projection.fromLatLngToDivPixel(new google.maps.LatLng(at[0], at[1]));
            if (!px) return; el.style.left = `${px.x}px`; el.style.top = `${px.y}px`; this.root.appendChild(el); OverlayView.preventMapHitsAndGesturesFrom(el); };
          const items = p.records.filter(r => r.coordinates).map(r => { const px = projection.fromLatLngToDivPixel(new google.maps.LatLng(r.coordinates![0], r.coordinates![1]));
            return { record: r, coordinates: r.coordinates as LatLng, x: px?.x ?? NaN, y: px?.y ?? NaN }; });
          for (const cluster of clusterProjected<MapRecord>(items)) {
            const el = evidenceMarker(cluster, p.selectedId, p.groupIds);
            el.addEventListener("click", ev => { ev.stopPropagation();
              if (cluster.records.length === 1) { live.current.onGroup([]); live.current.onSelect(cluster.records[0].id); }
              else { live.current.onGroup(cluster.records.map(r => r.id)); fit(cluster.records.map(r => r.coordinates as LatLng), Math.min((m.getZoom() ?? 11) + 3, 20)); } });
            el.style.left = `${cluster.x}px`; el.style.top = `${cluster.y}px`; this.root.appendChild(el); OverlayView.preventMapHitsAndGesturesFrom(el);
          }
          p.draft?.points.forEach((pt, i) => place(vertexDot(i, p.draft!.tool === "measure" ? "Measurement point" : "Vertex"), pt));
          if (p.subject) {
            const el = subjectMarker(p.subject, p.subjectDraggable); place(el, p.subject.coordinates);
            if (p.subjectDraggable) attachDrag(el, projection);
          }
        }
      }
      const attachDrag = (el: HTMLElement, projection: google.maps.MapCanvasProjection) => {
        const toLatLng = (clientX: number, clientY: number): LatLng | null => {
          const rect = container.current!.getBoundingClientRect();
          const pt = projection.fromContainerPixelToLatLng(new google.maps.Point(clientX - rect.left, clientY - rect.top));
          return pt ? [pt.lat(), pt.lng()] : null;
        };
        el.addEventListener("pointerdown", e => { e.preventDefault(); el.setPointerCapture(e.pointerId); m.setOptions({ gestureHandling: "none" }); el.classList.add("is-dragging"); });
        el.addEventListener("pointermove", e => { if (!el.hasPointerCapture(e.pointerId)) return;
          const at = toLatLng(e.clientX, e.clientY); const div = at && projection.fromLatLngToDivPixel(new google.maps.LatLng(at[0], at[1]));
          if (div) { el.style.left = `${div.x}px`; el.style.top = `${div.y}px`; } });
        el.addEventListener("pointerup", e => { if (!el.hasPointerCapture(e.pointerId)) return; el.releasePointerCapture(e.pointerId);
          m.setOptions({ gestureHandling: "greedy" }); const p = toLatLng(e.clientX, e.clientY); if (p) live.current.onSubjectMove(p); });
        el.addEventListener("keydown", e => { const d = arrowDelta(e); const s = live.current.subject; if (!d || !s) return; e.preventDefault();
          const px = projection.fromLatLngToContainerPixel(new google.maps.LatLng(s.coordinates[0], s.coordinates[1])); if (!px) return;
          const rect = container.current!.getBoundingClientRect(); const p = toLatLng(px.x + d[0] + rect.left, px.y + d[1] + rect.top);
          if (p) { live.current.onSubjectMove(p); requestAnimationFrame(() => (container.current?.querySelector(".mizan-subject") as HTMLElement | null)?.focus()); } });
      };
      const o = new EvidenceOverlay() as EvidenceOverlay & { redraw: () => void }; o.setMap(m); overlay.current = o;
      syncShapes();
    }).catch(e => live.current.onStatus({ provider: "google", state: "error", capabilities: caps.current, imageryNote: "", message: (e as Error).message }));
    return () => { disposed = true; stopAuth(); listeners.forEach(l => l.remove());
      overlay.current?.setMap(null); const s = shapes.current; s.pathListeners?.forEach(l => l.remove());
      [s.circle, s.polygon, s.site, s.draft].forEach(x => x?.setMap(null)); shapes.current = {};
      if (map.current) google.maps.event.clearInstanceListeners(map.current); map.current = null; overlay.current = null; };
    // The map is created once; later prop changes are applied imperatively below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function fit(points: LatLng[], maxZoom = 17) {
    const m = map.current; if (!m || !points.length) return;
    if (points.length === 1) { m.panTo(ll(points[0])); m.setZoom(Math.max(m.getZoom() ?? 11, Math.min(maxZoom, 17))); return; }
    const b = new google.maps.LatLngBounds(); points.forEach(p => b.extend(ll(p)));
    m.fitBounds(b, 56);
    google.maps.event.addListenerOnce(m, "idle", () => { if ((m.getZoom() ?? 0) > maxZoom) m.setZoom(maxZoom); });
  }

  function syncShapes() {
    const m = map.current; if (!m) return; const p = live.current; const s = shapes.current;
    syncing.current = true;
    const area = p.searchArea;
    if (area?.kind === "radius") {
      if (!s.circle) {
        s.circle = new google.maps.Circle({ ...AREA_STYLE, map: m });
        const report = () => { if (syncing.current) return; const c = s.circle!.getCenter(); if (c) live.current.onAreaEdit({ kind: "radius", center: [c.lat(), c.lng()], radius_m: Math.max(10, Math.min(50000, s.circle!.getRadius())) }); };
        s.circle.addListener("radius_changed", report); s.circle.addListener("center_changed", report);
      }
      s.circle.setCenter(ll(area.center)); s.circle.setRadius(area.radius_m); s.circle.setEditable(p.editArea); s.circle.setOptions({ clickable: p.editArea });
    } else { s.circle?.setMap(null); s.circle = undefined; }
    if (area?.kind === "polygon") {
      if (!s.polygon) s.polygon = new google.maps.Polygon({ ...AREA_STYLE, map: m });
      s.pathListeners?.forEach(l => l.remove());
      s.polygon.setPath(area.ring.map(ll)); s.polygon.setEditable(p.editArea); s.polygon.setOptions({ clickable: p.editArea });
      const path = s.polygon.getPath();
      const report = () => { if (syncing.current) return; live.current.onAreaEdit({ kind: "polygon", ring: path.getArray().map(q => [q.lat(), q.lng()] as LatLng) }); };
      s.pathListeners = ["set_at", "insert_at", "remove_at"].map(evt => path.addListener(evt, report));
    } else { s.pathListeners?.forEach(l => l.remove()); s.pathListeners = undefined; s.polygon?.setMap(null); s.polygon = undefined; }
    if (p.siteOutline) { if (!s.site) s.site = new google.maps.Polygon({ ...SITE_STYLE, map: m }); s.site.setPath(p.siteOutline.map(ll)); }
    else { s.site?.setMap(null); s.site = undefined; }
    if (p.draft && p.draft.points.length) {
      if (!s.draft) s.draft = new google.maps.Polyline({ map: m, strokeColor: p.draft.tool === "measure" ? "#f8fafc" : "#38bdf8", strokeWeight: 2, clickable: false });
      s.draft.setPath([...p.draft.points, ...(p.draft.tool !== "measure" && p.draft.points.length > 2 ? [p.draft.points[0]] : [])].map(ll));
    } else { s.draft?.setMap(null); s.draft = undefined; }
    syncing.current = false;
  }

  useEffect(() => { overlay.current?.redraw(); },
    [props.records, props.selectedId, props.groupIds, props.subject, props.subjectDraggable, props.draft]);
  useEffect(() => { syncShapes(); }, [props.searchArea, props.editArea, props.siteOutline, props.draft]);
  useEffect(() => { map.current?.setMapTypeId(props.basemap); }, [props.basemap]);
  useEffect(() => { map.current?.setOptions({ draggableCursor: props.tool === "browse" ? null : "crosshair", disableDoubleClickZoom: props.tool !== "browse" }); }, [props.tool]);

  useImperativeHandle(ref, () => ({
    fit,
    center: () => { const c = map.current?.getCenter(); return c ? [c.lat(), c.lng()] : null; },
    resetNorth: () => { map.current?.setHeading(0); map.current?.setTilt(0); },
    rotate: delta => { const m = map.current; if (!m || !caps.current.rotate) return false; m.setHeading(((m.getHeading() ?? 0) + delta + 360) % 360); return true; },
    tilt: deg => { const m = map.current; if (!m || !caps.current.tilt) return false; m.setTilt(deg); return (m.getTilt() ?? 0) === deg || deg === 0; },
    streetView: async at => {
      const m = map.current; if (!m) return { ok: false, message: "Map not ready." };
      const { StreetViewService, StreetViewSource } = await google.maps.importLibrary("streetView") as google.maps.StreetViewLibrary;
      try {
        const { data } = await new StreetViewService().getPanorama({ location: ll(at), radius: 50, sources: [StreetViewSource.OUTDOOR] });
        const pano = m.getStreetView(); pano.setPano(data.location!.pano!); pano.setVisible(true);
        return { ok: true, message: `Street View panorama within 50 m${data.imageDate ? ` · capture ${data.imageDate} (provider-reported)` : " · capture date not reported"}${data.copyright ? ` · ${data.copyright}` : ""}` };
      } catch { return { ok: false, message: "No outdoor Street View panorama within 50 m of this point." }; }
    },
    geocode: async query => {
      const { Geocoder } = await google.maps.importLibrary("geocoding") as google.maps.GeocodingLibrary;
      try {
        const { results } = await new Geocoder().geocode({ address: query, region: "SA", componentRestrictions: { country: "SA" } });
        const precision: Record<string, GeocodeResult["precision"]> = { ROOFTOP: "rooftop", RANGE_INTERPOLATED: "range_interpolated", GEOMETRIC_CENTER: "geometric_center", APPROXIMATE: "approximate" };
        return results.slice(0, 6).map(r => ({ label: r.formatted_address, coordinates: [r.geometry.location.lat(), r.geometry.location.lng()] as LatLng,
          precision: precision[String(r.geometry.location_type)] || "approximate", types: r.types }));
      } catch (e) {
        const code = (e as { code?: string }).code;
        if (code === "ZERO_RESULTS") return [];
        throw new Error(code === "REQUEST_DENIED" ? "Address search was denied: enable the Geocoding API for this key." : `Address search failed${code ? ` (${code})` : ""}.`);
      }
    },
  }));

  return <div ref={container} className="absolute inset-0" role="application" aria-label="Satellite map of the subject and saved evidence" />;
});
export default GoogleRenderer;
