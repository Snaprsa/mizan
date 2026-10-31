"use client";
// Map-first workspace, redesigned for simplicity: a full-screen map, one floating card (bottom sheet on
// phones) that shows one thing at a time, and a few quiet map controls.
// Journey: explore evidence → value a property (location → type → approach) → inputs → result.
import dynamic from "next/dynamic";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Check, Circle, Expand, Hexagon, Layers, LocateFixed, Map as MapIcon, Menu, Minus, PencilRuler, Plus, Ruler, Scan, Shrink, SlidersHorizontal, Square, Table2, X } from "lucide-react";
import { getMapRecords, getProperty, saveProperty, getValuationCatalog, startMapAnalysis, type MapRecord, type MapResponse, type PreparedAnalysis, type ValuationMethod } from "@/lib/api";
import ValuationWorkflow from "@/components/valuation-workflow";
import { areaPoints, formatArea, formatDistance, geodesicAreaSqm, haversineMeters, inSearchArea, latLngsFromPolygon, pathLengthMeters, polygonFromLatLngs, type GeoJSONPolygon, type LatLng, type SearchArea } from "@/lib/geo";
import { applyEvidenceFilters, evidenceSummaries, facetValues, LAYER, LAYERS, riyadhToday, sourceLabel, UNAVAILABLE_LAYERS } from "@/lib/map-evidence";
import { BASEMAPS, defaultState, loadState, saveState, type Basemap, type Camera, type Subject, type WorkspaceState } from "@/lib/map-workspace-state";
import { readProviderConfig } from "@/lib/map-provider";
import MapSearch from "@/components/map/map-search";
import MapStylePanel from "@/components/map/map-style-panel";
import { CoveragePanel, EvidenceTable, money, precisionLabel } from "@/components/map/evidence-panels";
import type { Draft, MapBounds, MapStatus, MapTool, RendererHandle } from "@/components/map/types";
import { Dot, Glass, PrimaryButton, Row, Section, Segmented, SheetHeader, Switch } from "@/components/ui/sheet-ui";

const MapRenderer = dynamic(() => import("@/components/map/map-renderer"), { ssr: false,
  loading: () => <div className="absolute inset-0 bg-[#e8e6e1]" aria-label="Loading map" /> });
const LIMIT = 5000;
const inBounds = (p: LatLng | null, b: MapBounds | null) => !!p && !!b && p[0] >= b.south && p[0] <= b.north && (b.west <= b.east ? p[1] >= b.west && p[1] <= b.east : p[1] >= b.west || p[1] <= b.east);
const n0 = new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 });
// Unicode isolate: stops an Arabic district from flipping a neighbouring date (2027-02-04 shown as 04-02-2027).
const isolate = (s: string | null | undefined) => `\u2068${s ?? ""}\u2069`;
const label = (s: string) => s.replaceAll("_", " ").replace(/^./, c => c.toUpperCase());
const NAV = [{ href: "/dashboard", label: "Cases" }, { href: "/properties", label: "Properties" }, { href: "/data", label: "Market data" }, { href: "/cases/new", label: "New case" }];
type Sheet = "peek" | "half" | "full";

