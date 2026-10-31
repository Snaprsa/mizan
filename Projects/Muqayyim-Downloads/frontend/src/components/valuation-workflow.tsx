"use client";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { PreparedAnalysis, ValuationMethod, AnalysisInput, AnalysisResult, prepareAnalysis, saveAnalysisInputs, calculateAnalysis, getAnalysisRuns } from "@/lib/api";

import SensitivityTable from "./sensitivity-table";
import AdjustmentGrid from "./adjustment-grid";
import { preparedSignature, savedRunMatchesPrepared, valuationSignature } from "@/lib/valuation-state";

type Draft = Record<string, { value: string; source: string; as_of: string }>;
export default function ValuationWorkflow({ propertyId, methods, onPrepared, onSelectEvidence, refreshKey = 0 }: {
  propertyId: string; methods: ValuationMethod[]; onPrepared: (p: PreparedAnalysis) => void; onSelectEvidence: (id: string) => void;
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
  const money = (n: number) => `SAR ${new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(n)}`;
  const range = result?.outputs.evidence?.indication as { low: number; high: number } | undefined;
  const grid = prepared.adjustment_analysis;
  const applied = grid ? grid.rows.reduce((n, r) => n + r.steps.length, 0) : 0;
  return <div className="space-y-3" aria-label="Valuation workspace">
    {/* The answer first. */}
    <section className="rounded-2xl bg-white p-4 ring-1 ring-black/[0.05]" aria-live="polite">
      {result ? <>
        <p className="text-[13px] text-black/50">{resultCurrent ? "Estimated value" : "Last saved value · inputs have changed since"}</p>
        <p className={`mt-0.5 text-[32px] font-semibold leading-tight tracking-tight ${resultCurrent ? "text-black/90" : "text-black/35"}`}>{money(result.outputs.value)}</p>
        {range && <p className="mt-1 text-[13px] text-black/55">Middle half of sales: {money(range.low)} – {money(range.high)}</p>}
        <p className="mt-1 text-[12px] text-black/40">{methods.find(m => m.key === result.method)?.label || result.method} · as of {result.data_date}</p>
      </> : <><p className="text-[15px] font-semibold text-black/85">{busy ? "Calculating…" : prepared.ready ? (automatic ? "Almost there" : "Ready to calculate") : "A few things are needed"}</p>
        <p className="mt-0.5 text-[13px] text-black/50">{prepared.ready ? "Your value will appear here." : "Complete the items below and your value will appear here."}</p></>}
    </section>
    {error && <div className="mizan-error" role="alert">{error}<button type="button" className="underline block mt-2" onClick={() => { setError(""); prepareAnalysis(propertyId, method).then(hydrate).catch(e => setError(e.message)); }}>Reload saved inputs</button></div>}
    {!!prepared.gaps.length && <section className="rounded-2xl bg-[#FF9F0A]/10 px-4 py-3 text-[13px] text-[#8a5300]"><h3 className="font-semibold">Still needed</h3><ul className="mt-1 list-disc space-y-0.5 pl-4">{prepared.gaps.map(g => <li key={g}>{g}</li>)}</ul></section>}

    {/* What this approach needs from you. */}
    {!!prepared.fields.length && <section className="space-y-3 rounded-2xl bg-white p-4 ring-1 ring-black/[0.05]" aria-label="Approach-specific required inputs">
      {prepared.fields.map(f => <div key={f.key} className="space-y-1.5"><label className="mizan-label">{f.label} ({f.unit === "sqm" ? "m²" : f.unit})<input aria-label={f.label} className="mizan-input" type="number" step={f.key === "holding_years" ? "1" : "any"} min={f.minimum} max={f.maximum ?? undefined} value={draft[f.key]?.value ?? ""} onChange={e => {
          const previous = draft[f.key] || { value: "", source: "", as_of: "" };
          const raw = e.target.value; const isOriginal = raw !== "" && f.value != null && Number(raw) === f.value;
          const changesSourcedValue = raw !== "" && f.value != null && !isOriginal && (previous.source === f.source || previous.source.startsWith("User override of:"));
          const source = isOriginal ? f.source || previous.source : changesSourcedValue ? `User override of: ${f.source || "saved value"}` : previous.source || "User input · valuation assumption";
          const date = isOriginal ? f.as_of || previous.as_of : changesSourcedValue ? asOf : previous.as_of || asOf;
          setDraft({ ...draft, [f.key]: { value: raw, source, as_of: date } }); setError("");
        }} /></label>
        {f.unit === "ratio" && <p className="text-[10px] text-slate-400">Use 0.08 for 8%. Enter 0 explicitly where applicable.</p>}
        {/* Provenance is always recorded; it opens by itself when something is missing. */}
        <details open={f.value != null && (!f.source || !f.as_of) ? true : undefined}>
          <summary className="mizan-summary cursor-pointer text-[12px] text-black/45">Source: <span className="text-black/65">{draft[f.key]?.source?.trim() || "added when you enter a value"}</span>{draft[f.key]?.as_of ? ` · ${draft[f.key].as_of}` : ""} <span className="text-[#007AFF]">Edit</span></summary>
          <div className="mt-2 space-y-2">
            <label className="mizan-label">Source for {f.label}<input className="mizan-input !text-xs" value={draft[f.key]?.source ?? ""} onChange={e => { setDraft({ ...draft, [f.key]: { ...draft[f.key], source: e.target.value } }); setError(""); }} placeholder="Source / user assumption" /></label>
            <label className="mizan-label">Source date for {f.label}<input className="mizan-input" type="date" value={draft[f.key]?.as_of ?? ""} onChange={e => { setDraft({ ...draft, [f.key]: { ...draft[f.key], as_of: e.target.value } }); setError(""); }} /></label>
            <p className="text-[10px] text-slate-500">{f.origin === "market_observation" ? "Filled from a matching source observation; source and date are recorded." : f.origin ? `Filled from ${f.origin.replaceAll("_", " ")}.` : "Missing from saved evidence. Supply a sourced value or explicit user assumption."}</p>
          </div>
        </details>
      </div>)}
      <p className="text-[11.5px] text-black/40">A value you type is recorded as your own assumption.</p>
    </section>}
    {!automatic && <button type="button" disabled={busy || !complete} className="w-full rounded-xl bg-[#007AFF] px-4 py-3 text-[16px] font-semibold text-white active:opacity-80 disabled:bg-black/10 disabled:text-black/35" onClick={() => perform(true)}>{busy ? "Calculating…" : "Calculate"}</button>}
    {notice && <p role="status" className="px-1 text-[12.5px] text-[#248a3d]">{notice}</p>}

    {/* Everything else is one tap away. */}
    <div className="divide-y divide-black/[0.06] overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.05]">
      {method === "sales_comparison" && grid && <Disclosure title="Adjust comparables" detail={applied ? `${applied} applied` : `${grid.rows.length} sales`}>
        <AdjustmentGrid propertyId={propertyId} prepared={prepared} disabled={busy} onSaved={adopt} onSelectEvidence={onSelectEvidence} /></Disclosure>}
      <Disclosure title="Evidence used" detail={method === "sales_comparison" ? `${prepared.eligible_comparables.length} of ${prepared.candidates.length} usable` : `${prepared.candidates.length} nearby`} defaultOpen={method === "sales_comparison" && !grid}>
        <p className="text-[12.5px] text-black/50">Within {prepared.radius_km} km. Listings and draft, undated or repeated records are not used as achieved sales.</p>
        <div className="mt-2 max-h-56 divide-y divide-black/[0.05] overflow-auto">{prepared.candidates.slice(0, 30).map(c => <button key={c.id} type="button" className="block w-full py-1.5 text-left" onClick={() => onSelectEvidence(c.id)}><span className="block truncate text-[14px] text-black/80" dir="auto">{c.title}</span><span className={`block text-[12px] ${c.eligible ? "text-[#248a3d]" : "text-black/45"}`}>{c.distance_km} km · {c.eligible ? "Used" : c.exclusion_reasons.join("; ")}</span></button>)}{!prepared.candidates.length && <p className="py-2 text-[13px] text-black/45">No located evidence within this radius.</p>}</div>
        <button type="button" className="mt-2 text-[13px] text-[#007AFF] disabled:opacity-40" disabled={busy} onClick={refresh}>Refresh evidence</button>
      </Disclosure>
      {result && <Disclosure title="How this was calculated">
        <ul className="list-disc space-y-1 pl-4 text-[12.5px] text-black/55">{result.outputs.limitations.map(l => <li key={l}>{l}</li>)}</ul>
        <SensitivityTable sensitivity={result.outputs.sensitivity} />
        <details className="mt-2"><summary className="cursor-pointer text-[12.5px] text-black/45">Technical details</summary><pre className="mt-1 max-h-52 overflow-auto rounded-lg bg-black/[0.03] p-2 text-[11px]">{JSON.stringify(result.outputs.evidence, null, 2)}</pre></details>
      </Disclosure>}
      {!!runs.length && <Disclosure title="Saved calculations" detail={String(runs.length)}>
        <ul className="divide-y divide-black/[0.05]">{runs.map(r => <li key={r.id}><button type="button" className="w-full py-1.5 text-left text-[13.5px] text-[#007AFF]" onClick={() => setResult({ ...r.data, id: r.id, created_at: r.created_at })}>{new Date(r.created_at).toLocaleString()}<span className="block text-[12px] text-black/45">{methods.find(m => m.key === r.data.method)?.label || r.data.method} · {money(r.data.outputs.value)} · revision {r.data.property_revision}</span></button></li>)}</ul>
      </Disclosure>}
      <Disclosure title="Settings" detail={`${asOf} · ${radius} km`}>
        <div className="space-y-2.5">
          <label className="mizan-label">Valuation approach<select aria-label="Valuation approach" className="mizan-input" value={method} disabled={busy} onChange={e => changeMethod(e.target.value)}>{methods.map(m => <option key={m.key} value={m.key} disabled={!m.implemented}>{m.label}{!m.implemented ? " · not available yet" : ""}</option>)}</select></label>
          <p className="text-[12px] text-black/45">{prepared.description}</p>
          <div className="grid grid-cols-2 gap-2"><label className="mizan-label">Valuation date<input className="mizan-input" type="date" value={asOf} onChange={e => { setAsOf(e.target.value); setError(""); }} /></label><label className="mizan-label">Evidence radius (km)<input className="mizan-input" type="number" min="0.1" max="50" step="0.1" value={radius} onChange={e => { setRadius(e.target.value); setError(""); }} /></label><label className="mizan-label col-span-2">Look back (days)<input className="mizan-input" type="number" min="1" max="3650" value={lookback} onChange={e => { setLookback(e.target.value); setError(""); }} /></label></div>
          <label className="flex items-center gap-2 text-[13.5px] text-black/70"><input type="checkbox" checked={automatic} onChange={e => setAutomatic(e.target.checked)} />Calculate automatically</label>
          <button type="button" disabled={busy} className="block text-[13.5px] text-[#007AFF] disabled:opacity-40" onClick={() => perform(false)}>Save without calculating</button>
          <p className="text-[11.5px] text-black/40">Revision {prepared.revision}</p>
          <Link href={`/properties/${propertyId}`} className="block text-[13.5px] text-[#007AFF]">Open full property details</Link>
        </div>
      </Disclosure>
    </div>
  </div>;
}

function Disclosure({ title, detail, defaultOpen, children }: { title: string; detail?: string; defaultOpen?: boolean; children: ReactNode }) {
  return <details open={defaultOpen ? true : undefined}>
    <summary className="mizan-summary flex min-h-[44px] cursor-pointer items-center gap-2 px-4 py-2 text-[15px] text-black/85 hover:bg-black/[0.02]"><span className="flex-1">{title}</span>
      {detail && <span className="text-[14px] text-black/40">{detail}</span>}<ChevronRight size={15} className="mizan-chevron shrink-0 text-black/25 transition-transform" /></summary>
    <div className="px-4 pb-3 pt-1">{children}</div>
  </details>;
}
