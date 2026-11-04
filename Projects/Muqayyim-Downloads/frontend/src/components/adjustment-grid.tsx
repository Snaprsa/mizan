"use client";
// Reviewer adjustment grid for sales comparison. All arithmetic is done by the API
// (api/app/services/comparable_adjustments.py); this component edits and displays the reviewed setup.
import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Plus, Trash2 } from "lucide-react";
import { errorText } from "@/lib/monitor";
import { Segmented, Switch } from "@/components/ui/sheet-ui";
import { saveAdjustments, saveComparableAttributes, type AdjustmentFactor, type AdjustmentLine, type AdjustmentRow, type AdjustmentRule, type AdjustmentSetup, type ComparableAttributes, type PreparedAnalysis, type RuleFactor } from "@/lib/api";

const FACTORS: { key: AdjustmentFactor; label: string; transactional?: boolean }[] = [
  { key: "conditions_of_sale", label: "Conditions of sale", transactional: true }, { key: "financing", label: "Financing", transactional: true },
  { key: "market_conditions", label: "Market conditions (time)", transactional: true }, { key: "location", label: "Location" },
  { key: "size", label: "Size" }, { key: "floor", label: "Floor" }, { key: "position", label: "Position in building" }, { key: "grade", label: "Grade" }, { key: "frontage", label: "Frontage" }, { key: "street_width", label: "Street width" }, { key: "corner", label: "Corner" },
  { key: "shape", label: "Shape" }, { key: "condition", label: "Condition" }, { key: "age", label: "Age" }, { key: "quality", label: "Quality" },
  { key: "occupancy", label: "Occupancy" }, { key: "development_potential", label: "Development potential" }, { key: "zoning", label: "Zoning" }, { key: "other", label: "Other" },
];
const FACTOR_LABEL = Object.fromEntries(FACTORS.map(f => [f.key, f.label])) as Record<AdjustmentFactor, string>;
const BASIS = { percent: "%", sar_per_sqm: "SAR/m²", sar_total: "SAR" } as const;
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
  const cls = "mizan-compact-input !w-32 text-right";
  if (factor === "floor") return <input aria-label="Floor" className={cls} type="number" step="1" value={value.floor ?? ""} onChange={e => onChange({ floor: e.target.value === "" ? null : Math.trunc(Number(e.target.value)) })} placeholder="Not set" />;
  if (factor === "street_width") return <input aria-label="Street width in metres" className={cls} type="number" min="0" step="any" value={value.street_width_m ?? ""} onChange={e => onChange({ street_width_m: e.target.value === "" ? null : Number(e.target.value) })} placeholder="Not set" />;
  if (factor === "position") return <select aria-label="Position in building" className={cls} value={value.position ?? ""} onChange={e => onChange({ position: (e.target.value || null) as ComparableAttributes["position"] })}><option value="">Not set</option><option value="rear">Rear</option><option value="side">Side</option><option value="front">Front</option><option value="corner">Corner</option></select>;
  if (factor === "grade") return <select aria-label="Grade" className={cls} value={value.grade ?? ""} onChange={e => onChange({ grade: (e.target.value || null) as ComparableAttributes["grade"] })}><option value="">Not set</option><option value="A+">A+</option><option value="A">A</option><option value="B">B</option><option value="C">C</option></select>;
  if (factor === "corner") return <select aria-label="Corner plot" className={cls} value={value.corner == null ? "" : value.corner ? "yes" : "no"} onChange={e => onChange({ corner: e.target.value === "" ? null : e.target.value === "yes" })}><option value="">Not set</option><option value="yes">Yes</option><option value="no">No</option></select>;
  return null;
}