function MapWorkspace() {
  const params = useSearchParams(); const router = useRouter();
  const caseId = params.get("case_id") || ""; const analysisId = params.get("analysis") || "";
  const [ws, setWs] = useState<WorkspaceState>(defaultState); const [hydrated, setHydrated] = useState(false);
  const update = useCallback((patch: Partial<WorkspaceState> | ((s: WorkspaceState) => Partial<WorkspaceState>)) =>
    setWs(s => ({ ...s, ...(typeof patch === "function" ? patch(s) : patch) })), []);
  const hadSavedCamera = useRef(false);
  useEffect(() => { const s = loadState(typeof window === "undefined" ? undefined : window.localStorage); hadSavedCamera.current = !!s.camera;
    // Always open somewhere sensible: the valuation in the URL, otherwise Explore.
    setWs({ ...s, panels: { ...s.panels, tab: new URLSearchParams(window.location.search).get("analysis") ? "valuation" : "evidence" } }); setHydrated(true); }, []);
  useEffect(() => { if (hydrated) saveState(window.localStorage, ws); }, [ws, hydrated]);

  const [methods, setMethods] = useState<ValuationMethod[]>([]); const [propertyTypes, setPropertyTypes] = useState<string[]>([]);
  const [prepared, setPrepared] = useState<PreparedAnalysis | null>(null);
  const [data, setData] = useState<MapResponse | null>(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [bounds, setBounds] = useState<MapBounds | null>(null); const [group, setGroup] = useState<string[]>([]);
  const [tool, setTool] = useState<MapTool>("browse"); const [draft, setDraft] = useState<Draft>(null); const [measure, setMeasure] = useState<LatLng[] | null>(null);
  const [editArea, setEditArea] = useState(false); const [status, setStatus] = useState<MapStatus | null>(null);
  const [notice, setNotice] = useState(""); const [starting, setStarting] = useState(false); const [savingOutline, setSavingOutline] = useState(false);
  const [fullscreen, setFullscreen] = useState(false); const [narrow, setNarrow] = useState(false);
  const [popover, setPopover] = useState<"" | "style" | "tools" | "menu">(""); const [filtersOpen, setFiltersOpen] = useState(false);
  const [sheet, setSheet] = useState<Sheet>("half"); const [place, setPlace] = useState<LatLng | null>(null); const [listSize, setListSize] = useState(30);
  const handle = useRef<RendererHandle | null>(null); const root = useRef<HTMLDivElement>(null);
  const today = useMemo(riyadhToday, []);
  const [esriKey, setEsriKey] = useState<string | null>(null);
  useEffect(() => { setEsriKey(readProviderConfig().esriKey); }, []);

  useEffect(() => { getValuationCatalog().then(c => { setMethods(c.methods); setPropertyTypes(c.property_types); }).catch(e => setError(e.message)); }, []);
  useEffect(() => { const set = () => setNarrow(window.innerWidth < 768); set(); window.addEventListener("resize", set); return () => window.removeEventListener("resize", set); }, []);
  useEffect(() => { const on = () => setFullscreen(!!document.fullscreenElement); document.addEventListener("fullscreenchange", on); return () => document.removeEventListener("fullscreenchange", on); }, []);
  useEffect(() => { if (!popover) return; const close = (e: KeyboardEvent) => { if (e.key === "Escape") setPopover(""); }; window.addEventListener("keydown", close); return () => window.removeEventListener("keydown", close); }, [popover]);

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
  // First visit (no saved camera): frame the saved evidence once it loads.
  const framed = useRef(false);
  useEffect(() => {
    if (framed.current || !hydrated || !data || !bounds || !handle.current) return;
    framed.current = true;
    if (hadSavedCamera.current) return;
    const pts = data.data.filter(r => r.coordinates).map(r => r.coordinates as LatLng);
    if (pts.length) handle.current.fit(pts, 15);
  }, [data, hydrated, bounds]);

  // The analysis property supplies the subject, its coordinate provenance and any saved outline.
  // True once this session has been on "no analysis": an outline drawn then belongs to the next analysis started.
  const blankBefore = useRef(false);
  const [propertyRevision, setPropertyRevision] = useState<number | null>(null); const [geometrySaves, setGeometrySaves] = useState(0);
  useEffect(() => {
    if (!analysisId) { setPrepared(null); setPropertyRevision(null); blankBefore.current = true; return; }
    let current = true;
    getProperty(analysisId).then(p => { if (!current) return; setPropertyRevision(p.revision);
      const loc = p.property.location as Record<string, unknown>;
      const outline = loc.site_outline as GeoJSONPolygon | undefined;
      // A saved outline wins; an unsaved one is kept only if it was drawn before any analysis was open.
      const carried = blankBefore.current ? undefined : null;
      update(s => ({ siteOutline: outline?.coordinates ? latLngsFromPolygon(outline) : carried === null ? null : s.siteOutline,
        subject: typeof loc.latitude === "number" && typeof loc.longitude === "number" ? { coordinates: [loc.latitude, loc.longitude],
          source: (loc.coordinate_source as Subject["source"]) || "map_pin", precision: (loc.coordinate_precision as Subject["precision"]) || "user_selected", confirmed: true, label: p.property.name } : s.subject }));
      blankBefore.current = false;
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
  const evidenceRing: SearchArea | null = ws.searchArea ?? (prepared?.coordinates ? { kind: "radius", center: prepared.coordinates, radius_m: prepared.radius_km * 1000 } : null);
  const listed = useMemo(() => layered.filter(r => (!f.withinView || inBounds(r.coordinates, bounds)) && (!ws.filterToArea || !ws.searchArea || inSearchArea(r.coordinates, ws.searchArea))
    && (!group.length || group.includes(r.id))), [layered, f.withinView, bounds, ws.filterToArea, ws.searchArea, group]);
  const summaries = useMemo(() => evidenceSummaries(listed), [listed]);
  const facets = useMemo(() => facetValues(all), [all]);
  const selected = all.find(r => r.id === ws.selectedId) || null;
  const subjectPoint = ws.subject?.coordinates || null;
  const caps = status?.capabilities;
  const view = ws.panels.tab === "coverage" ? "coverage" : filtersOpen ? "filters" : ws.panels.tab === "valuation" && analysisId ? "analysis"
    : ws.panels.tab === "subject" || (ws.panels.tab === "valuation" && !analysisId) ? "flow" : selected ? "record" : "explore";
  const setPanels = useCallback((patch: Partial<WorkspaceState["panels"]>) => update(s => ({ panels: { ...s.panels, ...patch } })), [update]);
  const go = useCallback((tab: WorkspaceState["panels"]["tab"]) => { setFiltersOpen(false); setPanels({ tab }); if (narrow) setSheet(s => s === "peek" ? "half" : s); }, [setPanels, narrow]);

  const select = useCallback((id: string) => { update(s => ({ selectedId: id, panels: { ...s.panels, tab: s.panels.tab === "valuation" ? "valuation" : "evidence" } })); setFiltersOpen(false); }, [update]);
  const selectRecord = useCallback((r: MapRecord) => { select(r.id); if (r.coordinates && !inBounds(r.coordinates, bounds)) handle.current?.fit([r.coordinates], 17); }, [select, bounds]);
  const setSubject = useCallback((s: Subject | null) => { update({ subject: s }); setPrepared(null); if (analysisId) analysisUrl(null); }, [update, analysisId, analysisUrl]);

  const onMapClick = useCallback((p: LatLng) => {
    setPopover("");
    if (tool === "place_subject") { setSubject({ coordinates: p, source: "map_pin", precision: "user_selected", confirmed: false }); setTool("browse"); setPlace(null); go("subject"); }
    else if (tool === "draw_area" || tool === "draw_site" || tool === "measure") setDraft(d => ({ tool, points: [...(d?.tool === tool ? d.points : []), p] }));
  }, [tool, setSubject, go]);
  const onCamera = useCallback((camera: Camera, b: MapBounds) => { setBounds(b); update({ camera }); }, [update]);
  const onStatus = useCallback((s: MapStatus) => setStatus(s), []);
  const onAreaEdit = useCallback((a: SearchArea) => update({ searchArea: a }), [update]);
  const onSubjectMove = useCallback((p: LatLng) => update(s => ({ subject: s.subject ? { ...s.subject, coordinates: p, source: "map_pin", precision: "user_selected", confirmed: false } : null })), [update]);

  function startTool(next: MapTool) {
    setPopover("");
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
    setPopover(""); const center = subjectPoint || handle.current?.center(); if (!center) return;
    update({ searchArea: { kind: "radius", center, radius_m: prepared ? prepared.radius_km * 1000 : 1000 }, filterToArea: true }); setEditArea(true); setTool("browse"); setDraft(null);
  }
  function fitEvidence() { const pts = (group.length ? located.filter(r => group.includes(r.id)) : located).map(r => r.coordinates as LatLng); if (pts.length) handle.current?.fit(pts, 16); else setNotice("No evidence with a location to show."); }
  function fitSubject() { const pts = [...(subjectPoint ? [subjectPoint] : []), ...areaPoints(evidenceRing), ...(ws.siteOutline || [])]; if (pts.length) handle.current?.fit(pts, 18); else setNotice("Drop a pin first."); }
  function toggleFullscreen() { if (document.fullscreenElement) document.exitFullscreen(); else root.current?.requestFullscreen?.().catch(() => setNotice("Fullscreen isn't available here.")); }
  function beginValuation() { setFiltersOpen(false); update(s => ({ selectedId: null, panels: { ...s.panels, tab: "subject" } })); if (!ws.subject) setTool("place_subject"); if (narrow) setSheet("half"); }

  async function start() {
    if (!ws.subject?.confirmed || !ws.subjectType || !ws.approach) return;
    setStarting(true); setError("");
    try {
      const p = await startMapAnalysis({ latitude: ws.subject.coordinates[0], longitude: ws.subject.coordinates[1], property_type: ws.subjectType, method: ws.approach,
        coordinate_source: ws.subject.source, coordinate_precision: ws.subject.precision, ...(f.city ? { city: f.city } : {}) });
      onPrepared(p); analysisUrl(p.property_id); go("valuation"); setReload(n => n + 1);
    } catch (e) { setError((e as Error).message); } finally { setStarting(false); }
  }
  async function saveOutline() {
    if (!analysisId || !ws.siteOutline) return;
    setSavingOutline(true); setError("");
    try {
      const p = await getProperty(analysisId);
      const outline = { ...polygonFromLatLngs(ws.siteOutline), source: "user_drawn", cadastral: false, drawn_on: today,
        basemap: status?.provider === "esri" ? `esri:${ws.basemap}` : "osm:roadmap", approximate_area_sqm: Math.round(geodesicAreaSqm(ws.siteOutline)) };
      const saved = await saveProperty(analysisId, { ...p.property, location: { ...p.property.location, site_outline: outline } }, p.revision, "Site outline drawn on map (approximate; not a cadastral boundary)");
      setPropertyRevision(saved.revision); setGeometrySaves(n => n + 1); setNotice("Outline saved to the property."); setReload(n => n + 1);
    } catch (e) { setError((e as Error).message); } finally { setSavingOutline(false); }
  }
  const openProperty = useCallback((r: MapRecord) => { analysisUrl(r.entity_id); go("valuation"); }, [analysisUrl, go]);
  // Search results only move the map; the user drops and confirms the pin (keeps geocoding within free, not-stored use).
  const onPlace = (p: LatLng) => { setPlace(p); handle.current?.fit([p], 17); };
  const onCoordinates = (p: LatLng) => { setSubject({ coordinates: p, source: "coordinate_entry", precision: "user_selected", confirmed: false }); setPlace(null); handle.current?.fit([p], 18); go("subject"); };
  useEffect(() => { if (!notice) return; const t = setTimeout(() => setNotice(""), 5000); return () => clearTimeout(t); }, [notice]);

  const draftMeasure = draft?.tool === "measure" ? pathLengthMeters(draft.points) : draft && draft.points.length >= 3 ? geodesicAreaSqm(draft.points) : null;
  const setFilter = (patch: Partial<WorkspaceState["filters"]>) => update(s => ({ filters: { ...s.filters, ...patch } }));
  const period = !f.from && !f.to ? "any" : f.to === today ? ({ 30: "30", 90: "90", 365: "365" } as Record<number, string>)[Math.round((new Date(`${today}T12:00:00Z`).getTime() - new Date(`${f.from}T12:00:00Z`).getTime()) / 86400000)] || "custom" : "custom";
  const setPeriod = (v: string) => { if (v === "any") return setFilter({ from: "", to: "" }); const days = Number(v); if (!days) return;
    const s = new Date(`${today}T12:00:00Z`); s.setUTCDate(s.getUTCDate() - days); setFilter({ to: today, from: s.toISOString().slice(0, 10) }); };
  const method = methods.find(m => m.key === ws.approach);
  const activeFilters = [f.city, f.type, f.from || f.to, ...f.statuses, ...f.sources, ...f.precisions, f.minReliability].filter(Boolean).length + LAYERS.filter(l => ws.layers[l.key] === false).length;

  // Auto-generated names look like "Land · 24.77200, 46.64100": show the coordinates as the subtitle.
  const analysisName = prepared?.property_name || ws.subject?.label || "Valuation";
  const nameMatch = analysisName.match(/^(.*) · (-?\d+\.\d+, -?\d+\.\d+)$/);
  const analysisTitle = nameMatch ? { title: nameMatch[1], place: nameMatch[2] } : { title: analysisName, place: "" };

  // ── Card content ──────────────────────────────────────────────────────────
  const explore = <>
    <SheetHeader title={group.length ? "Cluster" : "Explore"} subtitle={loading ? "Updating…" : `${listed.length} record${listed.length === 1 ? "" : "s"}${f.withinView ? " in view" : ""}${data?.truncated ? ` · first ${data.returned} of ${data.total}` : ""}`}
      trailing={<button type="button" onClick={() => setFiltersOpen(true)} className="relative mt-1 grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-black/70 active:bg-black/10" aria-label="Filters">
        <SlidersHorizontal size={17} />{activeFilters > 0 && <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-[#007AFF] px-1 text-[10px] font-semibold text-white">{activeFilters}</span>}</button>} />
    <div className="px-4 pb-2"><PrimaryButton onClick={beginValuation}>Value a property</PrimaryButton></div>
    <div className="px-4 py-2 grid grid-cols-3 gap-2">{(["transaction", "listing", "property"] as const).map(k => {
      const s = summaries.find(x => x.key === `${k}:SAR`); const count = listed.filter(r => r.kind === k).length;
      return <div key={k} className="rounded-xl bg-white ring-1 ring-black/[0.05] px-3 py-2.5">
        <div className="flex items-center gap-1.5 text-[12px] text-black/50"><Dot color={LAYER[k].color} />{LAYER[k].short}</div>
        <div className="text-[22px] font-semibold tracking-tight text-black/90 leading-tight mt-0.5">{count}</div>
        <div className="text-[11.5px] text-black/45 truncate" title={s && !s.insufficient ? "Median unit value" : "Needs at least 3 values"}>{s && !s.insufficient ? `${n0.format(s.median!)} SAR/m²` : k === "property" ? "saved" : "median —"}</div></div>; })}</div>
    <div className="px-4 py-1"><Segmented label="Scope" value={f.withinView ? "view" : "all"} onChange={v => setFilter({ withinView: v === "view" })}
      options={[{ value: "view", label: "In map view" }, { value: "all", label: "All saved" }]} /></div>
    {group.length > 0 && <div className="px-4 pt-2"><button type="button" className="text-[14px] text-[#007AFF]" onClick={() => setGroup([])}>Show all records</button></div>}
    {ws.filterToArea && ws.searchArea && <div className="px-4 pt-2 text-[13px] text-black/55">Limited to your search area · <button type="button" className="text-[#007AFF]" onClick={() => update({ filterToArea: false })}>Show all</button></div>}
    <Section title="Evidence" footer={listed.length > listSize ? <button type="button" className="text-[#007AFF]" onClick={() => setListSize(n => n + 30)}>Show more</button> : "Saved Mizan records — asking prices are never counted as sales."}>
      {listed.slice(0, listSize).map(r => <Row key={r.id} onClick={() => selectRecord(r)} leading={<Dot color={LAYER[r.kind].color} />} label={r.title}
        detail={[LAYER[r.kind].short, r.district || r.city, r.date ? (r.date > today ? `${r.date} (future)` : r.date) : "undated"].filter(Boolean).map(isolate).join(" · ")}
        value={r.kind === "market" ? `${String(r.value)}` : r.price_per_sqm != null ? `${n0.format(r.price_per_sqm)}/m²` : r.coordinates ? "" : "No location"} />)}
      {!listed.length && !loading && <div className="px-4 py-6 text-center text-[14px] text-black/45">{f.withinView ? "Nothing in this part of the map." : "No records match your filters."}</div>}
    </Section>
    {(unlocated.length > 0 || (data?.coverage?.unverified_datasets ?? 0) > 0) && <Section>
      <Row onClick={() => go("coverage")} chevron label="Data to review" detail={`${unlocated.length} without a location · ${data?.coverage?.unverified_datasets ?? 0} files not imported`} />
    </Section>}
  </>;

  const record = selected && <>
    <SheetHeader onBack={() => update({ selectedId: null })} backLabel="Explore" title={selected.title} subtitle={`${LAYER[selected.kind].label} · ${selected.status}`} />
    <Section>
      <Row label={selected.kind === "transaction" ? "Sale price" : selected.kind === "market" ? "Value" : "Asking price"} value={selected.kind === "market" ? `${String(selected.value)} ${selected.unit || ""}` : money(selected.price, selected.currency)} />
      <Row label="Unit value" value={selected.price_per_sqm == null ? "—" : `${n0.format(selected.price_per_sqm)} SAR/m²`} />
      <Row label="Area" value={selected.area_sqm == null ? "—" : `${n0.format(selected.area_sqm)} m²`} />
      <Row label="Date" detail={selected.date_basis.replaceAll("_", " ")} value={selected.date ? `${selected.date}${selected.date > today ? " · future" : ""}` : "Not recorded"} />
      {subjectPoint && selected.coordinates && <Row label="Distance to pin" value={`≈ ${formatDistance(haversineMeters(subjectPoint, selected.coordinates))}`} />}
    </Section>
    <Section title="Source" footer={selected.coordinates ? undefined : "No location is guessed from the city or district."}>
      <Row label="Location" detail={precisionLabel(selected.location_precision)} value={selected.coordinates ? selected.coordinates.map(v => v.toFixed(4)).join(", ") : "Missing"} />
      <Row label="Reliability" value={selected.reliability_score == null ? "Not scored" : `${selected.reliability_score} of 5`} />
      {/^https?:\/\//i.test(selected.source) ? <Row label="Source" value={<a className="text-[#007AFF]" href={selected.source} target="_blank" rel="noopener noreferrer">{sourceLabel(selected.source)}</a>} />
        : <Row label="Source" detail={selected.source} />}
    </Section>
    <Section>
      {selected.kind === "property" && <Row onClick={() => openProperty(selected)} label={<span className="text-[#007AFF]">Value this property</span>} />}
      <Row onClick={() => router.push(selected.href)} chevron label={`Open ${selected.kind === "property" ? "property" : selected.kind === "market" ? "market data" : "evidence"}`} />
    </Section>
  </>;

  const flow = <>
    <SheetHeader onBack={() => { setTool("browse"); go("evidence"); }} backLabel="Explore" title="Value a property" subtitle="Three quick choices, then Mizan gathers the evidence." />
    <Section title="1 · Location" footer={!ws.subject ? "Tap the map where the property is, or type coordinates in the search bar." : !ws.subject.confirmed ? "Drag the pin, or select it and use the arrow keys, until it sits on the property." : undefined}>
      {!ws.subject ? <Row label={tool === "place_subject" ? <span className="text-[#007AFF]">Tap the map to drop a pin…</span> : "Drop a pin"} onClick={() => setTool("place_subject")} leading={<LocateFixed size={18} className="text-[#007AFF]" />} />
        : <><Row label={ws.subject.confirmed ? "Location confirmed" : "Is the pin in the right place?"} detail={`${ws.subject.coordinates.map(n => n.toFixed(5)).join(", ")} · ${precisionLabel(ws.subject.precision)}`}
              leading={ws.subject.confirmed ? <Check size={18} className="text-[#34C759]" /> : <LocateFixed size={18} className="text-[#FF9F0A]" />} />
          {!ws.subject.confirmed && <div className="p-3"><PrimaryButton onClick={() => update(s => ({ subject: s.subject && { ...s.subject, confirmed: true } }))}>Confirm location</PrimaryButton></div>}
          {!analysisId && <Row onClick={() => { setSubject(null); setTool("place_subject"); }} label={<span className="text-[#007AFF]">Move pin</span>} />}</>}
    </Section>
    {ws.subject?.confirmed && <Section title="2 · Property type">
      <div className="flex flex-wrap gap-2 p-3">{propertyTypes.map(t => <button key={t} type="button" onClick={() => update({ subjectType: t })} aria-pressed={ws.subjectType === t}
        className={`rounded-full px-3.5 py-1.5 text-[14px] ${ws.subjectType === t ? "bg-[#007AFF] text-white" : "bg-black/[0.05] text-black/75 active:bg-black/10"}`}>{label(t)}</button>)}</div>
    </Section>}
    {ws.subject?.confirmed && ws.subjectType && <Section title="3 · Approach" footer={method?.fields.length ? `You'll be asked for: ${method.fields.map(x => x.label.toLowerCase()).join(", ")}.` : undefined}>
      {methods.filter(m => m.implemented).map(m => <Row key={m.key} onClick={() => update({ approach: m.key })} label={m.label} detail={m.description}
        leading={<span className={`grid h-5 w-5 place-items-center rounded-full ${ws.approach === m.key ? "bg-[#007AFF] text-white" : "ring-1 ring-black/20"}`}>{ws.approach === m.key && <Check size={13} strokeWidth={3} />}</span>} />)}
    </Section>}
    {ws.subject?.confirmed && ws.subjectType && <div className="px-4 py-3"><PrimaryButton disabled={starting || !method?.implemented} onClick={start}>{starting ? "Gathering evidence…" : "Start valuation"}</PrimaryButton></div>}
    {!ws.subject && all.some(r => r.kind === "property") && <Section title="Or pick a saved property">
      {all.filter(r => r.kind === "property").slice(0, 8).map(r => <Row key={r.id} onClick={() => openProperty(r)} chevron leading={<Dot color={LAYER.property.color} />} label={r.title} detail={r.coordinates ? precisionLabel(r.location_precision) : "No location yet"} />)}
    </Section>}
    {methods.some(m => !m.implemented) && ws.subjectType && <p className="px-5 pb-4 text-[12px] text-black/40">Not available yet: {methods.filter(m => !m.implemented).map(m => m.label).join(", ")}.</p>}
  </>;

  const analysis = <>
    <SheetHeader onBack={() => { analysisUrl(null); setPrepared(null); go("evidence"); }} backLabel="Done" title={analysisTitle.title}
      subtitle={prepared ? [analysisTitle.place, prepared.method_label].filter(Boolean).join(" · ") : "Loading…"} />
    {ws.siteOutline && <Section title="Site outline" footer="Drawn by you on the map. Approximate — not a certified cadastral boundary.">
      <Row label="Approximate area" value={formatArea(geodesicAreaSqm(ws.siteOutline))} />
      <Row onClick={saveOutline} label={<span className="text-[#007AFF]">{savingOutline ? "Saving…" : "Save outline to property"}</span>} />
    </Section>}
    <div className="px-3 pb-4"><ValuationWorkflow key={analysisId} propertyId={analysisId} methods={methods} onPrepared={onPrepared} onSelectEvidence={select} refreshKey={geometrySaves} /></div>
  </>;

  const filters = <>
    <SheetHeader onBack={() => setFiltersOpen(false)} backLabel="Done" title="Filters" trailing={activeFilters > 0 ? <button type="button" className="mt-1 text-[15px] text-[#007AFF]" onClick={() => update(s => ({ layers: defaultState().layers, filters: { ...defaultState().filters, withinView: s.filters.withinView } }))}>Reset</button> : undefined} />
    <Section title="Show on map" footer={<>Not connected yet: {UNAVAILABLE_LAYERS.map(u => u.label.toLowerCase()).join(", ")}.</>}>
      {LAYERS.map(l => <Row key={l.key} leading={<Dot color={l.color} />} label={l.label} detail={`${all.filter(r => r.kind === l.key && r.coordinates).length} on map · ${all.filter(r => r.kind === l.key).length} saved`}>
        <Switch label={l.label} checked={ws.layers[l.key] !== false} onChange={v => update(s => ({ layers: { ...s.layers, [l.key]: v } }))} /></Row>)}
    </Section>
    <Section title="Period">
      <div className="p-2"><Segmented label="Period" value={period === "custom" ? "custom" : period} onChange={setPeriod}
        options={[{ value: "any", label: "Any" }, { value: "30", label: "30 days" }, { value: "90", label: "90 days" }, { value: "365", label: "1 year" }, ...(period === "custom" ? [{ value: "custom", label: "Custom" }] : [])]} /></div>
      <div className="grid grid-cols-2 gap-2 px-3 pb-3 text-[13px] text-black/55"><label>From<input type="date" className="mizan-field mt-1" value={f.from} onChange={e => setFilter({ from: e.target.value })} /></label>
        <label>To<input type="date" className="mizan-field mt-1" value={f.to} onChange={e => setFilter({ to: e.target.value })} /></label></div>
    </Section>
    <Section title="Place & type">
      <Row label="City"><select aria-label="City" className="mizan-select" value={f.city} onChange={e => setFilter({ city: e.target.value })}><option value="">Any</option>{data?.available.cities.map(c => <option key={c}>{c}</option>)}</select></Row>
      <Row label="Property type"><select aria-label="Property type" className="mizan-select" value={f.type} onChange={e => setFilter({ type: e.target.value })}><option value="">Any</option>{data?.available.property_types.map(t => <option key={t} value={t}>{label(t)}</option>)}</select></Row>
      <Row label="Search"><input aria-label="Search evidence text" className="mizan-field !w-40" placeholder="Name, district…" value={f.q} onChange={e => setFilter({ q: e.target.value })} /></Row>
    </Section>
    <Section title="Quality">
      <div className="p-2"><Segmented label="Minimum reliability" value={String(f.minReliability ?? "any")} onChange={v => setFilter({ minReliability: v === "any" ? null : Number(v) })}
        options={[{ value: "any", label: "Any" }, { value: "3", label: "3+" }, { value: "4", label: "4+" }, { value: "5", label: "5" }]} /></div>
      {(["statuses", "precisions", "sources"] as const).map(key => facets[key].length > 1 && <details key={key} className="group">
        <summary className="flex min-h-[44px] cursor-pointer items-center px-3.5 text-[15px] text-black/85 list-none">{key === "statuses" ? "Status" : key === "sources" ? "Source" : "Location precision"}
          <span className="ml-auto text-black/40 text-[14px]">{f[key].length ? `${f[key].length} selected` : "All"}</span></summary>
        <div className="divide-y divide-black/[0.06] border-t border-black/[0.06]">{facets[key].map(([v, n]) => <Row key={v} label={key === "precisions" ? precisionLabel(v) : v} detail={`${n} records`}>
          <Switch label={v} checked={f[key].includes(v)} onChange={on => setFilter({ [key]: on ? [...f[key], v] : f[key].filter(x => x !== v) })} /></Row>)}</div></details>)}
    </Section>
  </>;

  const coverage = <>
    <SheetHeader onBack={() => go("evidence")} backLabel="Explore" title="Data to review" subtitle="Records without a location stay off the map — nothing is guessed." />
    <CoveragePanel data={data} unlocated={unlocated} onSelect={r => { go("evidence"); selectRecord(r); }} />
  </>;

  const content = view === "coverage" ? coverage : view === "filters" ? filters : view === "analysis" ? analysis : view === "flow" ? flow : view === "record" ? record : explore;
  const sheetHeight = narrow ? (sheet === "peek" ? "h-[200px]" : sheet === "half" ? "h-[52vh]" : "h-[88vh]") : "";

  return <div ref={root} className="mizan-apple relative h-full w-full overflow-hidden bg-[#e8e6e1]">
    {hydrated && <MapRenderer key={esriKey || "standard"} handleRef={handle} records={located} selectedId={ws.selectedId} groupIds={group} basemap={ws.basemap} initialCamera={ws.camera}
      subject={ws.subject} subjectDraggable={!analysisId && !!ws.subject && !ws.subject.confirmed} searchArea={evidenceRing} editArea={editArea && !!ws.searchArea}
      siteOutline={ws.siteOutline} placeMarker={place} tool={tool} draft={draft ?? (measure ? { tool: "measure", points: measure } : null)}
      onCamera={onCamera} onSelect={select} onGroup={setGroup} onMapClick={onMapClick} onSubjectMove={onSubjectMove} onAreaEdit={onAreaEdit} onStatus={onStatus} />}

    {/* The one card: sidebar on desktop, bottom sheet on phones. */}
    <Glass role="complementary" aria-label="Mizan" className={`absolute z-[1000] flex flex-col overflow-hidden ${narrow ? `inset-x-0 bottom-0 rounded-t-[22px] ${sheetHeight} transition-[height] duration-200` : "left-3 top-3 bottom-3 w-[380px] rounded-[22px]"}`}>
      {narrow && <button type="button" aria-label={`Sheet ${sheet}; change size`} onClick={() => setSheet(s => s === "peek" ? "half" : s === "half" ? "full" : "peek")} className="mx-auto mt-2 h-[5px] w-10 shrink-0 rounded-full bg-black/20" />}
      <div className="flex shrink-0 items-center gap-2 px-3 pt-3">
        <div className="relative">
          <button type="button" aria-label="Menu" aria-expanded={popover === "menu"} onClick={() => setPopover(p => p === "menu" ? "" : "menu")} className="grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-black/70 active:bg-black/10"><Menu size={17} /></button>
          {popover === "menu" && <Glass className="absolute left-0 top-11 z-10 w-56 rounded-2xl p-1.5">
            <p className="px-3 py-1.5 text-[13px] font-semibold text-black/80">Mizan <span lang="ar" className="font-normal text-black/40">ميزان</span></p>
            {NAV.map(n => <Link key={n.href} href={n.href} className="block rounded-lg px-3 py-2 text-[15px] text-black/80 hover:bg-black/[0.05]">{n.label}</Link>)}</Glass>}
        </div>
        <div className="flex-1 min-w-0"><MapSearch records={all} geocodingAvailable={!!caps?.geocoding} hasKey={!!esriKey} onCoordinates={onCoordinates} onRecord={r => { setPlace(null); selectRecord(r); }} onPlace={onPlace} /></div>
      </div>
      {caseId && <p className="mx-4 mt-2 rounded-lg bg-[#007AFF]/10 px-3 py-1.5 text-[12.5px] text-[#0059c9]">Showing one case. <Link href="/map" className="underline">Show everything</Link></p>}
      {error && <p role="alert" className="mx-4 mt-2 rounded-lg bg-[#FF3B30]/10 px-3 py-1.5 text-[13px] text-[#c4271d]">{error}</p>}
      <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain pb-3">{content}</div>
    </Glass>

    {/* Map style + provider status (top right). */}
    <div className="absolute right-3 top-3 z-[1001] flex flex-col items-end gap-2">
      <Glass className="rounded-full"><button type="button" aria-label="Map style" aria-expanded={popover === "style"} onClick={() => setPopover(p => p === "style" ? "" : "style")} className="grid h-11 w-11 place-items-center text-black/75"><MapIcon size={19} /></button></Glass>
      {popover === "style" && <Glass className="max-h-[calc(100vh-90px)] w-[320px] max-w-[calc(100vw-24px)] overflow-y-auto rounded-2xl p-3.5">
        <MapStylePanel basemap={ws.basemap} status={status} onChoose={b => { update({ basemap: b }); setPopover(""); }}
          onKeyChange={k => { setEsriKey(k); if (k) { update({ basemap: "hybrid" }); setPopover(""); setNotice("Satellite is on."); } }} /></Glass>}
      {status?.state === "error" && <Glass className="max-w-[260px] rounded-2xl px-3 py-2 text-[12.5px] text-[#c4271d]">{status.message}</Glass>}
    </div>

    {/* Map controls (bottom right). */}
    <div className={`absolute right-3 z-[1000] flex flex-col items-end gap-2 ${narrow ? (sheet === "full" ? "hidden" : sheet === "half" ? "bottom-[calc(52vh+12px)]" : "bottom-[212px]") : "bottom-8"}`}>
      {popover === "tools" && <Glass className="w-60 rounded-2xl p-1.5">
        {[{ t: "draw_area" as MapTool, icon: Hexagon, text: "Draw a search area" }, { t: "draw_site" as MapTool, icon: Square, text: "Trace the site outline" }, { t: "measure" as MapTool, icon: Ruler, text: "Measure distance" }].map(x =>
          <button key={x.t} type="button" onClick={() => startTool(x.t)} className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[15px] text-black/80 hover:bg-black/[0.05]"><x.icon size={17} className="text-[#007AFF]" />{x.text}</button>)}
        <button type="button" onClick={radiusAroundSubject} className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[15px] text-black/80 hover:bg-black/[0.05]"><Circle size={17} className="text-[#007AFF]" />Radius around pin</button>
        {(ws.searchArea || ws.siteOutline || measure) && <div className="mt-1 border-t border-black/[0.06] pt-1">
          {ws.searchArea && <button type="button" onClick={() => { setEditArea(v => !v); setPopover(""); }} className="w-full rounded-lg px-3 py-2 text-left text-[14px] text-black/70 hover:bg-black/[0.05]">{editArea ? "Done editing area" : "Edit search area"}</button>}
          {ws.searchArea && <button type="button" onClick={() => { update({ searchArea: null, filterToArea: false }); setEditArea(false); setPopover(""); }} className="w-full rounded-lg px-3 py-2 text-left text-[14px] text-[#FF3B30] hover:bg-black/[0.05]">Remove search area</button>}
          {ws.siteOutline && <button type="button" onClick={() => { update({ siteOutline: null }); setPopover(""); }} className="w-full rounded-lg px-3 py-2 text-left text-[14px] text-[#FF3B30] hover:bg-black/[0.05]">Remove outline from map</button>}
          {measure && <button type="button" onClick={() => { setMeasure(null); setPopover(""); }} className="w-full rounded-lg px-3 py-2 text-left text-[14px] text-[#FF3B30] hover:bg-black/[0.05]">Clear measurement</button>}</div>}
      </Glass>}
      <Glass className="flex flex-col overflow-hidden rounded-[14px] divide-y divide-black/[0.08]">
        <MapButton label="Tools" onClick={() => setPopover(p => p === "tools" ? "" : "tools")} pressed={popover === "tools" || tool !== "browse"}><PencilRuler size={18} /></MapButton>
        <MapButton label="Show the pin" onClick={fitSubject}><LocateFixed size={18} /></MapButton>
        <MapButton label="Show all evidence" onClick={fitEvidence}><Scan size={18} /></MapButton>
        {!narrow && <MapButton label="Evidence table" onClick={() => setPanels({ table: !ws.panels.table })} pressed={ws.panels.table}><Table2 size={18} /></MapButton>}
        {!narrow && <MapButton label={fullscreen ? "Exit full screen" : "Full screen"} onClick={toggleFullscreen}>{fullscreen ? <Shrink size={18} /> : <Expand size={18} />}</MapButton>}
      </Glass>
      <Glass className="flex flex-col overflow-hidden rounded-[14px] divide-y divide-black/[0.08]">
        <MapButton label="Zoom in" onClick={() => handle.current?.zoomBy(1)}><Plus size={18} /></MapButton>
        <MapButton label="Zoom out" onClick={() => handle.current?.zoomBy(-1)}><Minus size={18} /></MapButton>
      </Glass>
    </div>

    {/* Quiet status pill when there is no satellite imagery. */}
    {status?.provider === "osm" && !narrow && <button type="button" onClick={() => setPopover("style")} className="absolute left-[calc(50%+196px)] top-3 z-[999] -translate-x-1/2">
      <Glass className="flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[12.5px] text-black/60"><Layers size={14} />Standard map · <span className="text-[#007AFF]">Turn on satellite</span></Glass></button>}

    {/* Drawing bar and toasts (bottom centre). */}
    {(draft || measure || tool === "place_subject") && <div className={`absolute left-1/2 z-[1001] -translate-x-1/2 ${narrow ? "top-3" : "bottom-8"}`} role="status" aria-live="polite">
      <Glass className="flex max-w-[92vw] flex-wrap items-center gap-x-3 gap-y-1 rounded-full px-4 py-2 text-[14px] text-black/80">
        {tool === "place_subject" && <><span>Tap the map to drop the pin</span><button type="button" className="text-[#007AFF]" onClick={() => setTool("browse")}>Cancel</button></>}
        {draft && <><span className="font-medium">{draft.tool === "measure" ? "Measure" : draft.tool === "draw_area" ? "Search area" : "Site outline"}</span>
          <span className="text-black/50">{draft.points.length} points{draftMeasure != null ? ` · ≈ ${draft.tool === "measure" ? formatDistance(draftMeasure) : formatArea(draftMeasure)}` : ""}</span>
          <button type="button" className="text-[#007AFF]" onClick={addCentreVertex} title="Adds a point at the centre of the map (keyboard alternative)">Add centre</button>
          <button type="button" className="text-[#007AFF] disabled:text-black/25" disabled={!draft.points.length} onClick={() => setDraft(d => d && { ...d, points: d.points.slice(0, -1) })}>Undo</button>
          <button type="button" className="rounded-full bg-[#007AFF] px-3 py-1 font-medium text-white disabled:bg-black/15" disabled={draft.tool === "measure" ? draft.points.length < 2 : draft.points.length < 3} onClick={finishDraft}>Done</button>
          <button type="button" aria-label="Cancel drawing" className="text-black/40" onClick={() => { setDraft(null); setTool("browse"); }}><X size={16} /></button></>}
        {!draft && measure && tool !== "place_subject" && <><span>≈ {formatDistance(pathLengthMeters(measure))}</span><span className="text-black/40">approximate</span><button type="button" aria-label="Clear measurement" className="text-black/40" onClick={() => setMeasure(null)}><X size={16} /></button></>}
      </Glass></div>}
    {notice && <div className="absolute left-1/2 top-16 z-[1002] -translate-x-1/2" role="status"><Glass className="rounded-full px-4 py-2 text-[14px] text-black/80">{notice}</Glass></div>}

    {ws.panels.table && !narrow && <Glass className="absolute bottom-3 left-[404px] right-20 z-[999] h-[38%] overflow-hidden rounded-[18px]" aria-label="Evidence table">
      <div className="flex items-center justify-between px-4 py-2"><h2 className="text-[15px] font-semibold text-black/85">Evidence table <span className="font-normal text-black/40">· {listed.length}</span></h2>
        <button type="button" aria-label="Close table" className="text-black/40" onClick={() => setPanels({ table: false })}><X size={18} /></button></div>
      <div className="h-[calc(100%-40px)] bg-white"><EvidenceTable records={listed} selectedId={ws.selectedId} onSelect={selectRecord} subject={subjectPoint} /></div>
    </Glass>}
  </div>;
}

function MapButton({ label, onClick, pressed, children }: { label: string; onClick: () => void; pressed?: boolean; children: React.ReactNode }) {
  return <button type="button" aria-label={label} title={label} aria-pressed={pressed} onClick={onClick}
    className={`grid h-11 w-11 place-items-center ${pressed ? "text-[#007AFF]" : "text-black/70"} hover:bg-black/[0.04] active:bg-black/[0.08]`}>{children}</button>;
}

export default function MapPage() { return <Suspense fallback={<div className="h-full bg-[#e8e6e1]" />}><MapWorkspace /></Suspense>; }
