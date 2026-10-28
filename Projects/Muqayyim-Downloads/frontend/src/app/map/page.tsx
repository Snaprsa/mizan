"use client";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getMapRecords, MapRecord, MapResponse, getValuationCatalog, startMapAnalysis, ValuationMethod, PreparedAnalysis } from "@/lib/api";
import ValuationWorkflow from "@/components/valuation-workflow";
import { MapBounds, COLORS, inBounds, googleMapsUrl } from "@/lib/map-utils";
const EvidenceMap = dynamic(() => import("@/components/intelligence-map"), { ssr: false, loading: () => <div className="mizan-panel h-[600px] text-sm">Loading map…</div> });
const LABELS = { property: "Properties", transaction: "Recorded transactions", listing: "Asking-price listings", other: "Other comparables", market: "Market observations" };
const money = (n: number | null, currency = "SAR") => n == null ? "Not recorded" : `${currency} ${new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(n)}`;
function safeSource(s: string) { return /^https?:\/\//i.test(s) ? s : null; }

function MapWorkspace() {
  const params = useSearchParams(); const router = useRouter(); const caseId = params.get("case_id") || "";
  const analysisId = params.get("analysis") || "";
  const [methods, setMethods] = useState<ValuationMethod[]>([]); const [propertyTypes, setPropertyTypes] = useState<string[]>([]);
  const [subject, setSubject] = useState<[number, number] | null>(null); const [pickMode, setPickMode] = useState(!analysisId);
  const [subjectType, setSubjectType] = useState(""); const [approach, setApproach] = useState("sales_comparison");
  const [starting, setStarting] = useState(false); const [prepared, setPrepared] = useState<PreparedAnalysis | null>(null);
  useEffect(() => { getValuationCatalog().then(c => { setMethods(c.methods); setPropertyTypes(c.property_types); }).catch(e => setError(e.message)); }, []);
  const onPrepared = useCallback((p: PreparedAnalysis) => { setPrepared(p); setSubject(p.coordinates); setSubjectType(p.property_type); setApproach(p.method); }, []);
  function analysisUrl(id: string | null) { const next = new URLSearchParams(params.toString()); if (id) next.set("analysis", id); else next.delete("analysis"); router.replace(`/map${next.toString() ? "?" + next : ""}`, { scroll: false }); }
  const onPick = useCallback((coordinates: [number, number]) => {
    setSubject(coordinates); setPickMode(false); setPrepared(null);
    const next = new URLSearchParams(window.location.search); next.delete("analysis");
    router.replace(`/map${next.toString() ? "?" + next : ""}`, { scroll: false });
  }, [router]);
  async function start() {
    if (!subject || !subjectType || !approach) return;
    setStarting(true); setError("");
    try { const p = await startMapAnalysis({ latitude: subject[0], longitude: subject[1], property_type: subjectType, method: approach, ...(city ? { city } : {}) });
      onPrepared(p); analysisUrl(p.property_id);
      getMapRecords({ q, city, property_type: type, date_from: from, date_to: to, case_id: caseId }).then(setData).catch(e => setError(e.message));
    } catch (e) { setError((e as Error).message); } finally { setStarting(false); }
  }
  const [data, setData] = useState<MapResponse | null>(null); const [error, setError] = useState("");
  const [loading, setLoading] = useState(true); const [q, setQ] = useState("");
  const [city, setCity] = useState(""); const [type, setType] = useState("");
  const [from, setFrom] = useState(""); const [to, setTo] = useState("");
  const [layers, setLayers] = useState<Record<MapRecord["kind"], boolean>>({ property: true, transaction: true, listing: true, other: true, market: true });
  const [bounds, setBounds] = useState<MapBounds | null>(null); const [withinView, setWithinView] = useState(false);
  const [selected, setSelected] = useState<string | null>(null); const [cluster, setCluster] = useState<string[]>([]);
  const [fitKey, setFitKey] = useState(0); const [page, setPage] = useState(0);
  useEffect(() => { let current = true; const controller = setTimeout(() => {
    setLoading(true); setError("");
    getMapRecords({ q, city, property_type: type, date_from: from, date_to: to, case_id: caseId })
      .then(r => { if (current) { setData(r); setPage(0); setCluster([]); } })
      .catch(e => { if (current) { setError(e.message); setData(null); } })
      .finally(() => { if (current) setLoading(false); });
    }, 200);
    return () => { current = false; clearTimeout(controller); };
  }, [q, city, type, from, to, caseId]);
  const onSelect = useCallback((id: string) => setSelected(id), []);
  const onCluster = useCallback((ids: string[]) => { setCluster(ids); setPage(0); }, []);
  const onBounds = useCallback((b: MapBounds) => setBounds(b), []);
  const visible = useMemo(() => (data?.data || []).filter(r => layers[r.kind]), [data, layers]);
  const inside = useMemo(() => visible.filter(r => inBounds(r, bounds)), [visible, bounds]);
  const results = useMemo(() => visible.filter(r => (!withinView || inBounds(r, bounds)) && (!cluster.length || cluster.includes(r.id))), [visible, withinView, bounds, cluster]);
  const current = visible.find(r => r.id === selected);
  const mapped = visible.filter(r => r.coordinates).length; const missing = visible.length - mapped;
  const areas = useMemo(() => {
    const groups = new Map<string, { city: string; district: string; records: number; transactions: number; listings: number }>();
    for (const r of inside) { const key = `${r.city || "Unknown city"}|${r.district || "Unknown district"}`;
      const g = groups.get(key) || { city: r.city || "Unknown city", district: r.district || "Unknown district", records: 0, transactions: 0, listings: 0 };
      g.records++; if (r.kind === "transaction") g.transactions++; if (r.kind === "listing") g.listings++; groups.set(key, g); }
    return Array.from(groups.values()).sort((a, b) => b.records - a.records);
  }, [inside]);
  function recent(days: number) {
    const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Riyadh", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    const start = new Date(`${today}T12:00:00Z`); start.setUTCDate(start.getUTCDate() - days);
    setTo(today); setFrom(start.toISOString().slice(0, 10));
  }
  return <div className="space-y-4">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-semibold">Property intelligence map <span className="text-lg text-slate-400" lang="ar" dir="rtl">الخريطة العقارية</span></h1>
      <p className="text-sm text-slate-500 mt-1">Select a location, property type and approach. Mizan gathers evidence and shows the inputs needed for that method.</p></div><Link className="text-sm text-blue-700" href="/properties">Manage properties →</Link></header>
    <section className="mizan-panel !p-4 border-blue-200" aria-label="Start valuation from the map"><div className="grid md:grid-cols-[1fr_1fr_1.3fr_auto] gap-3 items-end">
      <div><p className="mizan-label mb-1">1 · Subject location</p><button type="button" className={`w-full px-3 py-2 text-sm border rounded ${pickMode ? "bg-blue-600 text-white" : "text-blue-700 bg-blue-50 border-blue-200"}`} onClick={() => setPickMode(v => !v)}>{pickMode ? "Click the map to place the subject" : subject ? "Choose another location" : "Select location on map"}</button><p className="text-[10px] text-slate-500 mt-1">{subject ? subject.map(n => n.toFixed(5)).join(", ") : "Click the map to place the subject pin."}</p></div>
      <label className="mizan-label">2 · Subject property type<select aria-label="Subject property type" className="mizan-input" value={subjectType} disabled={!!analysisId} onChange={e => setSubjectType(e.target.value)}><option value="">Choose property type</option>{propertyTypes.map(t => <option key={t} value={t}>{t.replaceAll("_", " ")}</option>)}</select></label>
      <label className="mizan-label">3 · Choose valuation approach<select aria-label="Choose valuation approach" className="mizan-input" value={approach} disabled={!!analysisId} onChange={e => setApproach(e.target.value)}>{methods.map(m => <option value={m.key} key={m.key} disabled={!m.implemented}>{m.label}{!m.implemented ? " · not yet implemented" : ""}</option>)}</select></label>
      <button type="button" className="mizan-button" disabled={starting || !subject || !subjectType || !!analysisId} onClick={start}>{starting ? "Preparing…" : analysisId ? "Analysis open below" : "Start valuation"}</button>
    </div>{analysisId && <p className="text-xs text-slate-500 mt-2">Inputs and results appear beside the same map. <button type="button" className="text-blue-700 underline" onClick={() => { analysisUrl(null); setPrepared(null); setPickMode(true); }}>Start a new subject</button></p>}</section>
    {caseId && <p className="text-xs text-blue-800 bg-blue-50 rounded p-2">Showing this case&apos;s comparables and linked properties. <Link href="/map" className="underline">Show all cases</Link></p>}
    <div className="mizan-panel !p-4 space-y-3"><div className="grid grid-cols-2 xl:grid-cols-5 gap-3">
      <label className="mizan-label">Search evidence<input className="mizan-input" type="search" value={q} onChange={e => setQ(e.target.value)} placeholder="Name, district, source…" /></label>
      <label className="mizan-label">City<select aria-label="City" className="mizan-input" value={city} onChange={e => setCity(e.target.value)}><option value="">All cities</option>{data?.available.cities.map(c => <option key={c}>{c}</option>)}</select></label>
      <label className="mizan-label">Property type<select aria-label="Property type" className="mizan-input" value={type} onChange={e => setType(e.target.value)}><option value="">All types</option>{data?.available.property_types.map(t => <option key={t}>{t}</option>)}</select></label>
      <label className="mizan-label">Evidence from<input aria-label="Evidence from" className="mizan-input" type="date" value={from} onChange={e => setFrom(e.target.value)} /></label>
      <label className="mizan-label">Evidence to<input aria-label="Evidence to" className="mizan-input" type="date" value={to} onChange={e => setTo(e.target.value)} /></label>
    </div><div className="flex flex-wrap gap-x-5 gap-y-2 items-center text-xs">{(Object.keys(LABELS) as MapRecord["kind"][]).map(k => <label key={k} className="flex items-center gap-2"><input type="checkbox" checked={layers[k]} onChange={e => { setLayers({ ...layers, [k]: e.target.checked }); setCluster([]); setPage(0); }} /><span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[k] }} />{LABELS[k]}</label>)}
      <span className="text-slate-400">Period:</span>{[30, 90, 365].map(days => <button key={days} className="text-blue-700 hover:underline" onClick={() => recent(days)}>Last {days} days</button>)}<button className="text-blue-700 hover:underline" onClick={() => { setFrom(""); setTo(""); }}>All dates</button>
    </div><p className="text-[11px] text-slate-500">Date filters use the transaction date, listing date or property collection date. Undated records are excluded when a period is selected. Invalid/outlier comparables are excluded.</p></div>
    {error && <p role="alert" className="mizan-error">{error}</p>}
    {loading && <p role="status" className="text-sm text-slate-500">Updating map evidence…</p>}
    {data?.truncated && <p role="status" className="text-sm text-amber-800">Showing the first {data.data.length} of {data.total} matching records. Refine the filters to include a smaller area or period.</p>}
    <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-600" aria-live="polite"><span><strong className="text-slate-900">{visible.length}</strong> loaded records</span><span><strong>{mapped}</strong> located</span><span><strong>{missing}</strong> location missing</span><span><strong>{inside.length}</strong> records in map view</span><span><strong>{inside.filter(r => r.kind === "transaction").length}</strong> recorded transactions in view</span></div>
    <div className="grid lg:grid-cols-[minmax(0,1fr)_340px] gap-4 items-start">
      <div className="space-y-3 min-w-0 lg:sticky lg:top-3"><div className="mizan-panel !p-2"><div className="flex justify-between items-center px-2 pb-2"><h2 className="text-xs font-semibold">Map · {mapped} located records</h2><button className="text-xs text-blue-700" onClick={() => { setFitKey(v => v + 1); setCluster([]); }}>Fit all locations</button></div><div className="h-[570px] min-h-[440px]"><div className="relative h-full"><EvidenceMap records={visible} selected={selected} fitKey={fitKey} onSelect={onSelect} onBounds={onBounds} onCluster={onCluster} pickMode={pickMode} subject={subject} radiusKm={prepared?.radius_km || 3} onPick={onPick} />
          <div className="absolute bottom-9 left-3 z-[450] max-w-[290px] bg-white/95 border border-slate-200 rounded px-3 py-2 text-[11px] shadow-sm" aria-label="Data coverage on map"><p className="font-semibold text-slate-800">All saved data · coverage</p><p>{data?.coverage?.properties || 0} properties · {data?.coverage?.comparables || 0} comparables · {data?.coverage?.market_observations || 0} market observations</p><p className="text-slate-500">{data?.coverage?.missing_location || 0} records lack exact locations · {data?.coverage?.unverified_datasets || 0} local files await review</p><a className="text-blue-700 underline" href="#map-data-coverage">View data coverage and missing locations</a></div></div></div></div>
        {!mapped && !loading && <p className="text-xs text-slate-600">No coordinates are available for these filters. The map is centered on Saudi Arabia for navigation; no evidence pins are inferred from city or district names.</p>}
        <details className="mizan-panel !p-3"><summary className="text-sm font-medium cursor-pointer">Activity in the visible area ({areas.length} district groups)</summary><p className="text-xs text-slate-500 my-2">Counts reflect your saved records in the current map view and period, not all Saudi market activity. Repeated sources can describe the same property.</p><table className="mizan-table"><thead><tr><th>City / district</th><th>Records</th><th>Transactions</th><th>Listings</th></tr></thead><tbody>{areas.map(g => <tr key={g.city+g.district}><td>{g.city} / {g.district}</td><td>{g.records}</td><td>{g.transactions}</td><td>{g.listings}</td></tr>)}</tbody></table>{!areas.length && <p className="text-xs text-slate-500 mt-2">No located records in this view.</p>}</details>
      </div>
      <aside className="space-y-3 min-w-0" aria-label="Comparables beside the map">
        {analysisId && <ValuationWorkflow key={analysisId} propertyId={analysisId} methods={methods} onPrepared={onPrepared} onSelectEvidence={onSelect} />}
        {current && <section className="mizan-panel !p-4 border-blue-300"><div className="flex justify-between gap-3"><h2 className="font-medium text-sm">{current.title}</h2><button aria-label="Clear selected record" onClick={() => setSelected(null)}>×</button></div>
          <p className="text-xs text-slate-500 mt-1">{LABELS[current.kind]} · {current.status}</p>{current.kind === "property" && <button type="button" className="text-xs text-blue-700 underline mt-2" onClick={() => analysisUrl(current.entity_id)}>Use this property as valuation subject</button>}
          {current.kind === "market" && <p className="text-sm font-medium mt-2">{String(current.value)} {current.unit} · source reliability {current.reliability_percent}/100</p>}
          <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs my-3"><dt className="text-slate-500">{current.kind === "property" || current.kind === "listing" ? "Asking price" : current.kind === "transaction" ? "Transacted price" : "Price"}</dt><dd>{money(current.price, current.currency)}</dd><dt className="text-slate-500">Price / m²</dt><dd>{money(current.price_per_sqm, current.currency)}</dd><dt className="text-slate-500">Area</dt><dd>{current.area_sqm == null ? "Not recorded" : `${current.area_sqm.toLocaleString()} m²`}</dd><dt className="text-slate-500">Evidence date</dt><dd>{current.date || "Not recorded"}</dd><dt className="text-slate-500">Date basis</dt><dd>{current.date_basis.replaceAll("_", " ")}</dd><dt className="text-slate-500">Coordinates</dt><dd>{current.coordinates?.map(n => n.toFixed(5)).join(", ") || "Missing"}</dd><dt className="text-slate-500">Source reliability</dt><dd>{current.reliability_score == null ? "Not scored" : `${current.reliability_score}/5 · source scale`}</dd></dl>
          <p className="text-xs break-all text-slate-500 mb-3">Source: {safeSource(current.source) ? <a className="text-blue-700 underline" href={safeSource(current.source)!} target="_blank" rel="noopener noreferrer">{current.source}</a> : current.source}</p>
          <div className="flex flex-wrap gap-3 text-xs"><Link className="text-blue-700 underline" href={current.href}>Open {current.kind === "property" ? "property" : current.kind === "market" ? "market data" : "evidence case"}</Link>{(current.coordinates || current.city || current.district) && <a className="text-blue-700 underline" href={googleMapsUrl(current)} target="_blank" rel="noopener noreferrer">{current.coordinates ? "Open in Google Maps ↗" : "Search area in Google Maps ↗"}</a>}</div>
          {!current.coordinates && <p className="text-xs text-amber-800 mt-3">Location missing. Add coordinates in the property workspace or comparable evidence; Google area search is approximate.</p>}
        </section>}
        <div className="mizan-panel !p-3"><div className="flex justify-between gap-2"><h2 className="font-semibold text-sm">Evidence alongside map ({results.length})</h2>{cluster.length > 0 && <button className="text-xs text-blue-700" onClick={() => setCluster([])}>Clear group</button>}</div>
          <label className="flex gap-2 items-center text-xs text-slate-600 my-3"><input type="checkbox" checked={withinView} onChange={e => { setWithinView(e.target.checked); setPage(0); }} />Only records in current map view</label>
          <div className="max-h-[520px] overflow-auto space-y-1">{results.slice(page * 30, (page + 1) * 30).map(r => <button key={r.id} data-record-id={r.id} onClick={() => setSelected(r.id)} aria-pressed={selected === r.id} className={`w-full text-left rounded border p-3 ${selected === r.id ? "border-blue-400 bg-blue-50" : "border-slate-200 hover:bg-slate-50"}`}>
            <div className="flex gap-2 items-start"><span className="mt-1 h-2 w-2 shrink-0 rounded-full" style={{ background: COLORS[r.kind] }} /><span className="text-sm font-medium break-words">{r.title}</span></div>
            <p className="text-xs text-slate-500 mt-1">{[r.city, r.district, r.property_type].filter(Boolean).join(" · ") || "Geography not recorded"}</p><p className="text-xs text-slate-700 mt-1">{r.kind === "market" ? `${String(r.value)} ${r.unit || ""}` : money(r.price, r.currency)} · {r.date || "Date unknown"}</p><p className="text-[11px] text-slate-500 mt-1">{LABELS[r.kind]} · {r.status}{!r.coordinates ? " · Location missing" : ""}</p>
          </button>)}{!results.length && !loading && <p className="text-sm text-slate-500 py-5">No matching evidence. Try all dates, clear the group or widen the map view.</p>}</div>
          {results.length > 30 && <div className="flex justify-between text-xs mt-3"><button disabled={!page} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page + 1}</span><button disabled={(page + 1) * 30 >= results.length} onClick={() => setPage(page + 1)}>Next</button></div>}
        </div>
      </aside>
    </div>
    <details id="map-data-coverage" className="mizan-panel !p-4"><summary className="text-sm font-semibold cursor-pointer">Data coverage: located records, area-only data and unreviewed files</summary><p className="text-xs text-slate-500 my-3">All saved properties, comparables and market observations are included before filters. Exact locations become pins. Area-level data and records without coordinates stay in the adjacent list; district centres are never presented as exact property locations.</p><p className="text-xs mb-3">{data?.coverage?.missing_location || 0} records lack exact coordinates. Filters currently load {visible.length} records.</p><h3 className="text-xs font-semibold">Existing local datasets · not imported as market evidence</h3><table className="mizan-table mt-2"><thead><tr><th>Dataset</th><th>Review status</th></tr></thead><tbody>{data?.coverage?.datasets.map(d => <tr key={d.path}><td>{d.name}</td><td>Unverified · not imported</td></tr>)}</tbody></table><Link href="/data" className="inline-block text-xs text-blue-700 mt-3">Manage sources and import reviewed observations →</Link></details>
    <p className="text-xs text-slate-500">The map displays Mizan&apos;s saved evidence, not a live transaction feed. Asking prices are not achieved sales. Transaction counts require a recorded transaction type, achieved price and transaction date. Tile basemap: OpenStreetMap; Google Maps opens separately.</p>
  </div>;
}

export default function MapPage() { return <Suspense fallback={<p>Loading map filters…</p>}><MapWorkspace /></Suspense>; }
