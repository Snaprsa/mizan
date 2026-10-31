"use client";
// Reviewer adjustment grid for sales comparison. All arithmetic is done by the API
// (api/app/services/comparable_adjustments.py); this component edits and displays the reviewed setup.
import { useEffect, useMemo, useState } from "react";
import { saveAdjustments, saveComparableAttributes, type AdjustmentFactor, type AdjustmentLine, type AdjustmentRow, type AdjustmentRule, type AdjustmentSetup, type ComparableAttributes, type PreparedAnalysis, type RuleFactor } from "@/lib/api";

const FACTORS: { key: AdjustmentFactor; label: string; transactional?: boolean }[] = [
  { key: "conditions_of_sale", label: "Conditions of sale", transactional: true }, { key: "financing", label: "Financing", transactional: true },
  { key: "market_conditions", label: "Market conditions (time)", transactional: true }, { key: "location", label: "Location" },
  { key: "size", label: "Size" }, { key: "floor", label: "Floor" }, { key: "position", label: "Position in building" }, { key: "grade", label: "Grade" }, { key: "frontage", label: "Frontage" }, { key: "street_width", label: "Street width" }, { key: "corner", label: "Corner" },
  { key: "shape", label: "Shape" }, { key: "condition", label: "Condition" }, { key: "age", label: "Age" }, { key: "quality", label: "Quality" },
  { key: "occupancy", label: "Occupancy" }, { key: "development_potential", label: "Development potential" }, { key: "zoning", label: "Zoning" }, { key: "other", label: "Other" },
];
const FACTOR_LABEL = Object.fromEntries(FACTORS.map(f => [f.key, f.label])) as Record<AdjustmentFactor, string>;
const BASIS = { percent: "%", sar_per_sqm: "SAR/m²", sar_total: "SAR total" } as const;
const n0 = new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 });
const pct = (v: number | null | undefined, digits = 1) => v == null ? "—" : `${(v * 100).toFixed(digits)}%`;
const EMPTY: AdjustmentSetup = { lines: [], rules: [], time: null, weighting: "equal", manual_weights: {}, weighting_rationale: null, conclusion_basis: "median", exclusions: {} };
const amountLabel = (l: AdjustmentLine) => l.basis === "percent" ? `${l.amount >= 0 ? "+" : ""}${(l.amount * 100).toFixed(1)}%` : `${l.amount >= 0 ? "+" : ""}${n0.format(l.amount)} ${BASIS[l.basis]}`;

// What one percentage means for each comparison factor. The rate itself is always the reviewer's.
const RULES: Record<RuleFactor, { label: string; each: string; attribute: keyof ComparableAttributes | null }> = {
  size: { label: "Size", each: "Each 100 m² larger than the sale", attribute: null },
  floor: { label: "Floor", each: "Each floor higher than the sale", attribute: "floor" },
  position: { label: "Position", each: "Each step better: rear → side → front → corner", attribute: "position" },
  grade: { label: "Grade", each: "Each grade better: C → B → A → A+", attribute: "grade" },
  street_width: { label: "Street width", each: "Each metre wider than the sale", attribute: "street_width_m" },
  corner: { label: "Corner", each: "If this property is a corner and the sale isn’t", attribute: "corner" },
};
const fmtValue = (v: unknown) => v == null ? "not set" : v === true ? "yes" : v === false ? "no" : String(v);
export function AttributeInput({ factor, value, onChange }: { factor: RuleFactor; value: ComparableAttributes; onChange: (patch: ComparableAttributes) => void }) {
  const cls = "mizan-compact-input !w-28 !py-1.5 text-right";
  if (factor === "floor") return <input aria-label="Floor" className={cls} type="number" step="1" value={value.floor ?? ""} onChange={e => onChange({ floor: e.target.value === "" ? null : Math.trunc(Number(e.target.value)) })} placeholder="Not set" />;
  if (factor === "street_width") return <input aria-label="Street width in metres" className={cls} type="number" min="0" step="any" value={value.street_width_m ?? ""} onChange={e => onChange({ street_width_m: e.target.value === "" ? null : Number(e.target.value) })} placeholder="Not set" />;
  if (factor === "position") return <select aria-label="Position in building" className={cls} value={value.position ?? ""} onChange={e => onChange({ position: (e.target.value || null) as ComparableAttributes["position"] })}><option value="">Not set</option><option value="rear">Rear</option><option value="side">Side</option><option value="front">Front</option><option value="corner">Corner</option></select>;
  if (factor === "grade") return <select aria-label="Grade" className={cls} value={value.grade ?? ""} onChange={e => onChange({ grade: (e.target.value || null) as ComparableAttributes["grade"] })}><option value="">Not set</option><option value="A+">A+</option><option value="A">A</option><option value="B">B</option><option value="C">C</option></select>;
  if (factor === "corner") return <select aria-label="Corner plot" className={cls} value={value.corner == null ? "" : value.corner ? "yes" : "no"} onChange={e => onChange({ corner: e.target.value === "" ? null : e.target.value === "yes" })}><option value="">Not set</option><option value="yes">Yes</option><option value="no">No</option></select>;
  return null;
}

