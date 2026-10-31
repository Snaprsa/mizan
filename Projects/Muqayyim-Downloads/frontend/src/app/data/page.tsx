"use client";
import { FormEvent, useEffect, useState } from "react";
import { listMarketSources, createMarketSource, listObservations, importMarketCsv, MarketSource, Observation, listLocalDatasets, LocalDataset } from "@/lib/api";

export default function DataPage() {
  const [datasets, setDatasets] = useState<LocalDataset[]>([]);
  const [sources, setSources] = useState<MarketSource[]>([]); const [rows, setRows] = useState<Observation[]>([]);
  const [total, setTotal] = useState(0); const [offset, setOffset] = useState(0); const [city, setCity] = useState("");
  const [sourceId, setSourceId] = useState(""); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false); const [loading, setLoading] = useState(true);
  useEffect(() => { listLocalDatasets().then(setDatasets).catch(e => setError(e.message)); listMarketSources().then(setSources).catch(e => setError(e.message)); }, []);
  useEffect(() => { let active = true; setLoading(true); listObservations(city, offset).then(r => { if (active) { setRows(r.data); setTotal(r.total); } }).catch(e => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); }); return () => { active = false; }; }, [city, offset]);
  async function register(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const form = e.currentTarget; const f = new FormData(form); setBusy(true); setError(""); setNotice("");
    try { const s = await createMarketSource({ name: String(f.get("name")), provider: String(f.get("provider")), source_type: String(f.get("type")), uri: String(f.get("uri")) || null, notes: String(f.get("notes")) || null }); setSources(prev => [s, ...prev]); setSourceId(s.id); form.reset(); setNotice("Source registered. Import observations below."); }
    catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  async function upload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const form = e.currentTarget; const f = new FormData(form); const file = f.get("file") as File;
    setBusy(true); setError(""); setNotice("");
    try { const r = await importMarketCsv(sourceId, file); setNotice(`${r.inserted} observations imported; ${r.duplicates} unchanged duplicates skipped.`); const result = await listObservations(city); setRows(result.data); setTotal(result.total); setOffset(0); form.reset(); }
    catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  function template() {
    const blob = new Blob(["external_id,observed_on,city,property_type,metric,unit,raw_value,normalized_value,reliability\n"], { type: "text/csv" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = "mizan-observations-template.csv"; a.click(); URL.revokeObjectURL(url);
  }
  return <div className="space-y-5"><header><h1 className="text-[28px] font-semibold tracking-tight">Market data</h1><p className="text-sm text-slate-500 mt-1">Source registry and evidence imports · No live feeds connected</p></header>
    {error && <p className="mizan-error" role="alert">{error}</p>}{notice && <p className="text-sm text-green-800" role="status">{notice}</p>}
    <div className="mizan-panel overflow-auto"><label className="mizan-label max-w-sm mb-4">Filter observations by city<input className="mizan-input" value={city} onChange={e => { setCity(e.target.value); setOffset(0); }} /></label><p className="text-xs text-slate-500 mb-3">{total} observations. Reliability is supplied by the evidence owner, not a calibrated valuation confidence.</p>
      <table className="mizan-table"><thead><tr>{["Date / city", "Property type", "Metric", "Raw", "Normalized", "Unit", "Source", "Reliability"].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map(r => <tr key={r.id}><td>{r.observed_on}<div>{r.city}{r.district ? ` / ${r.district}` : ""}</div></td><td>{r.property_type}</td><td>{r.metric}</td><td>{String(r.raw_value)}</td><td>{String(r.normalized_value)}</td><td>{r.unit}</td><td>{r.source}</td><td>{r.reliability}/100</td></tr>)}</tbody></table>
      {loading && <p role="status" className="text-sm mt-3">Loading observations…</p>}{!loading && !rows.length && <p className="text-sm text-slate-500 mt-3">No observations found. Nothing is pre-populated as market evidence.</p>}
      <div className="flex gap-3 mt-3 text-sm"><button disabled={!offset} onClick={() => setOffset(offset - 100)}>Previous</button><span>{total ? offset + 1 : 0}–{offset + rows.length} of {total}</span><button disabled={offset + 100 >= total} onClick={() => setOffset(offset + 100)}>Next</button></div>
    </div>
    <details className="mizan-panel"><summary className="cursor-pointer text-[15px] font-medium">Import observations</summary><div className="mt-3">
    <form onSubmit={upload} className="space-y-3"><p className="text-xs text-slate-500">Use UTF-8 CSV, ISO dates (YYYY-MM-DD), explicit units and reliability from 0–100. Preserve the original value and provide the normalized value yourself. Imports are append-only; changed evidence requires a new external ID. Max 1,000 rows / 2 MB.</p>
      <button type="button" className="text-sm text-[#007AFF] underline" onClick={template}>Download empty CSV template</button>
      <label className="mizan-label">Source<select aria-label="Source" className="mizan-input" required value={sourceId} onChange={e => setSourceId(e.target.value)}><option value="">Select source</option>{sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
      <label className="mizan-label">CSV file<input className="mizan-input" name="file" type="file" accept=".csv,text/csv" required /></label><button className="mizan-button" disabled={busy || !sourceId}>{busy ? "Working…" : "Import CSV"}</button>
    </form>
    </div></details>
    <details className="mizan-panel"><summary className="cursor-pointer text-[15px] font-medium">Sources</summary><div className="mt-3">
    <div className="overflow-auto"><table className="mizan-table"><thead><tr>{["Source", "Provider", "Type", "Reference / notes"].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{sources.map(s => <tr key={s.id}><td>{s.name}</td><td>{s.provider}</td><td>{s.source_type}</td><td className="break-all">{s.uri}<div className="text-xs text-slate-500">{s.notes}</div></td></tr>)}</tbody></table>{!sources.length && <p className="text-sm text-slate-500 mt-3">No sources registered.</p>}</div>
    <form onSubmit={register} className="space-y-3"><div className="grid md:grid-cols-3 gap-3">
      <label className="mizan-label">Source name<input className="mizan-input" name="name" required /></label><label className="mizan-label">Provider / organization<input className="mizan-input" name="provider" required /></label>
      <label className="mizan-label">Source type<select aria-label="Source type" className="mizan-input" name="type">{["user_upload", "official_dataset", "broker", "listing_portal", "internal", "economic", "construction", "rental"].map(t => <option key={t}>{t}</option>)}</select></label>
      <label className="mizan-label">Source URL or reference<input className="mizan-input" name="uri" /></label><label className="mizan-label">Notes / evidence limitations<input className="mizan-input" name="notes" /></label>
    </div><button className="mizan-button" disabled={busy}>Register source</button></form>
    </div></details>
    <details className="mizan-panel"><summary className="text-sm font-semibold cursor-pointer">Existing local datasets ({datasets.length})</summary><p className="text-xs text-slate-500 my-3">Preserved files for provenance and quality review. None are automatically promoted to market evidence. Some may contain sample or aggregate data.</p><table className="mizan-table"><thead><tr><th>File</th><th>Location</th><th>Review status</th></tr></thead><tbody>{datasets.map(d => <tr key={d.path}><td>{d.name}</td><td className="break-all text-xs">{d.path}</td><td>Unverified · not imported</td></tr>)}</tbody></table></details>
  </div>;
}
