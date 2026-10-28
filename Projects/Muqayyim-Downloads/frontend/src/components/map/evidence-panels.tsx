"use client";
// Inspector panels: selected record, evidence summaries/list, data coverage and the linked table.
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { MapRecord, MapResponse } from "@/lib/api";
import { formatDistance, haversineMeters, type LatLng } from "@/lib/geo";
import { activityCounts, evidenceSummaries, LAYER, MIN_SUMMARY_SAMPLE, riyadhToday, sourceLabel, type Summary } from "@/lib/map-evidence";

const n0 = new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 });
export const money = (n: number | null | undefined, currency = "SAR") => n == null ? "—" : `${currency} ${n0.format(n)}`;
const PRECISION_LABEL: Record<string, string> = { source_reported: "As reported by source (unverified)", user_selected: "Selected by user on map",
  rooftop: "Rooftop (geocoder)", range_interpolated: "Interpolated (geocoder)", geometric_center: "Area centre (geocoder)", approximate: "Approximate",
  exact: "Exact (source)", property: "Property-level (source)", area: "Area-level only", missing: "No location", unspecified: "Precision not recorded" };
export const precisionLabel = (p?: string) => PRECISION_LABEL[p || "unspecified"] || p || "Precision not recorded";
const isFuture = (d: string | null) => !!d && d > riyadhToday();
const safeUrl = (s: string) => /^https?:\/\//i.test(s) ? s : null;
const priceLabel = (r: MapRecord) => r.kind === "transaction" ? "Achieved price" : r.kind === "listing" || r.kind === "property" ? "Asking price" : "Price";

export function SelectedRecord({ record, subject, onClear, onUseAsSubject, compact = false, onExpand }: { record: MapRecord; subject: LatLng | null; onClear: () => void; onUseAsSubject: (r: MapRecord) => void; compact?: boolean; onExpand?: () => void }) {
  const layer = LAYER[record.kind];
  if (compact) return <div className="flex items-center gap-2 border-b border-slate-200 bg-blue-50/40 px-4 py-1.5 text-xs" aria-label="Selected record">
    <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: layer.color }} /><span className="font-medium truncate" dir="auto">{record.title}</span>
    <span className="text-slate-500 whitespace-nowrap">{record.price_per_sqm == null ? money(record.price, record.currency) : `${n0.format(record.price_per_sqm)} /m²`}</span>
    {onExpand && <button type="button" className="ml-auto text-blue-700 underline whitespace-nowrap" onClick={onExpand}>Details</button>}
    <button type="button" className="text-slate-400 hover:text-slate-700 px-1" aria-label="Clear selected record" onClick={onClear}>×</button></div>;
  return <section className="border-b border-slate-200 bg-blue-50/40 px-4 py-3" aria-label="Selected record">
    <div className="flex items-start gap-2"><span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: layer.color }} />
      <div className="min-w-0 flex-1"><h3 className="text-sm font-semibold break-words" dir="auto">{record.title}</h3>
        <p className="text-[11px] text-slate-500">{layer.label} · {record.status}</p></div>
      <button type="button" className="text-slate-400 hover:text-slate-700 text-lg leading-none px-1" aria-label="Clear selected record" onClick={onClear}>×</button></div>
    {record.kind === "market" ? <p className="text-sm font-medium mt-2">{String(record.value)} {record.unit} <span className="text-xs text-slate-500">· source reliability {record.reliability_percent ?? "—"}/100</span></p> : null}
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs mt-2">
      <dt className="text-slate-500">{priceLabel(record)}</dt><dd>{money(record.price, record.currency)}</dd>
      <dt className="text-slate-500">Unit value</dt><dd>{record.price_per_sqm == null ? "—" : `${money(record.price_per_sqm, record.currency)}/m²`}</dd>
      <dt className="text-slate-500">Area</dt><dd>{record.area_sqm == null ? "—" : `${n0.format(record.area_sqm)} m²`}</dd>
      <dt className="text-slate-500">Date</dt><dd>{record.date || "Not recorded"} <span className="text-slate-400">({record.date_basis.replaceAll("_", " ")})</span>{isFuture(record.date) && <span className="block text-amber-800">After today — check the source date.</span>}</dd>
      <dt className="text-slate-500">Location</dt><dd>{record.coordinates ? record.coordinates.map(v => v.toFixed(5)).join(", ") : "Missing"} <span className="text-slate-400">· {precisionLabel(record.location_precision)}</span></dd>
      {subject && record.coordinates && <><dt className="text-slate-500">To subject</dt><dd>≈ {formatDistance(haversineMeters(subject, record.coordinates))}</dd></>}
      <dt className="text-slate-500">Reliability</dt><dd>{record.reliability_score == null ? "Not scored" : `${record.reliability_score}/5 (source scale)`}</dd>
      <dt className="text-slate-500">Source</dt><dd className="break-all">{safeUrl(record.source) ? <a className="text-blue-700 underline" href={record.source} target="_blank" rel="noopener noreferrer">{sourceLabel(record.source)}</a> : record.source}</dd>
    </dl>
    <div className="flex flex-wrap gap-3 text-xs mt-2">
      <Link className="text-blue-700 underline" href={record.href}>Open {record.kind === "property" ? "property" : record.kind === "market" ? "market data" : "evidence case"}</Link>
      {record.kind === "property" && <button type="button" className="text-blue-700 underline" onClick={() => onUseAsSubject(record)}>Use as valuation subject</button>}
    </div>
    {!record.coordinates && <p className="text-xs text-amber-800 mt-2">No exact location. Add coordinates in the {record.kind === "property" ? "property workspace" : "evidence review"}; no pin is inferred from the city or district.</p>}
  </section>;
}

