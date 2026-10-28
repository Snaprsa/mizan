"use client";
// Map-first workspace: explore evidence → choose subject → property type → approach → sourced inputs → results.
import dynamic from "next/dynamic";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Check, Circle, Compass, Crosshair, Expand, Hexagon, Layers, LocateFixed, MousePointer2, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Ruler, RotateCcw, RotateCw, ScanEye, Table2, Shrink, Square } from "lucide-react";
import { getMapRecords, getProperty, saveProperty, getValuationCatalog, startMapAnalysis, type MapRecord, type MapResponse, type PreparedAnalysis, type ValuationMethod } from "@/lib/api";
import ValuationWorkflow from "@/components/valuation-workflow";
import { areaPoints, formatArea, formatDistance, geodesicAreaSqm, inSearchArea, latLngsFromPolygon, pathLengthMeters, polygonFromLatLngs, type GeoJSONPolygon, type LatLng, type SearchArea } from "@/lib/geo";
import { applyEvidenceFilters, facetValues, LAYERS, riyadhToday, UNAVAILABLE_LAYERS } from "@/lib/map-evidence";
import { BASEMAPS, defaultState, loadState, saveState, type Basemap, type Camera, type InspectorTab, type Subject, type WorkspaceState } from "@/lib/map-workspace-state";
import MapSearch from "@/components/map/map-search";
import { CoveragePanel, EvidenceList, EvidenceSummary, EvidenceTable, SelectedRecord, precisionLabel } from "@/components/map/evidence-panels";
import type { Draft, GeocodeResult, MapBounds, MapStatus, MapTool, RendererHandle } from "@/components/map/types";

const MapCanvas = dynamic(() => import("@/components/map/map-canvas"), { ssr: false,
  loading: () => <div className="absolute inset-0 grid place-items-center text-sm text-slate-500 bg-slate-200">Loading map…</div> });
const LIMIT = 5000;
const inBounds = (p: LatLng | null, b: MapBounds | null) => !!p && !!b && p[0] >= b.south && p[0] <= b.north && (b.west <= b.east ? p[1] >= b.west && p[1] <= b.east : p[1] >= b.west || p[1] <= b.east);
const STAGES = ["Location", "Property type", "Approach", "Inputs", "Result"];