type Props = { propertyId: string; prepared: PreparedAnalysis; disabled: boolean; onSaved: (p: PreparedAnalysis) => void; onSelectEvidence: (id: string) => void; onEvidenceChanged: () => void };
const signed = (v: number | null | undefined, digits = 1) => v == null ? "—" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v * 100).toFixed(digits)}%`;
const km = (v: number | null | undefined) => v == null ? "—" : v < 1 ? `${Math.round(v * 1000)} m` : `${v.toFixed(1)} km`;
// A new line nobody has filled in is not an adjustment; it is dropped on save instead of blocking it.
const untouched = (l: AdjustmentLine) => !l.amount && !l.rationale.trim() && !l.source;
const lineProblem = (l: AdjustmentLine) => untouched(l) ? null : l.rationale.trim().length < 3 ? "Say why, in at least 3 characters" : !Number.isFinite(l.amount) ? "Enter a number" : null;

export default function AdjustmentGrid({ propertyId, prepared, disabled, onSaved, onSelectEvidence, onEvidenceChanged }: Props) {
  const saved = useMemo(() => ({ ...EMPTY, ...(prepared.adjustment_setup || {}) }), [prepared.adjustment_setup]);
  const [setup, setSetup] = useState<AdjustmentSetup>(saved);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [tried, setTried] = useState(false);
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

  const problems = setup.lines.map(lineProblem).filter(Boolean).length + (setup.weighting === "manual" && (setup.weighting_rationale || "").trim().length < 3 ? 1 : 0)
    + (setup.time && setup.time.source.trim().length < 3 ? 1 : 0);
  async function save() {
    setTried(true); setError("");
    if (problems) { setError(`${problems} ${problems === 1 ? "item needs" : "items need"} attention before saving. Fix the highlighted fields, or remove them.`); return; }
    setBusy(true);
    try {
      const clean = { ...setup, lines: setup.lines.filter(l => !untouched(l)) };
      const p = await saveAdjustments(propertyId, { expected_revision: prepared.revision, reason: `Reviewed comparable adjustments: ${clean.rules.length} rule(s), ${clean.lines.length} line(s), ${Object.keys(clean.exclusions).length} exclusion(s)`, adjustments: clean });
      setBase(JSON.stringify({ ...EMPTY, ...(p.adjustment_setup || {}) })); setTried(false); onSaved(p);
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }

  return <section className="space-y-4 text-[14px]" aria-label="Comparable adjustments">
    {/* Outcome from the last saved grid. */}
    <div className="rounded-2xl bg-white p-4 ring-1 ring-black/[0.06]">
      <div className="text-[12.5px] text-[#5F5F64]">Concluded unit value</div>
      <div className="text-[26px] font-semibold tabular-nums tracking-tight text-[#1D1D1F]">{a.concluded_sar_sqm == null ? "—" : `${n0.format(a.concluded_sar_sqm)} SAR/m²`}</div>
      <div className="text-[12.5px] text-[#5F5F64]">{a.indication ? <>SAR {n0.format(a.indication.base)} for the property · middle half {n0.format(a.indication.low)}–{n0.format(a.indication.high)}</> : "Needs the property's area and a valid grid"}</div>
      <div className="mt-1 text-[12px] text-[#5F5F64]">{titleOf(a.conclusion_basis)} of {a.rows.length} sales{a.excluded.length ? ` · ${a.excluded.length} excluded` : ""} · {titleOf(a.weighting)} weights</div>
      {a.raw && a.adjusted && <details className="mt-2"><summary className="cursor-pointer text-[13px] text-[#0062C4]">Statistics</summary>
        <table className="mt-2 w-full text-[12.5px] tabular-nums [&_td]:py-1 [&_td:not(:first-child)]:text-right [&_th]:pb-1 [&_th]:font-medium [&_th]:text-[#5F5F64] [&_th:not(:first-child)]:text-right [&_tr]:border-b [&_tr]:border-black/[0.05]">
          <thead><tr><th className="text-left">SAR/m²</th><th>Before</th><th>After</th></tr></thead>
          <tbody>
            <tr><td className="text-[#5F5F64]">Median</td><td>{n0.format(a.raw.median)}</td><td>{n0.format(a.adjusted.median)}</td></tr>
            <tr><td className="text-[#5F5F64]">Mean</td><td>{n0.format(a.raw.mean)}</td><td>{n0.format(a.adjusted.mean)}</td></tr>
            <tr><td className="text-[#5F5F64]">Weighted median</td><td>—</td><td>{a.adjusted.weighted_median == null ? "—" : n0.format(a.adjusted.weighted_median)}</td></tr>
            <tr><td className="text-[#5F5F64]">Middle half</td><td>{n0.format(a.raw.p25)}–{n0.format(a.raw.p75)}</td><td>{n0.format(a.adjusted.p25)}–{n0.format(a.adjusted.p75)}</td></tr>
            <tr><td className="text-[#5F5F64]">Spread (CV)</td><td>{pct(a.raw.cv, 0)}</td><td>{pct(a.adjusted.cv, 0)}</td></tr>
          </tbody></table><p className="mt-1 text-[11.5px] text-[#5F5F64]">The middle half is not a confidence interval.</p></details>}
    </div>
    {!!a.gaps.length && <ul className="list-disc rounded-xl bg-[rgba(255,159,10,0.12)] py-2 pl-7 pr-3 text-[13px] text-[#8A5200]">{a.gaps.map(g => <li key={g}>{g}</li>)}</ul>}
    {a.pending_count > 0 && <p className="text-[13px] text-[#8A5200]">{a.pending_count} saved {a.pending_count === 1 ? "adjustment is" : "adjustments are"} switched off, so not applied.</p>}
    {a.orphaned_lines.length > 0 && <p className="text-[13px] text-[#8A5200]">{a.orphaned_lines.length} saved {a.orphaned_lines.length === 1 ? "adjustment refers to a sale" : "adjustments refer to sales"} no longer eligible, and {a.orphaned_lines.length === 1 ? "is" : "are"} ignored.</p>}

    {/* One rate per factor, applied to every sale from the difference in details. */}
    <div className="rounded-2xl bg-white p-4 ring-1 ring-black/[0.06]">
      <h4 className="text-[16px] font-semibold text-[#1D1D1F]">Compare to this property</h4>
      <p className="mb-3 text-[12.5px] leading-snug text-[#5F5F64]">Set a rate once and it applies to every sale. A minus sign lowers the sale. Mizan doesn’t suggest rates.</p>
      <ul className="divide-y divide-black/[0.06]">{factors.map(f => { const def = RULES[f]; const rule = setup.rules.find(r => r.factor === f);
        return <li key={f} className="py-2.5"><div className="flex items-center gap-3"><span className="min-w-0 flex-1"><span className="block text-[14.5px] font-medium text-[#1D1D1F]">{def.label}</span>
            <span className="block text-[12px] leading-snug text-[#5F5F64]">{def.each}{def.attribute ? ` · this property: ${fmtValue(subject[def.attribute])}` : ""}</span></span>
          <label className="flex items-center gap-1.5 whitespace-nowrap text-[14px] text-[#5F5F64]"><input aria-label={`${def.label} rate in percent`} type="number" step="0.1" min="-50" max="50" placeholder="0" className="mizan-compact-input !w-20 text-right"
            value={rule ? Number((rule.percent * 100).toFixed(3)) : ""} onChange={e => e.target.value === "" ? setRule(f, null) : setRule(f, { percent: Number(e.target.value) / 100 })} />%</label></div>
          {rule && <input aria-label={`${def.label} rate basis`} className="mizan-compact-input mt-2 !h-8 !text-[13px]" value={rule.source} placeholder="Basis for this rate" onChange={e => setRule(f, { source: e.target.value })} />}
        </li>; })}</ul>
    </div>

    {/* One row per sale; details and its own adjustments one tap away. */}
    <div className="overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.06]">
      <div className="flex items-baseline justify-between px-4 pb-1 pt-3"><h4 className="text-[16px] font-semibold text-[#1D1D1F]">Sales</h4><span className="text-[12px] text-[#5F5F64]">SAR/m², after adjustments</span></div>
      <ul className="divide-y divide-black/[0.06]">{rows.map(r => {
        const excluded = r.id in setup.exclusions; const lines = setup.lines.map((l, i) => [l, i] as const).filter(([l]) => l.comparable_id === r.id);
        const change = r.raw_sar_sqm ? r.adjusted_sar_sqm / r.raw_sar_sqm - 1 : null; const isOpen = open === r.id;
        return <li key={r.id} className={excluded ? "bg-black/[0.02]" : ""}>
          <button type="button" className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-black/[0.02]" aria-expanded={isOpen} onClick={() => { setOpen(isOpen ? null : r.id); onSelectEvidence(r.id); }}>
            <span className="min-w-0 flex-1"><span className={`line-clamp-2 text-[14.5px] font-medium leading-snug ${excluded ? "text-[#5F5F64] line-through" : "text-[#1D1D1F]"}`} dir="auto">{(r.title || r.id).replace(/^DEMO · /, "")}</span>
              <span className="block text-[12.5px] text-[#5F5F64]">{[r.date || "Undated", km(r.distance_km), r.area_sqm == null ? null : `${n0.format(r.area_sqm)} m²`].filter(Boolean).join(" · ")}</span>
              <span className="block text-[12.5px] text-[#5F5F64]">{[...factors.filter(f => RULES[f].attribute).map(f => describe(f, r.attributes)), /^DEMO · /.test(r.title || "") ? "Demo" : null].filter(Boolean).join(" · ")}</span></span>
            <span className="text-right"><span className="block text-[15px] font-semibold tabular-nums text-[#1D1D1F]">{excluded ? "Excluded" : n0.format(r.adjusted_sar_sqm)}</span>
              <span className="block text-[12px] tabular-nums text-[#5F5F64]">{excluded ? "" : !change || Math.abs(change) < 0.0005 ? `${n0.format(r.raw_sar_sqm)} · unadjusted` : `${n0.format(r.raw_sar_sqm)} · ${signed(change)}`}</span></span>
            <ChevronDown size={16} className={`shrink-0 text-[#5F5F64] transition-transform ${isOpen ? "rotate-180" : ""}`} />
          </button>
          {r.notes.length > 0 && !isOpen && <p className="-mt-1 px-4 pb-2 text-[12px] text-[#8A5200]">{r.notes[0]}</p>}
          {isOpen && <div className="space-y-3 bg-[#F5F5F7] px-4 py-3">
            {r.notes.map(n => <p key={n} className="text-[12.5px] text-[#8A5200]">{n}</p>)}
            {!excluded && <ComparableDetails key={JSON.stringify(r.attributes)} entityId={r.id.replace(/^comparable:/, "")} factors={factors} attributes={r.attributes} onSaved={onEvidenceChanged} />}
            {r.steps.length > 0 && <div><p className="mb-1 text-[12px] font-medium uppercase tracking-wide text-[#5F5F64]">Applied</p>
              <ul className="space-y-1">{r.steps.map((s, i) => <li key={i} className="flex justify-between gap-3 text-[13.5px]"><span className="min-w-0 text-[#1D1D1F]">{FACTOR_LABEL[s.factor]}<span className="block truncate text-[12px] text-[#5F5F64]">{s.derived ? "From your rate" : s.rationale}</span></span><span className="whitespace-nowrap tabular-nums">{amountLabel(s)}</span></li>)}</ul></div>}
            {!excluded && <div><p className="mb-1 text-[12px] font-medium uppercase tracking-wide text-[#5F5F64]">Adjustments for this sale only</p>
              {lines.length === 0 && <p className="text-[12.5px] text-[#5F5F64]">None. An adjustment here replaces the rate for its factor on this sale.</p>}
              <div className="space-y-2">{lines.map(([l, i]) => <LineEditor key={i} line={l} showErrors={tried} onChange={patch => setLine(i, patch)} onRemove={() => setLine(i, null)} />)}</div>
              <button type="button" className="mt-2 inline-flex items-center gap-1 text-[13.5px] font-medium text-[#0062C4]" onClick={() => update({ lines: [...setup.lines, { comparable_id: r.id, factor: factors.includes("street_width") ? "street_width" : "location", basis: "percent", amount: 0, rationale: "", source: null, status: "approved" }] })}><Plus size={15} />Add adjustment</button></div>}
            {setup.weighting === "manual" && !excluded && <label className="flex items-center justify-between gap-2 text-[13.5px]">Weight<input className="mizan-compact-input !w-24 text-right" type="number" min={0} step="any" value={setup.manual_weights[r.id] ?? ""}
              onChange={e => update({ manual_weights: { ...setup.manual_weights, [r.id]: Number(e.target.value) } })} /></label>}
            {r.weight != null && setup.weighting !== "equal" && !excluded && <p className="text-[12.5px] text-[#5F5F64]">Weight in the conclusion: {(r.weight * 100).toFixed(0)}%</p>}
            {excluded ? <div className="flex flex-wrap items-center justify-between gap-2 text-[13px]"><span className="text-[#5F5F64]">Excluded: {setup.exclusions[r.id]}</span>
              <button type="button" className="font-medium text-[#0062C4]" onClick={() => { const next = { ...setup.exclusions }; delete next[r.id]; update({ exclusions: next }); }}>Include again</button></div>
              : <ExcludeControl onExclude={why => update({ exclusions: { ...setup.exclusions, [r.id]: why } })} />}
          </div>}
        </li>; })}</ul>
    </div>

    {/* Less-used settings stay folded away. */}
    <details className="rounded-2xl bg-white p-4 ring-1 ring-black/[0.06]" open={!!setup.time || setup.weighting !== "equal"}>
      <summary className="cursor-pointer text-[15px] font-medium text-[#1D1D1F]">Time and weighting</summary>
      <div className="mt-3 space-y-3">
        {setup.time ? <div className="space-y-2">
          <div className="flex items-center justify-between gap-2"><span className="text-[14px]">Market change per year</span>
            <label className="flex items-center gap-1.5 text-[#5F5F64]"><input className="mizan-compact-input !w-20 text-right" type="number" step="0.1" value={Number((setup.time.annual_rate * 100).toFixed(4))} onChange={e => update({ time: { ...setup.time!, annual_rate: Number(e.target.value) / 100 } })} />%</label></div>
          <input className="mizan-compact-input" aria-invalid={tried && setup.time.source.trim().length < 3} value={setup.time.source} placeholder="Basis, e.g. index or paired sales (required)" onChange={e => update({ time: { ...setup.time!, source: e.target.value } })} />
          <div className="flex items-center justify-between gap-2"><label className="text-[13px] text-[#5F5F64]">Source date <input className="mizan-compact-input mt-1 !w-40" type="date" value={setup.time.as_of} onChange={e => update({ time: { ...setup.time!, as_of: e.target.value } })} /></label>
            <span className="flex items-center gap-2 text-[13.5px]">Apply<Switch label="Apply the time rule" checked={setup.time.status === "approved"} onChange={v => update({ time: { ...setup.time!, status: v ? "approved" : "proposed" } })} /></span></div>
          <p className="text-[12px] text-[#5F5F64]">Compounded from each sale date to {prepared.as_of}. <button type="button" className="text-[#C0271B]" onClick={() => update({ time: null })}>Remove</button></p></div>
          : <button type="button" className="inline-flex items-center gap-1 text-[13.5px] font-medium text-[#0062C4]" onClick={() => update({ time: { annual_rate: 0, source: "", as_of: prepared.as_of, status: "approved" } })}><Plus size={15} />Add a market change rate</button>}
        <div className="grid grid-cols-2 gap-3">
          <label className="text-[13px] text-[#5F5F64]">Weighting<select className="mizan-compact-input mt-1" value={setup.weighting} onChange={e => update({ weighting: e.target.value as AdjustmentSetup["weighting"] })}>
            <option value="equal">Equal</option><option value="inverse_gross_adjustment">Less adjusted count more</option><option value="manual">Manual</option></select></label>
          <label className="text-[13px] text-[#5F5F64]">Conclude on<select className="mizan-compact-input mt-1" value={setup.conclusion_basis} onChange={e => update({ conclusion_basis: e.target.value as AdjustmentSetup["conclusion_basis"] })}>
            <option value="median">Median</option><option value="mean">Mean</option><option value="weighted_median">Weighted median</option><option value="weighted_mean">Weighted mean</option></select></label>
        </div>
        {setup.weighting === "inverse_gross_adjustment" && <p className="text-[12px] text-[#5F5F64]">Weight is 1 ÷ (5% + gross adjustment), so sales needing less adjustment count more.</p>}
        {setup.weighting === "manual" && <input className="mizan-compact-input" aria-invalid={tried && (setup.weighting_rationale || "").trim().length < 3} value={setup.weighting_rationale || ""} onChange={e => update({ weighting_rationale: e.target.value })} placeholder="Why these weights (required)" />}
      </div>
    </details>

    {/* Save bar: only when something changed. */}
    {(dirty || error) && <div className="sticky bottom-0 z-10 -mx-1 rounded-2xl bg-white/95 p-3 shadow-[0_-4px_16px_rgba(0,0,0,0.08)] ring-1 ring-black/[0.06] backdrop-blur">
      {error && <p role="alert" className="mb-2 text-[13px] text-[#C0271B]">{error}</p>}
      <div className="flex items-center gap-3"><span className="flex-1 text-[13px] text-[#5F5F64]">{dirty ? "Unsaved changes" : ""}</span>
        {dirty && <button type="button" className="text-[14px] font-medium text-[#0062C4]" onClick={() => { setSetup(JSON.parse(base)); setError(""); setTried(false); }}>Discard</button>}
        <button type="button" className="h-10 rounded-[12px] bg-[#0071E3] px-4 text-[14.5px] font-semibold text-white disabled:opacity-40" disabled={!dirty || busy || disabled} onClick={save}>{busy ? "Saving…" : "Save"}</button></div>
    </div>}
    <details><summary className="cursor-pointer text-[13px] text-[#5F5F64]">How Mizan applies adjustments</summary><ul className="mt-1 list-disc pl-5 text-[12.5px] text-[#5F5F64]">{a.conventions.map(c => <li key={c}>{c}</li>)}</ul></details>
  </section>;
}

