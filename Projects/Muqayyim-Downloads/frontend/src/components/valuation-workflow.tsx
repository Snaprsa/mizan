"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { PreparedAnalysis, ValuationMethod, AnalysisInput, AnalysisResult, prepareAnalysis, saveAnalysisInputs, calculateAnalysis, getAnalysisRuns } from "@/lib/api";

import SensitivityTable from "./sensitivity-table";
import AdjustmentGrid from "./adjustment-grid";
import { preparedSignature, savedRunMatchesPrepared, valuationSignature } from "@/lib/valuation-state";

type Draft = Record<string, { value: string; source: string; as_of: string }>;
export default function ValuationWorkflow({ propertyId, methods, onPrepared, onSelectEvidence, refreshKey = 0, embedded = false }: {
  propertyId: string; methods: ValuationMethod[]; onPrepared: (p: PreparedAnalysis) => void; onSelectEvidence: (id: string) => void;
  /** Rendered inside the map card: no outer panel chrome or duplicate title. */
  embedded?: boolean;
  /** Increment after another screen changes the property (e.g. map geometry) to adopt its new revision. */
  refreshKey?: number;
}) {
  const [prepared, setPrepared] = useState<PreparedAnalysis | null>(null); const [method, setMethod] = useState("");
  const [draft, setDraft] = useState<Draft>({}); const [radius, setRadius] = useState("3"); const [lookback, setLookback] = useState("365"); const [asOf, setAsOf] = useState("");
  const [automatic, setAutomatic] = useState(true); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const [notice, setNotice] = useState(""); const [result, setResult] = useState<AnalysisResult | null>(null);
  const [runs, setRuns] = useState<{ id: string; created_at: string; data: AnalysisResult }[]>([]);
  const processed = useRef(""); const alive = useRef(true);
  const hydrate = useCallback((p: PreparedAnalysis) => {
    setPrepared(p); setMethod(p.method); setRadius(String(p.radius_km)); setLookback(String(p.lookback_days)); setAsOf(p.as_of);
    setDraft(Object.fromEntries(p.fields.map(f => [f.key, { value: f.value == null ? "" : String(f.value), source: f.source || "", as_of: f.as_of || "" }])));
    onPrepared(p);
  }, [onPrepared]);
  useEffect(() => { alive.current = true; let current = true; setPrepared(null); setResult(null); processed.current = "";
    Promise.all([prepareAnalysis(propertyId), getAnalysisRuns(propertyId)]).then(([p, history]) => {
      if (!current) return; setRuns(history); const latest = history.find(r => r.data.property_revision === p.revision && r.data.method === p.method);
      if (latest) setResult({ ...latest.data, id: latest.id, created_at: latest.created_at });
      // Existing saved calculations must not be recreated merely by reopening the map.
      if (latest && savedRunMatchesPrepared(p, latest.data)) processed.current = preparedSignature(p);
      hydrate(p);
    }).catch(e => { if (current) setError(e.message); });
    return () => { current = false; alive.current = false; };
  }, [propertyId, hydrate]);
  const values = useMemo(() => Object.fromEntries(Object.entries(draft).filter(([, d]) => d.value !== "").map(([key, d]) => [key, { value: Number(d.value), source: d.source, as_of: d.as_of,
      status: prepared?.fields.find(f => f.key === key && f.value === Number(d.value) && f.source === d.source && f.as_of === d.as_of)?.assumption_status || "user_input" }])) as Record<string, AnalysisInput>, [draft, prepared]);
  const signature = useMemo(() => valuationSignature({ method, asOf, radius: Number(radius),
    lookback: Number(lookback), inputs: values, evidence: prepared?.eligible_comparables || [], adjustments: prepared?.adjustment_setup }),
    [method, asOf, radius, lookback, values, prepared]);
  const complete = !!prepared && prepared.fields.every(f => {
    const d = draft[f.key]; const value = Number(d?.value);
    return d?.value !== "" && !!d?.source.trim() && !!d?.as_of && Number.isFinite(value) && value >= f.minimum &&
      (!f.positive || value > 0) && (f.maximum == null || value <= f.maximum) && (f.key !== "holding_years" || Number.isInteger(value));
  }) && !!asOf && Number(radius) >= 0.1 && Number(radius) <= 50 && Number(lookback) >= 1 && Number(lookback) <= 3650;
  // Re-prepare from the server; fills untouched blanks and keeps the user's unsaved edits.
  const adopt = useCallback((p: PreparedAnalysis) => {
    setPrepared(p); setDraft(previous => Object.fromEntries(p.fields.map(f => {
      const existing = previous[f.key];
      return [f.key, !existing || (existing.value === "" && existing.source === "" && existing.as_of === "")
        ? { value: f.value == null ? "" : String(f.value), source: f.source || "", as_of: f.as_of || "" }
        : existing];
    }))); onPrepared(p); setError("");
  }, [onPrepared]);
  const refresh = useCallback(() => prepareAnalysis(propertyId, method || undefined).then(adopt).catch(e => setError(e.message)), [propertyId, method, adopt]);
  const lastRefreshKey = useRef(refreshKey);
  useEffect(() => { if (refreshKey !== lastRefreshKey.current) { lastRefreshKey.current = refreshKey; refresh(); } }, [refreshKey, refresh]);
  const perform = useCallback(async (shouldCalculate: boolean) => {
    if (!prepared || busy) return;
    processed.current = signature; setBusy(true); setError(""); setNotice("");
    try {
      const saved = await saveAnalysisInputs(propertyId, { method, expected_revision: prepared.revision, inputs: values,
        as_of: asOf, radius_km: Number(radius), lookback_days: Number(lookback) });
      if (!alive.current) return;
      setPrepared(saved); onPrepared(saved);
      if (shouldCalculate && saved.ready) {
        const run = await calculateAnalysis(propertyId, saved.revision);
        if (!alive.current) return;
        setResult(run); setRuns(await getAnalysisRuns(propertyId)); setNotice("Calculated and saved with its inputs and evidence.");
      } else setNotice(shouldCalculate ? "Inputs saved. Waiting for the missing evidence shown below." : "Inputs saved as a new revision.");
    } catch (err) { if (alive.current) setError((err as Error).message); }
    finally { if (alive.current) setBusy(false); }
  }, [prepared, busy, signature, propertyId, method, values, asOf, radius, lookback, onPrepared]);
  useEffect(() => {
    if (!automatic || !complete || busy || processed.current === signature || error) return;
    const timer = setTimeout(() => { void perform(true); }, 1000);
    return () => clearTimeout(timer);
  }, [automatic, complete, busy, signature, error, perform]);
  async function changeMethod(key: string) {
    setBusy(true); setError(""); setResult(null); processed.current = "";
    try {
      const p = await prepareAnalysis(propertyId, key);
      const latest = runs.find(r => r.data.property_revision === p.revision && r.data.method === p.method);
      if (latest) { setResult({ ...latest.data, id: latest.id, created_at: latest.created_at }); if (savedRunMatchesPrepared(p, latest.data)) processed.current = preparedSignature(p); }
      hydrate(p);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  if (!prepared) return <section className="mizan-panel !p-4">{error ? <p role="alert" className="mizan-error">{error}</p> : <p role="status" className="text-sm">Gathering evidence and required inputs…</p>}</section>;
  const resultCurrent = result && savedRunMatchesPrepared(prepared, result) && preparedSignature(prepared) === signature;
  return <section className={embedded ? "mizan-embedded space-y-3 rounded-2xl bg-white p-4 ring-1 ring-black/[0.05]" : "mizan-panel !p-4 space-y-3 border-blue-300"} aria-label="Valuation workspace">
    {embedded && result && <div className="rounded-xl bg-black/[0.03] px-3 py-3">
      <p className="text-[12px] text-black/50">{resultCurrent ? "Estimated value" : "Last saved value · inputs have changed since"}</p>
      <p className={`text-[30px] font-semibold tracking-tight leading-tight ${resultCurrent ? "text-black/90" : "text-black/40"}`}>SAR {new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(result.outputs.value)}</p>
      <p className="text-[12px] text-black/45">{methods.find(m => m.key === result.method)?.label || result.method} · as of {result.data_date}</p></div>}
    {embedded && !result && <p className="rounded-xl bg-black/[0.03] px-3 py-3 text-[13px] text-black/55">{prepared.ready ? "Ready — calculating…" : `Still needed: ${prepared.gaps.length} item${prepared.gaps.length === 1 ? "" : "s"} (listed below).`}</p>}
    {embedded ? <p className="text-[12px] text-black/40">Revision {prepared.revision}</p> : <div><h2 className="font-semibold text-sm">Valuation workspace</h2><p className="text-xs text-slate-500 mt-1">{prepared.property_name} · Revision {prepared.revision}</p></div>}
    {error && <div className="mizan-error" role="alert">{error}<button type="button" className="underline block mt-2" onClick={() => { setError(""); prepareAnalysis(propertyId, method).then(hydrate).catch(e => setError(e.message)); }}>Reload saved inputs</button></div>}
    {/* Settings stay one tap away; the summary line shows their current values. */}
    <details className="group rounded-xl bg-black/[0.03] px-3 py-2">
      <summary className="cursor-pointer list-none text-[13px] text-black/60"><span className="font-medium text-black/80">Settings</span> · {methods.find(m => m.key === method)?.label} · {asOf} · {radius} km · {lookback} days{automatic ? " · auto" : ""}</summary>
      <div className="mt-2 space-y-2">
      <label className="mizan-label">Valuation approach<select aria-label="Valuation approach" className="mizan-input" value={method} disabled={busy} onChange={e => changeMethod(e.target.value)}>{methods.map(m => <option key={m.key} value={m.key} disabled={!m.implemented}>{m.label}{!m.implemented ? " · not yet implemented" : ""}</option>)}</select></label>
      <p className="text-xs text-slate-500">{prepared.description}</p>
      <label className="text-xs flex gap-2 items-center"><input type="checkbox" checked={automatic} onChange={e => setAutomatic(e.target.checked)} />Calculate automatically when required inputs are complete</label>
      <div className="grid grid-cols-2 gap-2"><label className="mizan-label">Valuation date<input className="mizan-input" type="date" value={asOf} onChange={e => { setAsOf(e.target.value); setError(""); }} /></label><label className="mizan-label">Evidence radius (km)<input className="mizan-input" type="number" min="0.1" max="50" step="0.1" value={radius} onChange={e => { setRadius(e.target.value); setError(""); }} /></label><label className="mizan-label">Evidence lookback (days)<input className="mizan-input" type="number" min="1" max="3650" value={lookback} onChange={e => { setLookback(e.target.value); setError(""); }} /></label></div>
      <p className="text-[10px] text-slate-500">Typing a missing value marks it as a user assumption at the selected valuation date. Source and date remain editable.</p>
      </div>
    </details>
    <div className="max-h-[480px] overflow-y-auto space-y-3 pr-1" aria-label="Approach-specific required inputs">
      {prepared.fields.map(f => <div key={f.key} className="border-t border-slate-100 pt-3 space-y-2"><label className="mizan-label">{f.label} ({f.unit})<input aria-label={f.label} className="mizan-input" type="number" step={f.key === "holding_years" ? "1" : "any"} min={f.minimum} max={f.maximum ?? undefined} value={draft[f.key]?.value ?? ""} onChange={e => {
          const previous = draft[f.key] || { value: "", source: "", as_of: "" };
          const raw = e.target.value; const isOriginal = raw !== "" && f.value != null && Number(raw) === f.value;
          const changesSourcedValue = raw !== "" && f.value != null && !isOriginal && (previous.source === f.source || previous.source.startsWith("User override of:"));
          const source = isOriginal ? f.source || previous.source : changesSourcedValue ? `User override of: ${f.source || "saved value"}` : previous.source || "User input · valuation assumption";
          const date = isOriginal ? f.as_of || previous.as_of : changesSourcedValue ? asOf : previous.as_of || asOf;
          setDraft({ ...draft, [f.key]: { value: raw, source, as_of: date } }); setError("");
        }} /></label>
        {f.unit === "ratio" && <p className="text-[10px] text-slate-400">Use 0.08 for 8%. Enter 0 explicitly where applicable.</p>}
        {/* Provenance is always recorded; it opens by itself when something is missing. */}
        <details open={!f.source || !f.as_of ? true : undefined}>
          <summary className="cursor-pointer list-none text-[12px] text-black/45">Source: <span className="text-black/65">{draft[f.key]?.source?.trim() || "not set"}</span>{draft[f.key]?.as_of ? ` · ${draft[f.key].as_of}` : ""} <span className="text-[#007AFF]">Edit</span></summary>
          <div className="mt-2 space-y-2">
            <label className="mizan-label">Source for {f.label}<input className="mizan-input !text-xs" value={draft[f.key]?.source ?? ""} onChange={e => { setDraft({ ...draft, [f.key]: { ...draft[f.key], source: e.target.value } }); setError(""); }} placeholder="Source / user assumption" /></label>
            <label className="mizan-label">Source date for {f.label}<input className="mizan-input" type="date" value={draft[f.key]?.as_of ?? ""} onChange={e => { setDraft({ ...draft, [f.key]: { ...draft[f.key], as_of: e.target.value } }); setError(""); }} /></label>
            <p className="text-[10px] text-slate-500">{f.origin === "market_observation" ? "Filled from a matching source observation; source and date are recorded." : f.origin ? `Filled from ${f.origin.replaceAll("_", " ")}.` : "Missing from saved evidence. Supply a sourced value or explicit user assumption."}</p>
          </div>
        </details>
      </div>)}
    </div>
    <div className="flex flex-wrap gap-2"><button type="button" disabled={busy} className="text-xs px-3 py-2 border rounded disabled:opacity-50" onClick={() => perform(false)}>Save inputs</button><button type="button" disabled={busy || !complete} className="mizan-button !text-xs" onClick={() => perform(true)}>{busy ? "Processing…" : "Calculate now"}</button><button type="button" className="text-xs text-blue-700" disabled={busy} onClick={refresh}>Refresh evidence</button></div>
    {notice && <p role="status" className="text-xs text-green-800">{notice}</p>}
    {!!prepared.gaps.length && <details open className="bg-amber-50 p-3 rounded text-xs text-amber-900"><summary className="font-medium cursor-pointer">Still required / last saved readiness</summary><ul className="list-disc pl-4 mt-2 space-y-1">{prepared.gaps.map(g => <li key={g}>{g}</li>)}</ul></details>}
    {method === "sales_comparison" && prepared.adjustment_analysis && <AdjustmentGrid propertyId={propertyId} prepared={prepared} disabled={busy} onSaved={adopt} onSelectEvidence={onSelectEvidence} />}
    <details className="text-xs" open={method === "sales_comparison" && !prepared.adjustment_analysis}><summary className="font-medium cursor-pointer">Nearby evidence: {prepared.candidates.length} records · {prepared.eligible_comparables.length} eligible achieved sales</summary><p className="text-slate-500 mt-2">Within {prepared.radius_km} km. Listings and draft / undated / repeated evidence are not used as achieved sales.</p><div className="max-h-48 overflow-auto mt-2 space-y-2">{prepared.candidates.slice(0, 30).map(c => <button key={c.id} type="button" className="block text-left border rounded p-2 w-full" onClick={() => onSelectEvidence(c.id)}><span className="font-medium">{c.title}</span><span className="block text-slate-500">{c.distance_km} km · {c.eligible ? "Eligible achieved sale" : c.exclusion_reasons.join("; ")}</span></button>)}{!prepared.candidates.length && <p className="text-slate-500">No located comparable evidence in this radius.</p>}</div></details>
    {result && <div className="border-t border-slate-200 pt-3"><p className="text-xs text-slate-500">{resultCurrent ? "Current saved indication" : "Previous saved result · inputs may have changed"}</p><p className="text-xl font-semibold mt-1">SAR {new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(result.outputs.value)}</p><p className="text-[10px] text-slate-500">{result.method} · property revision {result.property_revision} · {result.data_date}</p>{result.outputs.limitations.map(l => <p key={l} className="text-[11px] text-slate-500 mt-1">{l}</p>)}<SensitivityTable sensitivity={result.outputs.sensitivity} /><details className="mt-2 text-xs"><summary>Calculation details</summary><pre className="overflow-auto max-h-52 bg-slate-50 p-2 mt-2">{JSON.stringify(result.outputs.evidence, null, 2)}</pre></details></div>}
    {!!runs.length && <details className="text-xs"><summary className="cursor-pointer">Saved calculations ({runs.length})</summary><ul className="space-y-2 mt-2">{runs.map(r => <li key={r.id}><button className="text-blue-700" onClick={() => setResult({ ...r.data, id: r.id, created_at: r.created_at })}>{r.data.method} · revision {r.data.property_revision} · {new Date(r.created_at).toLocaleString()}</button></li>)}</ul></details>}
    <div className="flex gap-3 text-xs"><Link href={`/properties/${propertyId}`} className="text-blue-700 underline">Full property workspace</Link></div>
  </section>;
}