function SummaryRow({ s }: { s: Summary }) {
  return <tr><td>{s.label}<span className="block text-[10px] text-slate-400">{s.unit}</span></td><td>{s.withValue}/{s.n}</td>
    <td>{s.insufficient ? <span className="text-slate-400" title={`At least ${MIN_SUMMARY_SAMPLE} records with a unit value are needed`}>insufficient</span> : n0.format(s.median!)}</td>
    <td className="text-slate-500">{s.insufficient ? "—" : `${n0.format(s.p25!)}–${n0.format(s.p75!)}`}</td>
    <td className="text-slate-500 whitespace-nowrap">{s.from ? `${s.from.slice(0, 7)}${s.to !== s.from ? `…${s.to!.slice(0, 7)}` : ""}` : "—"}</td></tr>;
}

export function EvidenceSummary({ records, scopeLabel, today }: { records: MapRecord[]; scopeLabel: string; today: string }) {
  const summaries = useMemo(() => evidenceSummaries(records), [records]);
  const activity = useMemo(() => activityCounts(records, today), [records, today]);
  const located = records.filter(r => r.coordinates && r.kind === "transaction" && r.price_per_sqm != null).length;
  return <details className="border-b border-slate-200 px-4 py-2" open>
    <summary className="text-xs font-semibold text-slate-700 cursor-pointer">Activity & unit values · {scopeLabel}</summary>
    <table className="w-full text-[11px] mt-2"><thead className="text-slate-500"><tr><th className="text-left font-medium">Window</th><th className="text-left font-medium">Sales</th><th className="text-left font-medium">Listings</th><th className="text-left font-medium">Other</th></tr></thead>
      <tbody>{activity.map(a => <tr key={a.days}><td>Last {a.days} days</td><td>{a.transactions}</td><td>{a.listings}</td><td>{a.other}</td></tr>)}</tbody></table>
    {summaries.length > 0 ? <table className="w-full text-[11px] mt-3 [&_td]:py-0.5 [&_td]:pr-2"><thead className="text-slate-500"><tr><th className="text-left font-medium">Evidence</th><th className="text-left font-medium">n</th><th className="text-left font-medium">Median</th><th className="text-left font-medium">IQR</th><th className="text-left font-medium">Period</th></tr></thead>
      <tbody>{summaries.map(s => <SummaryRow key={s.key} s={s} />)}</tbody></table>
      : <p className="text-[11px] text-slate-500 mt-2">No sale, listing or observation values in this scope.</p>}
    <p className="text-[10px] text-slate-500 mt-2">Saved Mizan records only, counted per record (the same property may appear in several sources). Sales, asking prices and observations are summarised separately. Price surface/heatmap: {located >= 20 ? "available when enabled" : `unavailable — needs ≥ 20 located achieved sales with SAR/m² (currently ${located})`}.</p>
  </details>;
}

