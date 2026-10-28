"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { getProperty, saveProperty, saveAssumption, listRevisions, getRevision, listCases, listObservations,
  PropertyWorkspace, PropertyInput, Assumption, Revision, Observation } from "@/lib/api";
import { Case } from "@/lib/types";
import { PropertyEditor } from "@/components/property-editor";

export default function PropertyPage({ params }: { params: { id: string } }) {
  const [workspace, setWorkspace] = useState<PropertyWorkspace | null>(null);
  const [draft, setDraft] = useState<PropertyInput | null>(null);
  const [tab, setTab] = useState("Overview"); const [error, setError] = useState("");
  const [notice, setNotice] = useState(""); const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<Revision[]>([]); const [cases, setCases] = useState<Case[]>([]);
  const [historical, setHistorical] = useState<{ property: PropertyInput; assumptions: Record<string, Assumption> } | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [assumptionEdit, setAssumptionEdit] = useState<{ key: string; data: Assumption } | null>(null);
  function loaded(p: PropertyWorkspace) { setWorkspace(p); setDraft(p.property); }
  useEffect(() => { getProperty(params.id).then(loaded).catch(e => setError(e.message));
    listCases().then(r => setCases(r.data)).catch(e => setError(e.message));
  }, [params.id]);
  useEffect(() => {
    if (tab === "History") listRevisions(params.id).then(setHistory).catch(e => setError(e.message));
    if (tab === "Market" && workspace) {
      const city = workspace.property.location.city;
      if (city) listObservations(String(city)).then(r => setObservations(r.data)).catch(e => setError(e.message));
      else setObservations([]);
    }
  }, [tab, params.id, workspace]);
  async function update(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); if (!workspace || !draft) return;
    const reason = String(new FormData(e.currentTarget).get("reason"));
    setBusy(true); setError(""); setNotice("");
    try { loaded(await saveProperty(params.id, draft, workspace.revision, reason)); setNotice("Saved as a new revision."); }
    catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  async function assumption(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); if (!workspace) return;
    const form = e.currentTarget; const f = new FormData(form); const key = String(f.get("key"));
    if (f.get("value_type") === "boolean" && ![String(f.get("value")), ...(f.get("override") ? [String(f.get("override"))] : [])].every(v => ["true", "false"].includes(v))) {
      setError("Boolean values must be true or false."); return;
    }
    const parseValue = (raw: string) => f.get("value_type") === "number" ? Number(raw) : f.get("value_type") === "boolean" ? raw === "true" : raw;
    const data: Assumption = { name: String(f.get("name")), value: parseValue(String(f.get("value"))), unit: String(f.get("unit")), category: String(f.get("category")), source: String(f.get("source")), as_of: String(f.get("as_of")), status: String(f.get("status")), user_override: f.get("override") === "" ? null : parseValue(String(f.get("override"))), notes: String(f.get("notes")) || null };
    setBusy(true); setError(""); setNotice("");
    try { loaded(await saveAssumption(params.id, key, data, workspace.revision, String(f.get("reason")))); setAssumptionEdit(null); form.reset(); setNotice("Assumption saved. Previous values remain in History. Valuation recalculation is not yet implemented."); }
    catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }
  if (!workspace || !draft) return <div>{error ? <p role="alert" className="mizan-error">{error}</p> : <p role="status">Loading property…</p>}</div>;
  const inputClass = "mizan-input";
  return <div className="space-y-5">
    <Link href="/properties" className="text-sm text-blue-700">← Properties</Link>
    <header><h1 className="text-2xl font-semibold">{workspace.property.name}</h1><p className="text-xs text-slate-500 mt-1">{workspace.id} · Revision {workspace.revision} · {workspace.property.currency} · Updated {new Date(workspace.updated_at).toLocaleString()}</p></header>
    {error && <div role="alert" className="mizan-error">{error}<button type="button" className="block underline mt-2" onClick={() => { getProperty(params.id).then(p => { loaded(p); setError(""); }).catch(e => setError(e.message)); }}>Reload saved inputs (discard unsaved edits)</button></div>}
    {notice && <p role="status" className="text-sm text-green-800">{notice}</p>}
    <Link className="inline-block text-sm text-blue-700" href={workspace.property.case_id ? `/map?case_id=${workspace.property.case_id}` : "/map"}>View map & comparable evidence →</Link>
    <nav aria-label="Property workspace" className="flex border-b border-slate-200 gap-5">{["Overview", "Assumptions", "Comparables", "Market", "History"].map(t => <button key={t} onClick={() => setTab(t)} aria-current={tab === t ? "page" : undefined} className={`py-2 text-sm ${tab === t ? "text-blue-700 border-b-2 border-blue-600" : "text-slate-500"}`}>{t}</button>)}</nav>
    {tab === "Overview" && <form onSubmit={update} className="mizan-panel space-y-5">
      <p className="text-xs text-slate-500">Blank fields mean unknown. Rates use ratios from 0 to 1. No valuation is calculated in this foundation release.</p>
      <PropertyEditor value={draft} onChange={setDraft} />
      <label className="mizan-label">Comparable evidence case<select aria-label="Comparable evidence case" className={inputClass} value={draft.case_id || ""} onChange={e => setDraft({ ...draft, case_id: e.target.value || null })}><option value="">Not linked</option>{cases.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
      <label className="mizan-label">Reason for change<input className={inputClass} name="reason" required /></label><button className="mizan-button" disabled={busy}>{busy ? "Saving…" : "Save revision"}</button>
    </form>}
    {tab === "Assumptions" && <div className="space-y-4">
      <div className="mizan-panel overflow-auto"><table className="mizan-table"><thead><tr>{["Assumption", "Effective value", "Unit / category", "Source", "As of", "Status", ""].map((h, i) => <th key={i}>{h}</th>)}</tr></thead><tbody>{Object.entries(workspace.assumptions).map(([key, a]) => <tr key={key}><td>{a.name}<div className="text-xs text-slate-400">{key}</div></td><td>{String(a.effective_value)}{a.user_override != null && <div className="text-xs text-amber-700">Override · original {String(a.value)}</div>}</td><td>{a.unit} / {a.category}</td><td>{a.source}<div className="text-xs text-slate-400">{a.notes}</div></td><td>{a.as_of}</td><td>{a.status.replaceAll("_", " ")}</td><td><button type="button" className="text-blue-700" onClick={() => setAssumptionEdit({ key, data: a })}>Edit</button></td></tr>)}</tbody></table>{!Object.keys(workspace.assumptions).length && <p className="text-sm py-3 text-slate-500">No assumptions recorded.</p>}</div>
      <form key={assumptionEdit?.key || "new"} onSubmit={assumption} className="mizan-panel space-y-4"><h2 className="font-medium text-sm">{assumptionEdit ? "Update assumption" : "Add assumption"}</h2>
        <div className="grid md:grid-cols-3 gap-3">
          <label className="mizan-label">Key (snake_case)<input className={inputClass} name="key" pattern="[a-z][a-z0-9_]{0,99}" defaultValue={assumptionEdit?.key || ""} readOnly={!!assumptionEdit} required /></label>
          {([ ["name", "Name"], ["value", "Original value"], ["unit", "Unit"], ["category", "Category"], ["source", "Source"], ["as_of", "As-of date"] ] as const).map(([key, label]) => <label className="mizan-label" key={key}>{label}<input className={inputClass} type={key === "as_of" ? "date" : "text"} name={key} defaultValue={String(assumptionEdit?.data[key] ?? "")} required /></label>)}
          <label className="mizan-label">Value type<select aria-label="Value type" className={inputClass} name="value_type" defaultValue={typeof assumptionEdit?.data.value === "number" ? "number" : typeof assumptionEdit?.data.value === "boolean" ? "boolean" : "text"}><option value="text">Text</option><option value="number">Number</option><option value="boolean">Boolean (true / false)</option></select></label>
          <label className="mizan-label">Status<select aria-label="Status" className={inputClass} name="status" defaultValue={assumptionEdit?.data.status || "user_input"}>{["observed", "market_derived", "system_estimate", "user_input", "model_derived"].map(s => <option key={s}>{s}</option>)}</select></label>
          <label className="mizan-label">User override (optional)<input className={inputClass} name="override" defaultValue={String(assumptionEdit?.data.user_override ?? "")} /></label>
          <label className="mizan-label">Notes (required for override)<input className={inputClass} name="notes" defaultValue={assumptionEdit?.data.notes || ""} /></label>
          <label className="mizan-label">Reason for change<input className={inputClass} name="reason" required /></label>
        </div><button className="mizan-button" disabled={busy}>Save assumption</button>{assumptionEdit && <button type="button" className="ml-4 text-sm" onClick={() => setAssumptionEdit(null)}>Cancel edit</button>}
      </form>
    </div>}
    {tab === "Comparables" && <div className="mizan-panel text-sm">{workspace.property.case_id ? <><p className="mb-3">Review existing comparable evidence, citations, overrides and exports in the linked case.</p><Link className="text-blue-700 underline" href={`/cases/${workspace.property.case_id}`}>Open comparable evidence case →</Link></> : <p>Link a case from Overview, or <Link className="text-blue-700 underline" href="/cases/new">create a case</Link> to ingest comparable URLs/PDFs.</p>}</div>}
    {tab === "Market" && <div className="mizan-panel overflow-auto"><p className="text-xs text-slate-500 mb-3">Recorded observations for this property&apos;s city (up to 100). These are source records, not valuation conclusions. No live market feed is connected.</p><table className="mizan-table"><thead><tr>{["Date", "Metric", "Value", "Unit", "Source", "Reliability"].map(h => <th key={h}>{h}</th>)}</tr></thead><tbody>{observations.map(o => <tr key={o.id}><td>{o.observed_on}</td><td>{o.metric}</td><td>{String(o.normalized_value)}</td><td>{o.unit}</td><td>{o.source}</td><td>{o.reliability}/100</td></tr>)}</tbody></table>{!observations.length && <p className="text-sm mt-3 text-slate-500">No observations found. <Link className="text-blue-700" href="/data">Register a source and import evidence.</Link></p>}</div>}
    {tab === "History" && <div className="mizan-panel"><h2 className="font-medium mb-3">Input and assumption history</h2><ul className="space-y-2 text-sm">{history.map(r => <li key={r.revision}><button className="text-blue-700" onClick={() => getRevision(params.id, r.revision).then(r => setHistorical(r.snapshot)).catch(e => setError(e.message))}>Revision {r.revision}</button> · {r.reason} · {new Date(r.created_at).toLocaleString()}</li>)}</ul>{historical && <details open className="mt-5"><summary className="text-sm font-medium">Saved input snapshot</summary><pre className="text-xs bg-slate-50 p-3 overflow-auto max-h-96 mt-2">{JSON.stringify(historical, null, 2)}</pre></details>}</div>}
    <p className="text-xs text-slate-400">Valuation, HBU, development, financing, returns, scenarios, risk and integrated reports are not yet implemented in this workspace. Existing legacy valuation tools are preserved separately.</p>
  </div>;
}