// The detail a rate compares on, as a short phrase; missing details say so rather than being hidden.
function describe(f: RuleFactor, a: ComparableAttributes) {
  if (f === "street_width") return a.street_width_m == null ? "street width not set" : `${n0.format(a.street_width_m)} m street`;
  if (f === "corner") return a.corner == null ? "corner not set" : a.corner ? "corner" : "not a corner";
  if (f === "floor") return a.floor == null ? "floor not set" : `floor ${a.floor}`;
  if (f === "position") return a.position ? `${a.position} position` : "position not set";
  if (f === "grade") return a.grade ? `grade ${a.grade}` : "grade not set";
  return null;
}
const titleOf = (s: string) => s.replaceAll("_", " ").replace(/^./, c => c.toUpperCase());

function LineEditor({ line, showErrors, onChange, onRemove }: { line: AdjustmentLine; showErrors: boolean; onChange: (patch: Partial<AdjustmentLine>) => void; onRemove: () => void }) {
  const problem = lineProblem(line); const flag = showErrors && !!problem;
  const percent = line.basis === "percent";
  return <div className={`rounded-xl bg-white p-3 ${flag ? "ring-2 ring-[#C0271B]" : "ring-1 ring-black/[0.06]"}`}>
    <div className="flex items-center gap-2">
      <select aria-label="Factor" className="mizan-compact-input flex-1" value={line.factor} onChange={e => onChange({ factor: e.target.value as AdjustmentFactor })}>{FACTORS.map(f => <option key={f.key} value={f.key}>{f.label}</option>)}</select>
      <input aria-label={percent ? "Amount in percent" : "Amount in SAR"} className="mizan-compact-input !w-24 text-right" type="number" step="any" placeholder="0"
        value={line.amount ? (percent ? Number((line.amount * 100).toFixed(4)) : line.amount) : ""} onChange={e => onChange({ amount: e.target.value === "" ? 0 : percent ? Number(e.target.value) / 100 : Number(e.target.value) })} />
      <button type="button" aria-label="Remove adjustment" className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-[#C0271B] hover:bg-[#C0271B]/10" onClick={onRemove}><Trash2 size={16} /></button>
    </div>
    <div className="mt-2"><Segmented label="Unit" value={line.basis} onChange={v => onChange({ basis: v, amount: 0 })} options={[{ value: "percent", label: "%" }, { value: "sar_per_sqm", label: "SAR/m²" }, { value: "sar_total", label: "SAR total" }]} /></div>
    <input aria-label="Why" aria-invalid={flag} className="mizan-compact-input mt-2" value={line.rationale} placeholder="Why? (required)" onChange={e => onChange({ rationale: e.target.value })} />
    {flag && <p className="mt-1 text-[12px] text-[#C0271B]">{problem}</p>}
    <div className="mt-2 flex items-center gap-2"><input aria-label="Source" className="mizan-compact-input flex-1 !h-8 !text-[13px]" value={line.source || ""} placeholder="Source (optional)" onChange={e => onChange({ source: e.target.value || null })} />
      <span className="flex items-center gap-2 whitespace-nowrap text-[13px] text-[#5F5F64]">Apply<Switch label="Apply this adjustment" checked={line.status === "approved"} onChange={v => onChange({ status: v ? "approved" : "proposed" })} /></span></div>
  </div>;
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
    catch (e) { setError(errorText(e)); setBusy(false); }
  }
  return <div><p className="mb-1 text-[12px] font-medium uppercase tracking-wide text-[#5F5F64]">This sale’s details</p>
    <div className="divide-y divide-black/[0.06] rounded-xl bg-white px-3 ring-1 ring-black/[0.06]">{editable.map(f => <div key={f} className="flex min-h-[48px] items-center justify-between gap-2 text-[14px] text-[#1D1D1F]"><span>{RULES[f].label}</span><AttributeInput factor={f} value={draft} onChange={p => setDraft(d => ({ ...d, ...p }))} /></div>)}</div>
    {changed && <button type="button" disabled={busy} onClick={save} className="mt-2 text-[13.5px] font-medium text-[#0062C4] disabled:opacity-40">{busy ? "Saving…" : "Save details"}</button>}
    {error && <p role="alert" className="mt-1 text-[12px] text-[#C0271B]">{error}</p>}
  </div>;
}

function ExcludeControl({ onExclude }: { onExclude: (reason: string) => void }) {
  const [open, setOpen] = useState(false); const [why, setWhy] = useState("");
  if (!open) return <button type="button" className="text-[13.5px] font-medium text-[#C0271B]" onClick={() => setOpen(true)}>Exclude this sale…</button>;
  return <div className="flex items-center gap-2"><input aria-label="Reason to exclude" autoFocus className="mizan-compact-input flex-1" value={why} onChange={e => setWhy(e.target.value)} placeholder="Why exclude it?" />
    <button type="button" className="whitespace-nowrap text-[13.5px] font-medium text-[#C0271B] disabled:opacity-40" disabled={why.trim().length < 3} onClick={() => onExclude(why.trim())}>Exclude</button>
    <button type="button" className="text-[13.5px] text-[#5F5F64]" onClick={() => { setOpen(false); setWhy(""); }}>Cancel</button></div>;
}