export function EvidenceList({ records, selectedId, onSelect, subject, groupActive, onClearGroup }: {
  records: MapRecord[]; selectedId: string | null; onSelect: (r: MapRecord) => void; subject: LatLng | null; groupActive: boolean; onClearGroup: () => void }) {
  const [page, setPage] = useState(0); const size = 40;
  useEffect(() => setPage(0), [records]);
  useEffect(() => { if (!selectedId) return; const i = records.findIndex(r => r.id === selectedId); if (i >= 0) setPage(Math.floor(i / size));
    requestAnimationFrame(() => document.querySelector(`[data-record-id="${CSS.escape(selectedId)}"]`)?.scrollIntoView({ block: "nearest" })); }, [selectedId, records]);
  return <div className="px-2 py-2">
    {groupActive && <div className="mx-2 mb-2 flex justify-between text-xs bg-sky-50 border border-sky-200 rounded px-2 py-1"><span>Showing a map cluster ({records.length})</span><button type="button" className="text-blue-700 underline" onClick={onClearGroup}>Show all</button></div>}
    <ul className="space-y-0.5" aria-label="Evidence records">{records.slice(page * size, (page + 1) * size).map(r => <li key={r.id}>
      <button type="button" data-record-id={r.id} aria-pressed={selectedId === r.id} onClick={() => onSelect(r)}
        className={`w-full text-left rounded px-2 py-1.5 border ${selectedId === r.id ? "border-blue-400 bg-blue-50" : "border-transparent hover:bg-slate-50"}`}>
        <div className="flex items-center gap-2"><span className="h-2 w-2 shrink-0 rounded-full" style={{ background: LAYER[r.kind].color }} />
          <span className="text-[13px] font-medium truncate flex-1" dir="auto">{r.title}</span>
          <span className="text-[11px] text-slate-600 whitespace-nowrap">{r.kind === "market" ? `${String(r.value)} ${r.unit || ""}` : r.price_per_sqm != null ? `${n0.format(r.price_per_sqm)} /m²` : money(r.price, r.currency)}</span></div>
        <div className="flex gap-2 pl-4 text-[11px] text-slate-500"><span className="truncate">{[LAYER[r.kind].short, r.district || r.city, r.property_type].filter(Boolean).join(" · ")}</span>
          <span className={`ml-auto whitespace-nowrap ${isFuture(r.date) ? "text-amber-800" : ""}`} title={isFuture(r.date) ? "Date is after today; check the source" : undefined}>{r.date || "undated"}{isFuture(r.date) ? " (future)" : ""}{subject && r.coordinates ? ` · ${formatDistance(haversineMeters(subject, r.coordinates))}` : ""}{!r.coordinates ? " · no location" : ""}</span></div>
      </button></li>)}</ul>
    {!records.length && <p className="text-xs text-slate-500 px-2 py-6 text-center">No matching evidence. Widen the map, clear filters or turn layers on.</p>}
    {records.length > size && <div className="flex justify-between items-center text-xs px-2 pt-2"><button type="button" disabled={!page} className="text-blue-700 disabled:text-slate-300" onClick={() => setPage(page - 1)}>← Previous</button>
      <span className="text-slate-500">{page * size + 1}–{Math.min(records.length, (page + 1) * size)} of {records.length}</span>
      <button type="button" disabled={(page + 1) * size >= records.length} className="text-blue-700 disabled:text-slate-300" onClick={() => setPage(page + 1)}>Next →</button></div>}
  </div>;
}

export function CoveragePanel({ data, unlocated, onSelect }: { data: MapResponse | null; unlocated: MapRecord[]; onSelect: (r: MapRecord) => void }) {
  const [q, setQ] = useState("");
  const queue = unlocated.filter(r => !q || [r.title, r.city, r.district, r.source].some(v => v?.toLowerCase().includes(q.toLowerCase())));
  const c = data?.coverage;
  return <div className="px-4 py-3 space-y-4 text-xs">
    <section><h3 className="font-semibold text-slate-700 mb-1">All saved data</h3>
      <p>{c?.properties ?? 0} properties · {c?.comparables ?? 0} comparables · {c?.market_observations ?? 0} market observations</p>
      <p className="text-slate-500 mt-1">Exact or source-reported locations become pins. Area-level observations and records without coordinates stay listed here; district centres are never shown as property locations.</p></section>
    <section><h3 className="font-semibold text-slate-700 mb-1">Location-resolution queue ({unlocated.length})</h3>
      <input className="mizan-compact-input mb-2" type="search" placeholder="Search unlocated records" aria-label="Search unlocated records" value={q} onChange={e => setQ(e.target.value)} />
      <ul className="max-h-64 overflow-auto divide-y divide-slate-100 border border-slate-200 rounded">{queue.map(r => <li key={r.id}>
        <button type="button" className="w-full text-left px-2 py-1.5 hover:bg-slate-50" onClick={() => onSelect(r)}>
          <span className="font-medium" dir="auto">{r.title}</span><span className="block text-[11px] text-slate-500">{LAYER[r.kind].short} · {[r.city, r.district].filter(Boolean).join(" / ") || "no geography"} · {precisionLabel(r.location_precision)}</span></button>
        <Link href={r.href} className="block px-2 pb-1.5 text-[11px] text-blue-700 underline">Resolve in {r.kind === "property" ? "property workspace" : r.kind === "market" ? "market data" : "evidence review"}</Link></li>)}
        {!queue.length && <li className="px-2 py-3 text-slate-500">Nothing to resolve for the current filters.</li>}</ul></section>
    <section><h3 className="font-semibold text-slate-700 mb-1">Local files awaiting review ({c?.unverified_datasets ?? 0})</h3>
      <p className="text-slate-500 mb-2">Not imported as market evidence. Grain, licensing, age and synthetic status must be reviewed first.</p>
      <ul className="max-h-48 overflow-auto divide-y divide-slate-100 border border-slate-200 rounded">{c?.datasets.map(d => <li key={d.path} className="px-2 py-1.5"><span className="font-medium break-all">{d.name}</span><span className="block text-[11px] text-slate-500">Unverified · not imported</span></li>)}</ul>
      <Link href="/data" className="inline-block mt-2 text-blue-700 underline">Manage sources and import reviewed observations →</Link></section>
  </div>;
}