type Props = { propertyId: string; prepared: PreparedAnalysis; disabled: boolean; onSaved: (p: PreparedAnalysis) => void; onSelectEvidence: (id: string) => void; onEvidenceChanged: () => void };

export default function AdjustmentGrid({ propertyId, prepared, disabled, onSaved, onSelectEvidence, onEvidenceChanged }: Props) {
  const saved = useMemo(() => ({ ...EMPTY, ...(prepared.adjustment_setup || {}) }), [prepared.adjustment_setup]);
  const [setup, setSetup] = useState<AdjustmentSetup>(saved);
  const [reason, setReason] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const savedKey = JSON.stringify(saved);
  // Adopt the server's saved grid only when there are no unsaved local edits.
  const [base, setBase] = useState(savedKey);
  const dirty = JSON.stringify(setup) !== base;
  useEffect(() => { if (!dirty) { setSetup(saved); setBase(savedKey); } }, [savedKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const a = prepared.adjustment_analysis!;
  const rows: AdjustmentRow[] = [...a.rows, ...a.excluded];
  const update = (patch: Partial<AdjustmentSetup>) => setSetup(s => ({ ...s, ...patch }));
  const setLine = (index: number, patch: Partial<AdjustmentLine> | null) => setSetup(s => ({ ...s,
    lines: patch ? s.lines.map((l, i) => i === index ? { ...l, ...patch } : l) : s.lines.filter((_, i) => i !== index) }));

  const factors = prepared.comparison_factors || ["size"];
  const subject = prepared.subject_attributes || {};
  const setRule = (factor: RuleFactor, patch: Partial<AdjustmentRule> | null) => setSetup(s => {
    const rest = s.rules.filter(r => r.factor !== factor); const current = s.rules.find(r => r.factor === factor);
    return { ...s, rules: patch ? [...rest, { factor, percent: 0, source: "Reviewer judgement", status: "approved" as const, ...current, ...patch }] : rest }; });

  async function save() {
    setBusy(true); setError("");
    try {
      const p = await saveAdjustments(propertyId, { expected_revision: prepared.revision, reason: reason.trim() || "Reviewed comparable adjustments", adjustments: setup });
      setBase(JSON.stringify({ ...EMPTY, ...(p.adjustment_setup || {}) })); setReason(""); onSaved(p);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }

  return <section className="space-y-3 text-xs" aria-label="Comparable adjustment grid">
    <div className="flex items-start justify-between gap-2">
      <p className="text-[12.5px] text-black/50">Unit values are SAR per m². Only adjustments you approve are applied.</p>
      {dirty && <span className="mizan-chip !bg-amber-50 !border-amber-200 !text-amber-900">Unsaved changes</span>}
    </div>

    {/* Reconciled outcome from the last saved grid. */}
    <div className="grid grid-cols-2 gap-2">
      <div className="rounded bg-slate-50 p-2"><p className="text-slate-500">Concluded unit value</p>
        <p className="text-base font-semibold">{a.concluded_sar_sqm == null ? "Not available" : `${n0.format(a.concluded_sar_sqm)} SAR/m²`}</p>
        <p className="text-[10px] text-slate-500">{a.conclusion_basis.replaceAll("_", " ")} · {a.weighting.replaceAll("_", " ")} weights · n={a.rows.length}</p></div>
      <div className="rounded bg-slate-50 p-2"><p className="text-slate-500">Indication (subject area)</p>
        {a.indication ? <><p className="text-base font-semibold">SAR {n0.format(a.indication.base)}</p>
          <p className="text-[10px] text-slate-500">IQR {n0.format(a.indication.low)} – {n0.format(a.indication.high)} · not a confidence interval</p></> : <p className="text-slate-500">Needs subject area and a valid grid</p>}</div>
    </div>
    {a.raw && a.adjusted && <table className="w-full text-[12px] tabular-nums [&_td]:py-1 [&_td:not(:first-child)]:text-right [&_th]:pb-1 [&_th]:font-medium [&_th]:text-black/40 [&_th:not(:first-child)]:text-right [&_tr]:border-b [&_tr]:border-black/[0.05]">
      <thead><tr><th className="text-left">SAR/m²</th><th>Raw</th><th>Adjusted</th></tr></thead>
      <tbody>
        <tr><td className="text-black/55">Median</td><td>{n0.format(a.raw.median)}</td><td>{n0.format(a.adjusted.median)}</td></tr>
        <tr><td className="text-black/55">Mean</td><td>{n0.format(a.raw.mean)}</td><td>{n0.format(a.adjusted.mean)}</td></tr>
        <tr><td className="text-black/55">Weighted median</td><td>—</td><td>{a.adjusted.weighted_median == null ? "—" : n0.format(a.adjusted.weighted_median)}</td></tr>
        <tr><td className="text-black/55">Weighted mean</td><td>—</td><td>{a.adjusted.weighted_mean == null ? "—" : n0.format(a.adjusted.weighted_mean)}</td></tr>
        <tr><td className="text-black/55">Middle half</td><td>{n0.format(a.raw.p25)}–{n0.format(a.raw.p75)}</td><td>{n0.format(a.adjusted.p25)}–{n0.format(a.adjusted.p75)}</td></tr>
        <tr><td className="text-black/55">Spread (CV)</td><td>{pct(a.raw.cv, 0)}</td><td>{pct(a.adjusted.cv, 0)}</td></tr>
      </tbody></table>}
    {!!a.gaps.length && <ul className="list-disc pl-4 text-amber-900">{a.gaps.map(g => <li key={g}>{g}</li>)}</ul>}
    {a.pending_count > 0 && <p className="text-amber-800">{a.pending_count} proposed adjustment(s) saved but not approved — not applied.</p>}
    {a.orphaned_lines.length > 0 && <p className="text-amber-800">{a.orphaned_lines.length} saved adjustment(s) refer to comparables that are no longer eligible and are ignored.</p>}

    {/* One line per factor; it applies to every sale from the difference in details. */}
    <div className="rounded-xl bg-black/[0.03] p-3"><h4 className="text-[13.5px] font-semibold text-black/80">Compare to this property</h4>
      <p className="mb-2 text-[12px] leading-snug text-black/50">Set a rate once and it applies to every sale. Use a minus sign to lower the sale’s value. Mizan doesn’t suggest rates.</p>
      <ul className="space-y-2.5">{factors.map(f => { const def = RULES[f]; const rule = setup.rules.find(r => r.factor === f);
        return <li key={f}><div className="flex items-center gap-2"><span className="min-w-0 flex-1"><span className="block text-[13.5px] font-medium text-black/80">{def.label}</span>
            <span className="block text-[11.5px] leading-snug text-black/50">{def.each}{def.attribute ? ` · this property: ${fmtValue(subject[def.attribute])}` : ""}</span></span>
          <label className="flex items-center gap-1 whitespace-nowrap text-[13px] text-black/60"><input aria-label={`${def.label} rate in percent`} type="number" step="0.1" min="-50" max="50" placeholder="0" className="mizan-compact-input !w-16 !py-1.5 text-right"
            value={rule ? Number((rule.percent * 100).toFixed(3)) : ""} onChange={e => e.target.value === "" ? setRule(f, null) : setRule(f, { percent: Number(e.target.value) / 100 })} />%</label></div>
          {rule && <input aria-label={`${def.label} rate source`} className="mizan-compact-input mt-1 !text-[11.5px]" value={rule.source} placeholder="Basis for this rate" onChange={e => setRule(f, { source: e.target.value })} />}
        </li>; })}</ul>
      {!dirty && setup.rules.length > 0 && <p className="mt-2 text-[11.5px] text-black/45">Applied. A manual adjustment on a sale replaces the rule for that sale.</p>}
    </div>

    {/* Time rule and reconciliation settings. */}
    <details className="rounded border border-slate-200 p-2" open={!!setup.time}>
      <summary className="font-medium cursor-pointer">Market conditions (time) rule {setup.time ? `· ${pct(setup.time.annual_rate)}/yr · ${setup.time.status}` : "· none"}</summary>
      {setup.time ? <div className="grid grid-cols-2 gap-2 mt-2">
        <label>Annual change (%)<input className="mizan-compact-input" type="number" step="0.1" value={Number((setup.time.annual_rate * 100).toFixed(4))} onChange={e => update({ time: { ...setup.time!, annual_rate: Number(e.target.value) / 100 } })} /></label>
        <label>Source date<input className="mizan-compact-input" type="date" value={setup.time.as_of} onChange={e => update({ time: { ...setup.time!, as_of: e.target.value } })} /></label>
        <label className="col-span-2">Source / basis<input className="mizan-compact-input" value={setup.time.source} placeholder="e.g. index, paired sales, reviewer judgement" onChange={e => update({ time: { ...setup.time!, source: e.target.value } })} /></label>
        <label className="flex items-center gap-1.5"><input type="checkbox" checked={setup.time.status === "approved"} onChange={e => update({ time: { ...setup.time!, status: e.target.checked ? "approved" : "proposed" } })} />Approved</label>
        <button type="button" className="text-left text-red-700 underline" onClick={() => update({ time: null })}>Remove rule</button>
        <p className="col-span-2 text-[10px] text-slate-500">Compounded from each sale date to the valuation date ({prepared.as_of}). No rate is suggested by Mizan.</p></div>
        : <button type="button" className="mt-2 text-blue-700 underline" onClick={() => update({ time: { annual_rate: 0, source: "", as_of: prepared.as_of, status: "proposed" } })}>Add a sourced annual market-change rate</button>}
    </details>
    <div className="grid grid-cols-2 gap-2">
      <label>Weighting<select className="mizan-compact-input" value={setup.weighting} onChange={e => update({ weighting: e.target.value as AdjustmentSetup["weighting"] })}>
        <option value="equal">Equal</option><option value="inverse_gross_adjustment">Inverse gross adjustment</option><option value="manual">Manual (with rationale)</option></select></label>
      <label>Conclude on<select className="mizan-compact-input" value={setup.conclusion_basis} onChange={e => update({ conclusion_basis: e.target.value as AdjustmentSetup["conclusion_basis"] })}>
        <option value="median">Median</option><option value="mean">Mean</option><option value="weighted_median">Weighted median</option><option value="weighted_mean">Weighted mean</option></select></label>
      {setup.weighting === "inverse_gross_adjustment" && <p className="col-span-2 text-[10px] text-slate-500">Weight ∝ 1 ÷ (5% + gross adjustment): less-adjusted sales count more.</p>}
      {setup.weighting === "manual" && <label className="col-span-2">Weighting rationale<input className="mizan-compact-input" value={setup.weighting_rationale || ""} onChange={e => update({ weighting_rationale: e.target.value })} placeholder="Why these weights" /></label>}
    </div>

    {/* One card per comparable. */}
    <ul className="space-y-1.5">{rows.map(r => {
      const excluded = r.id in setup.exclusions; const lines = setup.lines.map((l, i) => [l, i] as const).filter(([l]) => l.comparable_id === r.id);
      return <li key={r.id} className={`rounded-xl ${excluded ? "bg-black/[0.03] opacity-70" : "ring-1 ring-black/[0.06]"}`}>
        <button type="button" className="w-full text-left px-2 py-1.5" aria-expanded={open === r.id} onClick={() => { setOpen(open === r.id ? null : r.id); onSelectEvidence(r.id); }}>
          <div className="flex items-center gap-2"><span className="font-medium truncate flex-1" dir="auto">{r.title || r.id}</span>
            <span className="whitespace-nowrap">{n0.format(r.raw_sar_sqm)} → <strong>{n0.format(r.adjusted_sar_sqm)}</strong></span></div>
          <div className="flex gap-2 text-[10px] text-slate-500"><span>{r.date || "undated"} · {r.distance_km ?? "—"} km · {r.area_sqm == null ? "area —" : `${n0.format(r.area_sqm)} m²`}</span>
            <span className="ml-auto">gross {pct(r.gross_adjustment, 0)} · net {pct(r.net_adjustment, 0)}{r.weight != null ? ` · w ${(r.weight * 100).toFixed(0)}%` : ""}{excluded ? " · excluded" : ""}</span></div>
          {r.notes.map(n => <p key={n} className="text-[10px] text-amber-800">{n}</p>)}
        </button>
        {open === r.id && <div className="border-t border-slate-100 px-2 py-2 space-y-2">
          {!excluded && <ComparableDetails key={JSON.stringify(r.attributes)} entityId={r.id.replace(/^comparable:/, "")} factors={factors} attributes={r.attributes} onSaved={onEvidenceChanged} />}
          {r.steps.filter(s => s.derived).map((s, i) => <p key={i} className="text-[12px] text-black/70"><span className="font-medium">{FACTOR_LABEL[s.factor]}</span> {amountLabel(s)} <span className="text-black/45">({s.rationale})</span></p>)}
          {lines.map(([l, i]) => <div key={i} className="grid grid-cols-[1fr_auto] gap-1 rounded bg-slate-50 p-1.5">
            <div className="grid grid-cols-3 gap-1">
              <select aria-label="Factor" className="mizan-compact-input" value={l.factor} onChange={e => setLine(i, { factor: e.target.value as AdjustmentFactor })}>{FACTORS.map(f => <option key={f.key} value={f.key}>{f.label}</option>)}</select>
              <select aria-label="Basis" className="mizan-compact-input" value={l.basis} onChange={e => setLine(i, { basis: e.target.value as AdjustmentLine["basis"] })}>{Object.entries(BASIS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
              <input aria-label={l.basis === "percent" ? "Amount in percent" : "Amount in SAR"} className="mizan-compact-input" type="number" step="any"
                value={l.basis === "percent" ? Number((l.amount * 100).toFixed(4)) : l.amount} onChange={e => setLine(i, { amount: l.basis === "percent" ? Number(e.target.value) / 100 : Number(e.target.value) })} />
              <input aria-label="Rationale" className="mizan-compact-input col-span-3" value={l.rationale} placeholder="Rationale (required)" onChange={e => setLine(i, { rationale: e.target.value })} />
              <input aria-label="Source" className="mizan-compact-input col-span-2" value={l.source || ""} placeholder="Source (optional)" onChange={e => setLine(i, { source: e.target.value || null })} />
              <label className="flex items-center gap-1"><input type="checkbox" checked={l.status === "approved"} onChange={e => setLine(i, { status: e.target.checked ? "approved" : "proposed" })} />Approved</label>
            </div>
            <button type="button" aria-label="Remove adjustment" className="text-red-700 px-1 self-start" onClick={() => setLine(i, null)}>×</button>
          </div>)}
          <button type="button" className="text-blue-700 underline" onClick={() => update({ lines: [...setup.lines, { comparable_id: r.id, factor: "location", basis: "percent", amount: 0, rationale: "", source: null, status: "proposed" }] })}>+ Add adjustment</button>
          {setup.weighting === "manual" && !excluded && <label className="flex items-center gap-2">Weight<input className="mizan-compact-input !w-24" type="number" min={0} step="any" value={setup.manual_weights[r.id] ?? ""}
            onChange={e => update({ manual_weights: { ...setup.manual_weights, [r.id]: Number(e.target.value) } })} /></label>}
          {excluded ? <div className="flex gap-2 items-center"><span className="text-slate-600">Excluded: {setup.exclusions[r.id]}</span>
            <button type="button" className="text-blue-700 underline" onClick={() => { const next = { ...setup.exclusions }; delete next[r.id]; update({ exclusions: next }); }}>Include again</button></div>
            : <ExcludeControl onExclude={why => update({ exclusions: { ...setup.exclusions, [r.id]: why } })} />}
        </div>}
      </li>; })}</ul>

    <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-2">
      <input aria-label="Reason for this revision" className="mizan-compact-input flex-1 min-w-[160px]" value={reason} onChange={e => setReason(e.target.value)} placeholder="Reason for this revision" />
      <button type="button" className="mizan-button !py-1 !px-3 !text-xs" disabled={!dirty || busy || disabled} onClick={save}>{busy ? "Saving…" : "Save adjustments"}</button>
      {dirty && <button type="button" className="text-slate-600 underline" onClick={() => setSetup(JSON.parse(base))}>Discard</button>}
    </div>
    {error && <p role="alert" className="mizan-error !text-xs">{error}</p>}
    <details><summary className="cursor-pointer text-slate-500">Method conventions</summary><ul className="list-disc pl-4 mt-1 text-slate-500">{a.conventions.map(c => <li key={c}>{c}</li>)}</ul></details>
  </section>;
}

function ComparableDetails({ entityId, factors, attributes, onSaved }: { entityId: string; factors: RuleFactor[]; attributes: ComparableAttributes; onSaved: () => void }) {
  const editable = factors.filter(f => RULES[f].attribute);
  const [draft, setDraft] = useState<ComparableAttributes>(attributes); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  if (!editable.length) return null;
  const clean = (a: ComparableAttributes) => { const { is_demo: _demo, ...rest } = a; return rest; };
  const changed = JSON.stringify(draft) !== JSON.stringify(attributes);
  async function save() {
    setBusy(true); setError("");
    try { await saveComparableAttributes(entityId, clean(draft), "Reviewed comparable details"); onSaved(); }
    catch (e) { setError((e as Error).message); setBusy(false); }
  }
  return <div className="rounded-lg bg-black/[0.03] p-2"><p className="mb-1 text-[12px] font-medium text-black/60">This sale’s details</p>
    <div className="space-y-1.5">{editable.map(f => <div key={f} className="flex items-center justify-between gap-2 text-[13px] text-black/70"><span>{RULES[f].label}</span><AttributeInput factor={f} value={draft} onChange={p => setDraft(d => ({ ...d, ...p }))} /></div>)}</div>
    {changed && <button type="button" disabled={busy} onClick={save} className="mt-2 text-[13px] font-medium text-[#007AFF] disabled:opacity-40">{busy ? "Saving…" : "Save details"}</button>}
    {error && <p role="alert" className="mt-1 text-[12px] text-[#c4271d]">{error}</p>}
  </div>;
}

function ExcludeControl({ onExclude }: { onExclude: (reason: string) => void }) {
  const [why, setWhy] = useState("");
  return <div className="flex gap-1"><input aria-label="Exclusion reason" className="mizan-compact-input" value={why} onChange={e => setWhy(e.target.value)} placeholder="Reason to exclude" />
    <button type="button" className="text-red-700 underline whitespace-nowrap disabled:text-slate-300" disabled={why.trim().length < 3} onClick={() => onExclude(why.trim())}>Exclude</button></div>;
}