function MapWorkspace() {
  const params = useSearchParams(); const router = useRouter();
  const caseId = params.get("case_id") || ""; const analysisId = params.get("analysis") || "";
  const [ws, setWs] = useState<WorkspaceState>(defaultState); const [hydrated, setHydrated] = useState(false);
  const update = useCallback((patch: Partial<WorkspaceState> | ((s: WorkspaceState) => Partial<WorkspaceState>)) =>
    setWs(s => ({ ...s, ...(typeof patch === "function" ? patch(s) : patch) })), []);
  useEffect(() => { setWs(loadState(typeof window === "undefined" ? undefined : window.localStorage)); setHydrated(true); }, []);
  useEffect(() => { if (hydrated) saveState(window.localStorage, ws); }, [ws, hydrated]);

  const [methods, setMethods] = useState<ValuationMethod[]>([]); const [propertyTypes, setPropertyTypes] = useState<string[]>([]);
  const [prepared, setPrepared] = useState<PreparedAnalysis | null>(null);
  const [data, setData] = useState<MapResponse | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [bounds, setBounds] = useState<MapBounds | null>(null); const [group, setGroup] = useState<string[]>([]);
  const [tool, setTool] = useState<MapTool>("browse"); const [draft, setDraft] = useState<Draft>(null); const [measure, setMeasure] = useState<LatLng[] | null>(null);
  const [editArea, setEditArea] = useState(false); const [status, setStatus] = useState<(MapStatus & { fallbackReason: string | null }) | null>(null);
  const [notice, setNotice] = useState(""); const [starting, setStarting] = useState(false); const [savingOutline, setSavingOutline] = useState(false);
  const [fullscreen, setFullscreen] = useState(false); const [narrow, setNarrow] = useState(false);
  const [viewportWidth, setViewportWidth] = useState(1440); const [overlayLeft, setOverlayLeft] = useState(false);
  const handle = useRef<RendererHandle | null>(null); const root = useRef<HTMLDivElement>(null);
  const today = useMemo(riyadhToday, []);

  useEffect(() => { getValuationCatalog().then(c => { setMethods(c.methods); setPropertyTypes(c.property_types); }).catch(e => setError(e.message)); }, []);
  useEffect(() => { const set = () => { setViewportWidth(window.innerWidth); setNarrow(window.innerWidth < 768); };
    set(); window.addEventListener("resize", set); return () => window.removeEventListener("resize", set); }, []);
  // Below 1280 px the filter drawer floats over the map instead of taking width from it.
  const compact = viewportWidth < 1280;
  const leftOpen = compact ? overlayLeft : ws.panels.left;
  const setLeftOpen = (open: boolean) => compact ? setOverlayLeft(open) : setPanels({ left: open });
  useEffect(() => { const on = () => setFullscreen(!!document.fullscreenElement); document.addEventListener("fullscreenchange", on); return () => document.removeEventListener("fullscreenchange", on); }, []);

  // Filter changes load once. Only when the result is truncated do camera moves issue bounded viewport queries.
  const f = ws.filters;
  const baseQuery = useMemo(() => ({ q: f.q, city: f.city, property_type: f.type, date_from: f.from, date_to: f.to, case_id: caseId, limit: String(LIMIT) }), [f.q, f.city, f.type, f.from, f.to, caseId]);
  const [viewportMode, setViewportMode] = useState(false);
  const bboxKey = viewportMode && bounds ? [bounds.south, bounds.west, bounds.north, bounds.east].map(n => n.toFixed(3)).join(",") : "";
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true); setError("");
      const [south, west, north, east] = bboxKey ? bboxKey.split(",") : [];
      getMapRecords({ ...baseQuery, ...(bboxKey ? { south, west, north, east } : {}) }, { signal: controller.signal })
        .then(r => { setData(r); if (!bboxKey && r.truncated) setViewportMode(true); })
        .catch(e => { if ((e as Error).name !== "AbortError") setError((e as Error).message); })
        .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, bboxKey ? 350 : 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [baseQuery, bboxKey, reload]);
  useEffect(() => { setViewportMode(false); setGroup([]); }, [baseQuery]);

  // The analysis property supplies the subject, its coordinate provenance and any saved outline.
  const [propertyRevision, setPropertyRevision] = useState<number | null>(null); const [geometrySaves, setGeometrySaves] = useState(0);
  useEffect(() => {
    if (!analysisId) { setPrepared(null); setPropertyRevision(null); return; }
    let current = true;
    getProperty(analysisId).then(p => { if (!current) return; setPropertyRevision(p.revision);
      const loc = p.property.location as Record<string, unknown>;
      const outline = loc.site_outline as GeoJSONPolygon | undefined;
      update(s => ({ siteOutline: outline?.coordinates ? latLngsFromPolygon(outline) : s.siteOutline,
        subject: typeof loc.latitude === "number" && typeof loc.longitude === "number" ? { coordinates: [loc.latitude, loc.longitude],
          source: (loc.coordinate_source as Subject["source"]) || "map_pin", precision: (loc.coordinate_precision as Subject["precision"]) || "user_selected", confirmed: true, label: p.property.name } : s.subject }));
    }).catch(e => setError(e.message));
    return () => { current = false; };
  }, [analysisId, update]);
  const onPrepared = useCallback((p: PreparedAnalysis) => { setPrepared(p); update({ subjectType: p.property_type, approach: p.method }); }, [update]);
  const analysisUrl = useCallback((id: string | null) => { const next = new URLSearchParams(window.location.search); if (id) next.set("analysis", id); else next.delete("analysis");
    router.replace(`/map${next.toString() ? "?" + next : ""}`, { scroll: false }); }, [router]);

  // Derived evidence scopes. Every count says which scope it describes.
  const all = useMemo(() => data?.data || [], [data]);
  const layered = useMemo(() => applyEvidenceFilters(all.filter(r => ws.layers[r.kind] !== false),
    { statuses: f.statuses, sources: f.sources, precisions: f.precisions, minReliability: f.minReliability }), [all, ws.layers, f.statuses, f.sources, f.precisions, f.minReliability]);
  const located = useMemo(() => layered.filter(r => r.coordinates), [layered]);
  const unlocated = useMemo(() => layered.filter(r => !r.coordinates), [layered]);
  const inView = useMemo(() => located.filter(r => inBounds(r.coordinates, bounds)), [located, bounds]);
  const evidenceRing: SearchArea | null = ws.searchArea ?? (prepared?.coordinates ? { kind: "radius", center: prepared.coordinates, radius_m: prepared.radius_km * 1000 } : null);
  const listed = useMemo(() => layered.filter(r => (!f.withinView || inBounds(r.coordinates, bounds)) && (!ws.filterToArea || !ws.searchArea || inSearchArea(r.coordinates, ws.searchArea))
    && (!group.length || group.includes(r.id))), [layered, f.withinView, bounds, ws.filterToArea, ws.searchArea, group]);
  const facets = useMemo(() => facetValues(all), [all]);
  const selected = all.find(r => r.id === ws.selectedId) || null;
  const subjectPoint = ws.subject?.coordinates || null;
  const caps = status?.capabilities;
  const scopeLabel = group.length ? "map cluster" : ws.filterToArea && ws.searchArea ? "search area" : f.withinView ? "map view" : "all loaded records";

  const select = useCallback((id: string) => { update(s => ({ selectedId: id, panels: { ...s.panels, right: true, tab: s.panels.tab === "valuation" ? "valuation" : "evidence" } })); }, [update]);
  const selectRecord = useCallback((r: MapRecord) => { select(r.id); if (r.coordinates && !inBounds(r.coordinates, bounds)) handle.current?.fit([r.coordinates], 17); }, [select, bounds]);
  const setSubject = useCallback((s: Subject | null) => { update({ subject: s }); setPrepared(null); if (analysisId) analysisUrl(null); }, [update, analysisId, analysisUrl]);

  const onMapClick = useCallback((p: LatLng) => {
    if (tool === "place_subject") { setSubject({ coordinates: p, source: "map_pin", precision: "user_selected", confirmed: false }); setTool("browse"); update(s => ({ panels: { ...s.panels, right: true, tab: "subject" } })); }
    else if (tool === "draw_area" || tool === "draw_site" || tool === "measure") setDraft(d => ({ tool, points: [...(d?.tool === tool ? d.points : []), p] }));
  }, [tool, setSubject, update]);
  const onCamera = useCallback((camera: Camera, b: MapBounds) => { setBounds(b); update({ camera }); }, [update]);
  const onStatus = useCallback((s: MapStatus & { fallbackReason: string | null }) => setStatus(s), []);
  const onAreaEdit = useCallback((a: SearchArea) => update({ searchArea: a }), [update]);
  const onSubjectMove = useCallback((p: LatLng) => update(s => ({ subject: s.subject ? { ...s.subject, coordinates: p, source: "map_pin", precision: "user_selected", confirmed: false } : null })), [update]);

  function startTool(next: MapTool) {
    if (tool === next) { setTool("browse"); setDraft(null); return; }
    setTool(next); setEditArea(false); setDraft(next === "draw_area" || next === "draw_site" || next === "measure" ? { tool: next, points: [] } : null);
    if (next === "measure") setMeasure(null);
  }
  const finishDraft = useCallback(() => {
    if (!draft) return;
    if (draft.tool === "measure") { setMeasure(draft.points); setDraft(null); setTool("browse"); return; }
    if (draft.points.length < 3) { setNotice("An area needs at least three points."); return; }
    if (draft.tool === "draw_area") update({ searchArea: { kind: "polygon", ring: draft.points }, filterToArea: true });
    else update({ siteOutline: draft.points });
    setDraft(null); setTool("browse");
  }, [draft, update]);
  const addCentreVertex = () => { const c = handle.current?.center(); if (c) onMapClick(c); };
  useEffect(() => {
    if (tool === "browse") return;
    const key = (e: KeyboardEvent) => { const t = e.target as HTMLElement; if (/INPUT|TEXTAREA|SELECT/.test(t.tagName)) return;
      if (e.key === "Escape") { setTool("browse"); setDraft(null); }
      else if (e.key === "Enter" && draft) { e.preventDefault(); finishDraft(); }
      else if (e.key === "Backspace" && draft) { e.preventDefault(); setDraft(d => d && { ...d, points: d.points.slice(0, -1) }); } };
    window.addEventListener("keydown", key); return () => window.removeEventListener("keydown", key);
  }, [tool, draft, finishDraft]);

  function radiusAroundSubject() {
    const center = subjectPoint || handle.current?.center(); if (!center) return;
    update({ searchArea: { kind: "radius", center, radius_m: prepared ? prepared.radius_km * 1000 : 1000 }, filterToArea: true }); setEditArea(true); setTool("browse"); setDraft(null);
  }
  function fitEvidence() { const pts = (group.length ? located.filter(r => group.includes(r.id)) : located).map(r => r.coordinates as LatLng); if (pts.length) handle.current?.fit(pts, 16); else setNotice("No located records to fit for the current filters."); }
  function fitSubject() { const pts = [...(subjectPoint ? [subjectPoint] : []), ...areaPoints(evidenceRing), ...(ws.siteOutline || [])]; if (pts.length) handle.current?.fit(pts, 18); else setNotice("Place or select a subject first."); }
  async function streetView() { const at = subjectPoint || handle.current?.center(); if (!at || !handle.current) return; const r = await handle.current.streetView(at); setNotice(r.message); }
  function toggleFullscreen() { if (document.fullscreenElement) document.exitFullscreen(); else root.current?.requestFullscreen?.().catch(() => setNotice("Fullscreen is not available in this browser.")); }
  function capability(name: "rotate" | "tilt", ok: boolean) { if (!ok) setNotice(name === "rotate" ? "Rotation needs a Google vector map (configure a vector Map ID)." : "Tilt is unavailable for this basemap/rendering type. Google retired automatic 45° imagery in May 2026; 3D maps are not integrated."); }

  async function start() {
    if (!ws.subject?.confirmed || !ws.subjectType || !ws.approach) return;
    setStarting(true); setError("");
    try {
      const p = await startMapAnalysis({ latitude: ws.subject.coordinates[0], longitude: ws.subject.coordinates[1], property_type: ws.subjectType, method: ws.approach,
        coordinate_source: ws.subject.source, coordinate_precision: ws.subject.precision, ...(f.city ? { city: f.city } : {}) });
      onPrepared(p); analysisUrl(p.property_id); update(s => ({ panels: { ...s.panels, right: true, tab: "valuation" } })); setReload(n => n + 1);
    } catch (e) { setError((e as Error).message); } finally { setStarting(false); }
  }
  async function saveOutline() {
    if (!analysisId || !ws.siteOutline) return;
    setSavingOutline(true); setError("");
    try {
      const p = await getProperty(analysisId);
      const outline = { ...polygonFromLatLngs(ws.siteOutline), source: "user_drawn", cadastral: false, drawn_on: today, basemap: status?.provider === "google" ? ws.basemap : "roadmap_fallback",
        approximate_area_sqm: Math.round(geodesicAreaSqm(ws.siteOutline)) };
      const saved = await saveProperty(analysisId, { ...p.property, location: { ...p.property.location, site_outline: outline } }, p.revision, "Site outline drawn on map (approximate; not a cadastral boundary)");
      setPropertyRevision(saved.revision); setGeometrySaves(n => n + 1); setNotice("Site outline saved to the property with user-drawn provenance."); setReload(n => n + 1);
    } catch (e) { setError((e as Error).message); } finally { setSavingOutline(false); }
  }
  const openProperty = useCallback((r: MapRecord) => { analysisUrl(r.entity_id); update(s => ({ panels: { ...s.panels, right: true, tab: "valuation" } })); }, [analysisUrl, update]);
  const onGeocoded = (g: GeocodeResult) => { setSubject({ coordinates: g.coordinates, source: "geocoded", precision: g.precision, confirmed: false, label: g.label }); handle.current?.fit([g.coordinates], 18); update(s => ({ panels: { ...s.panels, right: true, tab: "subject" } })); };
  const onCoordinates = (p: LatLng) => { setSubject({ coordinates: p, source: "coordinate_entry", precision: "user_selected", confirmed: false }); handle.current?.fit([p], 18); update(s => ({ panels: { ...s.panels, right: true, tab: "subject" } })); };
  useEffect(() => { if (!notice) return; const t = setTimeout(() => setNotice(""), 7000); return () => clearTimeout(t); }, [notice]);

  const stage = !ws.subject ? 0 : !ws.subjectType ? 1 : !analysisId ? 2 : !prepared?.ready ? 3 : 4;
  const draftMeasure = draft?.tool === "measure" ? pathLengthMeters(draft.points) : draft && draft.points.length >= 3 ? geodesicAreaSqm(draft.points) : null;
  const setFilter = (patch: Partial<WorkspaceState["filters"]>) => update(s => ({ filters: { ...s.filters, ...patch } }));
  const setPanels = (patch: Partial<WorkspaceState["panels"]>) => update(s => ({ panels: { ...s.panels, ...patch } }));
  const recent = (days: number) => { const start = new Date(`${today}T12:00:00Z`); start.setUTCDate(start.getUTCDate() - days); setFilter({ to: today, from: start.toISOString().slice(0, 10) }); };
  const basemapAvailable = (b: Basemap) => !!caps?.[b];
  const rightWidth = narrow ? undefined : Math.min(ws.panels.rightWidth, Math.max(300, Math.round(viewportWidth * 0.36)));
  const startResize = (e: React.PointerEvent) => { const startX = e.clientX; const startW = ws.panels.rightWidth;
    const move = (ev: PointerEvent) => setPanels({ rightWidth: Math.max(320, Math.min(760, startW + startX - ev.clientX)) });
    const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up); };

  return <div ref={root} className="flex flex-col h-full bg-slate-100">
    {/* Slim header: search, workflow stage, essential actions. */}
    <header className="h-12 shrink-0 flex items-center gap-3 px-3 bg-white border-b border-slate-200">
      <h1 className="text-sm font-semibold whitespace-nowrap hidden md:block">Property map <span className="text-slate-400 font-normal" lang="ar" dir="rtl">الخريطة العقارية</span></h1>
      <MapSearch records={all} geocodingAvailable={!!caps?.geocoding} geocodingNote={status?.provider === "google" ? "Address search is loading." : "Address search needs the Google provider (Geocoding API). Enter latitude, longitude instead."}
        geocode={q => handle.current ? handle.current.geocode(q) : Promise.resolve([])} onCoordinates={onCoordinates} onRecord={selectRecord} onGeocoded={onGeocoded} />
      <ol className="hidden xl:flex items-center gap-1 text-[11px] text-slate-500" aria-label="Workflow stage">{STAGES.map((s, i) =>
        <li key={s} className={`flex items-center gap-1 px-1.5 py-0.5 rounded ${i === stage ? "bg-blue-50 text-blue-800 font-medium" : i < stage ? "text-slate-700" : ""}`} aria-current={i === stage ? "step" : undefined}>
          {i < stage ? <Check size={11} /> : <span className="w-3 text-center">{i + 1}</span>}{s}</li>)}</ol>
      <div className="ml-auto flex items-center gap-2 text-xs">
        {ws.subject?.label && <span className="hidden lg:inline max-w-[220px] truncate text-slate-600" title={ws.subject.label}>{ws.subject.label}</span>}
        <Link className="text-blue-700 whitespace-nowrap" href="/properties">Properties →</Link></div>
    </header>
    {caseId && <p className="text-xs text-blue-800 bg-blue-50 px-3 py-1 border-b border-blue-100">Showing this case&apos;s comparables and linked properties. <Link href="/map" className="underline">Show all cases</Link></p>}

    <div className={`relative flex-1 min-h-0 flex ${narrow ? "flex-col overflow-y-auto" : "flex-row"}`}>
      {/* Left layers/filters drawer. */}
      {leftOpen && <aside className={`${compact ? "absolute z-[1100] top-0 left-0 bottom-0 shadow-xl" : "relative"} w-64 shrink-0 bg-white border-r border-slate-200 overflow-y-auto text-xs`} aria-label="Layers and filters">
        <div className="flex items-center justify-between px-3 h-9 border-b border-slate-100"><h2 className="font-semibold text-slate-700 flex items-center gap-1.5"><Layers size={13} />Layers & filters</h2>
          <button type="button" className="text-slate-400 hover:text-slate-700" aria-label="Collapse layers panel" onClick={() => setLeftOpen(false)}><PanelLeftClose size={15} /></button></div>
        <fieldset className="px-3 py-2 space-y-1"><legend className="sr-only">Evidence layers</legend>
          {LAYERS.map(l => { const total = all.filter(r => r.kind === l.key).length; const pinned = all.filter(r => r.kind === l.key && r.coordinates).length;
            return <label key={l.key} className="flex items-center gap-2 py-0.5" title={l.description}><input type="checkbox" checked={ws.layers[l.key] !== false} onChange={e => update(s => ({ layers: { ...s.layers, [l.key]: e.target.checked } }))} />
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: l.color }} /><span className="flex-1">{l.label}</span><span className="text-slate-400 tabular-nums" title={`${pinned} located of ${total} loaded`}>{pinned}/{total}</span></label>; })}
          <details className="pt-1"><summary className="text-slate-500 cursor-pointer">Unavailable layers ({UNAVAILABLE_LAYERS.length})</summary>
            <ul className="mt-1 space-y-1">{UNAVAILABLE_LAYERS.map(u => <li key={u.label} className="text-slate-400"><input type="checkbox" disabled aria-label={u.label} className="mr-2" />{u.label}<span className="block pl-5 text-[10px]">{u.reason}</span></li>)}</ul></details>
        </fieldset>
        <div className="px-3 py-2 border-t border-slate-100 space-y-2">
          <label className="block">Text<input className="mizan-compact-input mt-0.5" type="search" value={f.q} onChange={e => setFilter({ q: e.target.value })} placeholder="Name, district, source…" /></label>
          <label className="block">City<select className="mizan-compact-input mt-0.5" value={f.city} onChange={e => setFilter({ city: e.target.value })}><option value="">All cities</option>{data?.available.cities.map(c => <option key={c}>{c}</option>)}</select></label>
          <label className="block">Property type<select className="mizan-compact-input mt-0.5" value={f.type} onChange={e => setFilter({ type: e.target.value })}><option value="">All types</option>{data?.available.property_types.map(t => <option key={t}>{t}</option>)}</select></label>
          <div className="grid grid-cols-2 gap-2"><label>From<input className="mizan-compact-input mt-0.5" type="date" value={f.from} onChange={e => setFilter({ from: e.target.value })} /></label>
            <label>To<input className="mizan-compact-input mt-0.5" type="date" value={f.to} onChange={e => setFilter({ to: e.target.value })} /></label></div>
          <div className="flex flex-wrap gap-x-2 text-blue-700">{[30, 90, 365].map(d => <button type="button" key={d} onClick={() => recent(d)}>{d}d</button>)}<button type="button" onClick={() => setFilter({ from: "", to: "" })}>All dates</button></div>
          <p className="text-[10px] text-slate-500">Dates use transaction, listing, observation or collection date. Undated records drop out when a period is set. Invalid/outlier comparables are excluded.</p>
          {(["statuses", "sources", "precisions"] as const).map(key => facets[key].length > 0 && <details key={key}><summary className="cursor-pointer text-slate-600">{key === "statuses" ? "Status" : key === "sources" ? "Source" : "Location precision"}{f[key].length ? ` (${f[key].length})` : ""}</summary>
            <div className="mt-1 space-y-0.5 max-h-36 overflow-auto">{facets[key].map(([v, n]) => <label key={v} className="flex items-center gap-2"><input type="checkbox" checked={f[key].includes(v)} onChange={e => setFilter({ [key]: e.target.checked ? [...f[key], v] : f[key].filter(x => x !== v) })} />
              <span className="flex-1 truncate" title={v}>{key === "precisions" ? precisionLabel(v) : v}</span><span className="text-slate-400">{n}</span></label>)}</div></details>)}
          <label className="block">Minimum source reliability<select className="mizan-compact-input mt-0.5" value={f.minReliability ?? ""} onChange={e => setFilter({ minReliability: e.target.value ? Number(e.target.value) : null })}>
            <option value="">Any (including unscored)</option>{[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}/5 or better (scored only)</option>)}</select></label>
        </div>
      </aside>}

      {/* Central map canvas. */}
      <section className={`relative flex-1 min-w-0 flex flex-col ${narrow ? "min-h-[58vh]" : ""}`} aria-label="Map workspace">
        <div className="relative flex-1 min-h-[320px] bg-slate-300">
          {hydrated && <MapCanvas handle={handle} records={located} selectedId={ws.selectedId} groupIds={group} basemap={ws.basemap} initialCamera={ws.camera}
            subject={ws.subject} subjectDraggable={!analysisId && !!ws.subject && !ws.subject.confirmed} searchArea={evidenceRing} editArea={editArea && !!ws.searchArea}
            siteOutline={ws.siteOutline} tool={tool} draft={draft ?? (measure ? { tool: "measure", points: measure } : null)}
            onCamera={onCamera} onSelect={select} onGroup={setGroup} onMapClick={onMapClick} onSubjectMove={onSubjectMove} onAreaEdit={onAreaEdit} onStatus={onStatus} />}

          {/* Top-left: panels + basemap. */}
          <div className="absolute top-2 left-2 z-[1000] flex flex-wrap items-center gap-1.5">
            {!leftOpen && <button type="button" className="mizan-tool" aria-label="Show layers and filters" title="Layers & filters" onClick={() => setLeftOpen(true)}><PanelLeftOpen size={15} /></button>}
            <div role="radiogroup" aria-label="Basemap" className="flex rounded border border-slate-300 bg-white/95 shadow-sm overflow-x-auto max-w-[calc(100vw-9rem)]">
              {BASEMAPS.map(b => <button key={b.key} type="button" role="radio" aria-checked={ws.basemap === b.key} disabled={!basemapAvailable(b.key) && b.key !== "roadmap"}
                title={basemapAvailable(b.key) ? b.label : `${b.label} imagery requires the Google provider`} onClick={() => update({ basemap: b.key })}
                className={`px-2 sm:px-2.5 h-8 text-xs font-medium whitespace-nowrap disabled:text-slate-300 disabled:cursor-not-allowed ${ws.basemap === b.key && basemapAvailable(b.key) ? "bg-blue-700 text-white" : "text-slate-700 hover:bg-slate-50"}`}>{b.label}</button>)}
            </div>
          </div>

          {/* Top-right: tools and camera controls. */}
          <div className="absolute top-2 right-2 bottom-6 z-[1000] flex flex-col gap-1 overflow-y-auto pr-0.5" role="toolbar" aria-label="Map tools" aria-orientation="vertical">
            {!ws.panels.right && !narrow && <button type="button" className="mizan-tool" aria-label="Show inspector" title="Show inspector" onClick={() => setPanels({ right: true })}><PanelRightOpen size={15} /></button>}
            <button type="button" className="mizan-tool" aria-pressed={tool === "browse"} title="Browse / select" aria-label="Browse and select" onClick={() => { setTool("browse"); setDraft(null); }}><MousePointer2 size={15} /></button>
            <button type="button" className="mizan-tool" aria-pressed={tool === "place_subject"} disabled={!!analysisId} title={analysisId ? "Start a new subject to move the pin" : "Place subject pin"} aria-label="Place subject pin" onClick={() => startTool("place_subject")}><Crosshair size={15} /></button>
            <button type="button" className="mizan-tool" aria-pressed={tool === "draw_area"} title="Draw search polygon" aria-label="Draw search polygon" onClick={() => startTool("draw_area")}><Hexagon size={15} /></button>
            <button type="button" className="mizan-tool" title="Search radius around subject" aria-label="Search radius around subject" onClick={radiusAroundSubject}><Circle size={15} /></button>
            <button type="button" className="mizan-tool" aria-pressed={tool === "draw_site"} title="Draw approximate site outline" aria-label="Draw approximate site outline" onClick={() => startTool("draw_site")}><Square size={15} /></button>
            <button type="button" className="mizan-tool" aria-pressed={tool === "measure"} title="Measure distance" aria-label="Measure distance" onClick={() => startTool("measure")}><Ruler size={15} /></button>
            <span className="h-1" />
            <button type="button" className="mizan-tool" title="Fit subject" aria-label="Fit subject" onClick={fitSubject}><LocateFixed size={15} /></button>
            <button type="button" className="mizan-tool text-[10px]" title="Fit evidence" aria-label="Fit evidence" onClick={fitEvidence}>Fit</button>
            <button type="button" className="mizan-tool" title="Reset north and tilt" aria-label="Reset north and tilt" onClick={() => handle.current?.resetNorth()}><Compass size={15} /></button>
            <button type="button" className="mizan-tool" disabled={!caps?.rotate} title={caps?.rotate ? "Rotate left" : "Rotation needs a Google vector map"} aria-label="Rotate left" onClick={() => capability("rotate", !!handle.current?.rotate(-30))}><RotateCcw size={15} /></button>
            <button type="button" className="mizan-tool" disabled={!caps?.rotate} title={caps?.rotate ? "Rotate right" : "Rotation needs a Google vector map"} aria-label="Rotate right" onClick={() => capability("rotate", !!handle.current?.rotate(30))}><RotateCw size={15} /></button>
            <button type="button" className="mizan-tool text-[10px]" disabled={!caps?.tilt} title={caps?.tilt ? "Tilt 45°" : "Tilt unavailable for this rendering"} aria-label="Tilt view" onClick={() => capability("tilt", !!handle.current?.tilt(45))}>3D</button>
            <button type="button" className="mizan-tool" disabled={!caps?.streetView} title={caps?.streetView ? "Street View at subject (if covered)" : "Street View requires the Google provider"} aria-label="Street View" onClick={streetView}><ScanEye size={15} /></button>
            <button type="button" className="mizan-tool" title={fullscreen ? "Exit fullscreen" : "Fullscreen"} aria-label={fullscreen ? "Exit fullscreen" : "Fullscreen"} onClick={toggleFullscreen}>{fullscreen ? <Shrink size={15} /> : <Expand size={15} />}</button>
            <button type="button" className="mizan-tool" aria-pressed={ws.panels.table} title="Evidence table" aria-label="Toggle evidence table" onClick={() => setPanels({ table: !ws.panels.table })}><Table2 size={15} /></button>
          </div>

          {/* Provider status: fallback is always labelled. */}
          {status?.fallbackReason && <details role="status" open={!narrow} className="absolute top-12 left-2 z-[1000] max-w-[min(560px,calc(100%-4rem))] rounded border border-amber-300 bg-amber-50/95 px-3 py-1.5 text-[11px] text-amber-900 shadow-sm">
            <summary className="font-semibold cursor-pointer">Road-map fallback · no satellite imagery</summary>{status.fallbackReason}</details>}
          {status?.state === "error" && status.provider === "leaflet" && <div role="alert" className="absolute top-24 left-2 z-[1000] rounded border border-red-300 bg-white px-3 py-1.5 text-[11px] text-red-800">{status.message}</div>}

          {/* Drawing / measuring bar with keyboard alternatives. */}
          {(draft || measure || tool === "place_subject") && <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[1000] flex flex-wrap items-center gap-2 rounded border border-slate-300 bg-white/95 px-3 py-1.5 text-xs shadow" role="status" aria-live="polite">
            {tool === "place_subject" && <span>Click the map to place the subject, or type coordinates in the search box. Esc cancels.</span>}
            {draft && <><span className="font-medium">{draft.tool === "measure" ? "Measure" : draft.tool === "draw_area" ? "Search polygon" : "Site outline"} · {draft.points.length} points</span>
              {draftMeasure != null && <span>≈ {draft.tool === "measure" ? formatDistance(draftMeasure) : formatArea(draftMeasure)} <span className="text-slate-400">(approximate geodesic)</span></span>}
              <button type="button" className="text-blue-700 underline" onClick={addCentreVertex}>Add point at map centre</button>
              <button type="button" className="text-blue-700 underline disabled:text-slate-300" disabled={!draft.points.length} onClick={() => setDraft(d => d && { ...d, points: d.points.slice(0, -1) })}>Undo (⌫)</button>
              <button type="button" className="mizan-button !py-0.5 !px-2 !text-xs" disabled={draft.tool === "measure" ? draft.points.length < 2 : draft.points.length < 3} onClick={finishDraft}>Finish (↵)</button>
              <button type="button" className="text-slate-600 underline" onClick={() => { setDraft(null); setTool("browse"); }}>Cancel (Esc)</button></>}
            {!draft && measure && <><span>Distance ≈ {formatDistance(pathLengthMeters(measure))} <span className="text-slate-400">(approximate geodesic, {measure.length} points)</span></span>
              <button type="button" className="text-slate-600 underline" onClick={() => setMeasure(null)}>Clear</button></>}
          </div>}
          {notice && <div role="status" className="absolute bottom-20 left-1/2 -translate-x-1/2 z-[1000] max-w-md rounded bg-slate-900/90 px-3 py-1.5 text-xs text-white">{notice}</div>}

          {/* Bottom-left scope counts. */}
          <div className="absolute bottom-6 left-2 z-[900] rounded border border-slate-200 bg-white/95 px-2.5 py-1.5 text-[11px] text-slate-700 shadow-sm max-w-[min(420px,calc(100%-1rem))]" aria-live="polite">
            <p><strong>{data?.matching_filters ?? data?.total ?? 0}</strong> match filters · <strong>{all.length}</strong> loaded · <strong>{located.length}</strong> pinned · <strong>{inView.length}</strong> in view · <strong>{unlocated.length}</strong> without location</p>
            {data?.truncated && <p className="text-amber-800">Showing {data.returned ?? all.length} of {data.total} {data.bbox ? "in this view" : "matches"}; {viewportMode ? "loading by viewport as you move." : "refine filters."}</p>}
            {loading && <p className="text-slate-500">Updating evidence…</p>}
            {error && <p className="text-red-700" role="alert">{error}</p>}
            {status?.imageryNote && <p className="text-slate-500">{status.imageryNote}</p>}
          </div>
        </div>
        {ws.panels.table && <div className="h-56 shrink-0 border-t border-slate-300 bg-white" aria-label="Evidence table">
          <EvidenceTable records={listed} selectedId={ws.selectedId} onSelect={selectRecord} subject={subjectPoint} /></div>}
      </section>

      {/* Right inspector: resizable on desktop, bottom sheet on narrow screens. */}
      {(ws.panels.right || narrow) && <>
        {!narrow && <div role="separator" aria-orientation="vertical" aria-label="Resize inspector" tabIndex={0} className="w-1 cursor-col-resize bg-slate-200 hover:bg-blue-300 focus:bg-blue-400 outline-none"
          onPointerDown={startResize} onKeyDown={e => { if (e.key === "ArrowLeft") setPanels({ rightWidth: Math.min(760, ws.panels.rightWidth + 20) }); if (e.key === "ArrowRight") setPanels({ rightWidth: Math.max(320, ws.panels.rightWidth - 20) }); }} />}
        <aside style={{ width: rightWidth }} className={`${narrow ? "h-[46vh] border-t" : "border-l"} shrink-0 bg-white border-slate-200 flex flex-col min-h-0`} aria-label="Inspector">
          <div className="flex items-center border-b border-slate-200 px-1" role="tablist" aria-label="Inspector sections">
            {(["evidence", "subject", "valuation", "coverage"] as InspectorTab[]).map(t => <button key={t} type="button" role="tab" id={`tab-${t}`} aria-controls={`panel-${t}`} aria-selected={ws.panels.tab === t} className="mizan-tab capitalize" onClick={() => setPanels({ tab: t })}>
              {t}{t === "evidence" ? ` (${listed.length})` : t === "coverage" ? ` (${unlocated.length})` : ""}</button>)}
            {!narrow && <button type="button" className="ml-auto p-2 text-slate-400 hover:text-slate-700" aria-label="Collapse inspector" onClick={() => setPanels({ right: false })}><PanelRightClose size={15} /></button>}
          </div>
          {selected && <SelectedRecord record={selected} subject={subjectPoint} onClear={() => update({ selectedId: null })} onUseAsSubject={openProperty} />}
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div role="tabpanel" id="panel-evidence" aria-labelledby="tab-evidence" hidden={ws.panels.tab !== "evidence"}>
              <div className="flex flex-wrap gap-x-4 gap-y-1 px-4 py-2 text-xs border-b border-slate-100">
                <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.withinView} onChange={e => setFilter({ withinView: e.target.checked })} />Only in map view</label>
                <label className={`flex items-center gap-1.5 ${ws.searchArea ? "" : "text-slate-400"}`}><input type="checkbox" disabled={!ws.searchArea} checked={ws.filterToArea && !!ws.searchArea} onChange={e => update({ filterToArea: e.target.checked })} />Only in search area</label></div>
              <EvidenceSummary records={listed} scopeLabel={scopeLabel} today={today} />
              <EvidenceList records={listed} selectedId={ws.selectedId} onSelect={selectRecord} subject={subjectPoint} groupActive={group.length > 0} onClearGroup={() => setGroup([])} />
            </div>
            <div role="tabpanel" id="panel-subject" aria-labelledby="tab-subject" hidden={ws.panels.tab !== "subject"} className="px-4 py-3 space-y-4 text-xs">
              <section><h3 className="font-semibold text-slate-700 mb-1">1 · Subject location</h3>
                {ws.subject ? <><p className="font-mono text-[12px]">{ws.subject.coordinates.map(n => n.toFixed(6)).join(", ")} <span className="font-sans text-slate-400">(lat, lng)</span></p>
                  <p className="text-slate-500">{ws.subject.source.replaceAll("_", " ")} · {precisionLabel(ws.subject.precision)}{ws.subject.label ? ` · ${ws.subject.label}` : ""}</p>
                  {!ws.subject.confirmed && !analysisId && <div className="mt-2 rounded border border-amber-200 bg-amber-50 p-2"><p className="text-amber-900">Check the pin against the imagery. Drag it or focus it and use arrow keys (Shift for larger steps).</p>
                    <button type="button" className="mizan-button !py-1 !px-3 !text-xs mt-2" onClick={() => update(s => ({ subject: s.subject && { ...s.subject, confirmed: true } }))}>Confirm subject location</button></div>}
                  {ws.subject.confirmed && <p className="text-green-700 mt-1 flex items-center gap-1"><Check size={12} />Confirmed</p>}
                  {!analysisId && <button type="button" className="text-blue-700 underline mt-1" onClick={() => setSubject(null)}>Clear subject</button>}</>
                  : <p className="text-slate-500">Use <Crosshair size={11} className="inline" /> to place a pin, type coordinates or an address in the search box, or pick a saved property below.</p>}
              </section>
              <section className="grid grid-cols-1 gap-2">
                <label className="block font-semibold text-slate-700">2 · Property type<select className="mizan-compact-input mt-1 font-normal" value={ws.subjectType} disabled={!!analysisId} onChange={e => update({ subjectType: e.target.value })}>
                  <option value="">Choose property type</option>{propertyTypes.map(t => <option key={t} value={t}>{t.replaceAll("_", " ")}</option>)}</select></label>
                <label className="block font-semibold text-slate-700">3 · Valuation approach<select className="mizan-compact-input mt-1 font-normal" value={ws.approach} disabled={!!analysisId} onChange={e => update({ approach: e.target.value })}>
                  {methods.map(m => <option key={m.key} value={m.key} disabled={!m.implemented}>{m.label}{m.implemented ? "" : " · not yet implemented"}</option>)}</select></label>
                {methods.find(m => m.key === ws.approach) && <p className="text-slate-500">{methods.find(m => m.key === ws.approach)!.description} Required inputs: {methods.find(m => m.key === ws.approach)!.fields.map(x => x.label).join(", ") || "evidence only"}.</p>}
                {analysisId ? <p className="text-slate-600">Analysis open in the Valuation tab. <button type="button" className="text-blue-700 underline" onClick={() => { analysisUrl(null); setPrepared(null); update({ subject: null, siteOutline: null }); setTool("place_subject"); }}>Start a new subject</button></p>
                  : <button type="button" className="mizan-button" disabled={starting || !ws.subject?.confirmed || !ws.subjectType} onClick={start}>{starting ? "Preparing…" : "Start valuation"}</button>}
                {!analysisId && ws.subject && !ws.subject.confirmed && <p className="text-amber-800">Confirm the subject location first.</p>}
              </section>
              <section><h3 className="font-semibold text-slate-700 mb-1">Search area</h3>
                {ws.searchArea ? <><p>{ws.searchArea.kind === "radius" ? `Radius ≈ ${formatDistance(ws.searchArea.radius_m)}` : `Polygon · ${ws.searchArea.ring.length} vertices · ≈ ${formatArea(geodesicAreaSqm(ws.searchArea.ring))}`} <span className="text-slate-400">(approximate)</span></p>
                  {ws.searchArea.kind === "radius" && <label className="flex items-center gap-2 mt-1">Radius (m)<input type="number" min={10} max={50000} step={50} className="mizan-compact-input !w-28" value={Math.round(ws.searchArea.radius_m)}
                    onChange={e => { const v = Number(e.target.value); if (v >= 10 && v <= 50000) update(s => ({ searchArea: s.searchArea?.kind === "radius" ? { ...s.searchArea, radius_m: v } : s.searchArea })); }} /></label>}
                  <div className="flex gap-3 mt-1"><button type="button" className="text-blue-700 underline" onClick={() => setEditArea(v => !v)}>{editArea ? "Stop editing" : "Edit on map"}</button>
                    <button type="button" className="text-blue-700 underline" onClick={() => { update({ searchArea: null, filterToArea: false }); setEditArea(false); }}>Remove</button></div>
                  <p className="text-slate-500 mt-1">Filters the evidence list on the map only. The valuation&apos;s evidence radius is set in the Valuation tab.</p></>
                  : <p className="text-slate-500">{prepared ? `Showing the valuation evidence radius (${prepared.radius_km} km). ` : ""}Draw a polygon <Hexagon size={11} className="inline" /> or radius <Circle size={11} className="inline" /> to filter evidence.</p>}
              </section>
              <section><h3 className="font-semibold text-slate-700 mb-1">Site outline</h3>
                {ws.siteOutline ? <><p>{ws.siteOutline.length} vertices · ≈ {formatArea(geodesicAreaSqm(ws.siteOutline))} · perimeter ≈ {formatDistance(pathLengthMeters([...ws.siteOutline, ws.siteOutline[0]]))}</p>
                  <p className="text-amber-800 mt-1">User-drawn on imagery. Approximate; not a certified cadastral, title-deed or municipal boundary.</p>
                  <div className="flex gap-3 mt-1">{analysisId && <button type="button" className="text-blue-700 underline disabled:opacity-50" disabled={savingOutline || propertyRevision == null} onClick={saveOutline}>{savingOutline ? "Saving…" : "Save to property"}</button>}
                    <button type="button" className="text-blue-700 underline" onClick={() => update({ siteOutline: null })}>Remove from map</button></div>
                  {!analysisId && <p className="text-slate-500 mt-1">Start or open an analysis to save the outline with the property.</p>}</>
                  : <p className="text-slate-500">Optional. Use <Square size={11} className="inline" /> to trace the visible site for approximate area.</p>}
              </section>
              <section><h3 className="font-semibold text-slate-700 mb-1">Saved properties</h3>
                <ul className="divide-y divide-slate-100 border border-slate-200 rounded max-h-48 overflow-auto">{all.filter(r => r.kind === "property").map(r => <li key={r.id} className="flex items-center gap-2 px-2 py-1.5">
                  <button type="button" className="flex-1 text-left hover:underline" onClick={() => selectRecord(r)}>{r.title}<span className="block text-[11px] text-slate-500">{r.coordinates ? precisionLabel(r.location_precision) : "No location"}{r.has_site_outline ? " · outline saved" : ""}</span></button>
                  <button type="button" className="text-blue-700 underline whitespace-nowrap" onClick={() => openProperty(r)}>Use as subject</button></li>)}
                  {!all.some(r => r.kind === "property") && <li className="px-2 py-2 text-slate-500">No saved properties for these filters.</li>}</ul></section>
            </div>
            {/* Kept mounted while hidden so unsaved valuation inputs survive tab and basemap changes. */}
            <div role="tabpanel" id="panel-valuation" aria-labelledby="tab-valuation" hidden={ws.panels.tab !== "valuation"} className="p-3">
              {analysisId ? <ValuationWorkflow key={analysisId} propertyId={analysisId} methods={methods} onPrepared={onPrepared} onSelectEvidence={select} refreshKey={geometrySaves} />
                : <div className="text-xs text-slate-500 space-y-2 p-1"><p>No analysis open. Choose a subject, property type and approach in the Subject tab, then start the valuation.</p>
                  <button type="button" className="text-blue-700 underline" onClick={() => setPanels({ tab: "subject" })}>Go to Subject →</button></div>}
            </div>
            <div role="tabpanel" id="panel-coverage" aria-labelledby="tab-coverage" hidden={ws.panels.tab !== "coverage"}>
              <CoveragePanel data={data} unlocated={unlocated} onSelect={selectRecord} />
            </div>
          </div>
          <p className="px-3 py-1.5 border-t border-slate-100 text-[10px] text-slate-500">Saved Mizan evidence, not a live transaction feed. Asking prices are not achieved sales. Distances and areas are approximate.</p>
        </aside>
      </>}
    </div>
  </div>;
}

export default function MapPage() { return <Suspense fallback={<p className="p-4 text-sm">Loading map workspace…</p>}><MapWorkspace /></Suspense>; }