type SortKey = "date" | "price_per_sqm" | "distance" | "title";
export function EvidenceTable({ records, selectedId, onSelect, subject }: { records: MapRecord[]; selectedId: string | null; onSelect: (r: MapRecord) => void; subject: LatLng | null }) {
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "date", dir: -1 });
  const rows = useMemo(() => {
    const value = (r: MapRecord) => sort.key === "date" ? r.date || "" : sort.key === "title" ? r.title.toLowerCase()
      : sort.key === "price_per_sqm" ? r.price_per_sqm ?? -Infinity : subject && r.coordinates ? haversineMeters(subject, r.coordinates) : Infinity;
    return records.slice().sort((a, b) => { const x = value(a); const y = value(b); return (x < y ? -1 : x > y ? 1 : 0) * sort.dir; }).slice(0, 200);
  }, [records, sort, subject]);
  const head = (key: SortKey, label: string) => <th aria-sort={sort.key === key ? (sort.dir === 1 ? "ascending" : "descending") : "none"}>
    <button type="button" className="hover:text-slate-800" onClick={() => setSort(s => ({ key, dir: s.key === key ? (s.dir === 1 ? -1 : 1) : key === "title" ? 1 : -1 }))}>{label}{sort.key === key ? (sort.dir === 1 ? " ↑" : " ↓") : ""}</button></th>;
  return <div className="h-full overflow-auto"><table className="mizan-table text-xs [&_td]:py-1 [&_th]:py-1.5 [&_th]:sticky [&_th]:top-0 [&_th]:bg-white">
    <thead><tr><th>Type</th>{head("title", "Record")}{head("date", "Date")}<th>Price</th>{head("price_per_sqm", "Unit value")}<th>Area</th>{head("distance", "Distance")}<th>Location</th><th>Source</th><th>Status</th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id} onClick={() => onSelect(r)} aria-selected={selectedId === r.id} className={`cursor-pointer ${selectedId === r.id ? "bg-blue-50" : "hover:bg-slate-50"}`}>
      <td><span className="inline-block w-2 h-2 rounded-full mr-1" style={{ background: LAYER[r.kind].color }} />{LAYER[r.kind].short}</td>
      <td><button type="button" dir="auto" className="text-left hover:underline" onClick={e => { e.stopPropagation(); onSelect(r); }}>{r.title}</button></td>
      <td className="whitespace-nowrap">{r.date || "—"}</td><td className="whitespace-nowrap">{r.kind === "market" ? `${String(r.value)} ${r.unit || ""}` : money(r.price, r.currency)}</td>
      <td className="whitespace-nowrap">{r.price_per_sqm == null ? "—" : `${n0.format(r.price_per_sqm)} ${r.currency}/m²`}</td><td>{r.area_sqm == null ? "—" : `${n0.format(r.area_sqm)} m²`}</td>
      <td className="whitespace-nowrap">{subject && r.coordinates ? formatDistance(haversineMeters(subject, r.coordinates)) : "—"}</td>
      <td className="text-slate-500">{precisionLabel(r.location_precision)}</td><td className="text-slate-500 max-w-[160px] truncate">{sourceLabel(r.source)}</td><td>{r.status}</td></tr>)}</tbody></table>
    {records.length > 200 && <p className="text-[11px] text-slate-500 px-3 py-2">Showing 200 of {records.length} rows; narrow the area or filters.</p>}
    {!records.length && <p className="text-xs text-slate-500 px-3 py-4">No rows for the current scope.</p>}</div>;
}
