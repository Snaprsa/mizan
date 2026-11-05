"use client";
// The valuer's adjustment table, laid out like a valuation sheet: one column per comparable, the main
// factors as rows, a weight per comparable and a rounded rate for the subject. Every number shown is
// calculated by the API (a preview while editing, the saved grid otherwise); this file does no valuation maths.
import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Plus, X } from "lucide-react";
import { errorText } from "@/lib/monitor";
import { getSizeEffect, previewAdjustments, saveAdjustments, type SizeEffect, type AdjustmentAnalysis, type AdjustmentFactor, type AdjustmentRow, type AdjustmentSetup, type PreparedAnalysis } from "@/lib/api";

const EMPTY: AdjustmentSetup = { lines: [], rules: [], time: null, weighting: "equal", manual_weights: {}, weighting_rationale: null, conclusion_basis: "median", exclusions: {} };
// The big factors valuers use for most comparables. Anything else is one tap away, never shown empty.
const PRELIMINARY: { key: AdjustmentFactor; label: string }[] = [{ key: "conditions_of_sale", label: "Market conditions / negotiation" }, { key: "financing", label: "Financing terms" }];
const MAIN: { key: AdjustmentFactor; label: string }[] = [{ key: "size", label: "Area" }, { key: "location", label: "Location" }, { key: "frontage", label: "No. of frontages" }];
const MORE: { key: AdjustmentFactor; label: string }[] = [{ key: "street_width", label: "Street width" }, { key: "corner", label: "Corner" }, { key: "shape", label: "Shape" },
  { key: "zoning", label: "Zoning / use" }, { key: "condition", label: "Condition" }, { key: "age", label: "Age" }, { key: "floor", label: "Floor" },
  { key: "position", label: "Position in building" }, { key: "grade", label: "Grade" }, { key: "other", label: "Other" }];
const LABEL = Object.fromEntries([...PRELIMINARY, ...MAIN, ...MORE].map(f => [f.key, f.label])) as Record<string, string>;
const DEFAULT_WHY = "Valuer's judgement";
const ROUNDING = [0, 10, 50, 100, 500, 1000];
const n0 = new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 });
const num = (v: number | null | undefined) => v == null || !Number.isFinite(v) ? "—" : n0.format(v);
// Signs after the number would read oddly in English; keep them in front, with a real minus.
const pctText = (v: number | null | undefined) => { if (v == null || !Number.isFinite(v)) return "—"; const p = Math.round(Math.abs(v) * 1000) / 10;
  return p === 0 ? "0%" : `${v < 0 ? "−" : "+"}${p % 1 ? p.toFixed(1) : p.toFixed(0)}%`; };
const monthYear = (d: string | null) => { if (!d) return "—"; const t = new Date(`${d}T00:00:00`); return Number.isNaN(t.getTime()) ? d : t.toLocaleDateString("en-GB", { month: "short", year: "2-digit" }).replace(" ", "-"); };

type Props = { propertyId: string; prepared: PreparedAnalysis; onSaved: (p: PreparedAnalysis) => void; onClose: () => void; subjectArea: number | null };

export default function AdjustmentSheet({ propertyId, prepared, onSaved, onClose, subjectArea }: Props) {
  const saved = useMemo<AdjustmentSetup>(() => ({ ...EMPTY, ...(prepared.adjustment_setup || {}) }), [prepared.adjustment_setup]);
  const [setup, setSetup] = useState<AdjustmentSetup>(saved);
  const [preview, setPreview] = useState<AdjustmentAnalysis | null>(prepared.adjustment_analysis || null);
  const [checking, setChecking] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const [extra, setExtra] = useState<AdjustmentFactor[]>([]);
  // Market-derived area adjustment: measured from saved evidence, applied only when the valuer chooses.
  const [size, setSize] = useState<SizeEffect | null>(null); const [sizeOpen, setSizeOpen] = useState(false); const [sizeBusy, setSizeBusy] = useState(false);
  const [sizeScope, setSizeScope] = useState({ radius: 10, years: 3 }); const [sizeError, setSizeError] = useState("");
  async function measureSize(scope = sizeScope) {
    setSizeOpen(true); setSizeBusy(true); setSizeError(""); setSizeScope(scope);
    try { setSize(await getSizeEffect(propertyId, scope.radius, scope.years * 365)); } catch (e) { setSizeError(errorText(e)); } finally { setSizeBusy(false); }
  }
  function useSize() {
    if (!size?.model) return;
    const m = size.model; const years = Math.round(size.lookback_days / 365);
    const why = `Market size effect: ${pctText(m.per_doubling)} per doubling of area, from ${m.n} records within ${size.radius_km} km over ${years} year${years === 1 ? "" : "s"} (R² ${m.r2 == null ? "—" : m.r2.toFixed(2)})`;
    setNotice("");
    setSetup(s => {
      const keep = s.lines.filter(l => !(l.factor === "size" && l.basis === "percent" && size.suggestions.some(x => x.comparable_id === l.comparable_id && x.percent != null)));
      const added = size.suggestions.filter(x => x.percent != null).map(x => ({ comparable_id: x.comparable_id, factor: "size" as AdjustmentFactor, basis: "percent" as const,
        amount: Math.round(x.percent! * 1000) / 1000, rationale: why, source: `Mizan size analysis, ${size.as_of}`, status: "approved" as const }));
      return { ...s, lines: [...keep, ...added] };
    });
    setSizeOpen(false);
  }
  const dirty = JSON.stringify(setup) !== JSON.stringify(saved);

  // Recalculate on the server shortly after each edit; nothing is stored until Save.
  const ask = useRef<AbortController | null>(null);
  useEffect(() => {
    if (!dirty) { setPreview(prepared.adjustment_analysis || null); setChecking(false); return; }
    setChecking(true);
    const t = setTimeout(() => {
      ask.current?.abort(); const c = new AbortController(); ask.current = c;
      previewAdjustments(propertyId, clean(setup), { signal: c.signal }).then(r => { setPreview(r.adjustment_analysis); setError(""); setChecking(false); })
        .catch(e => { if ((e as Error).name !== "AbortError") { setError(errorText(e)); setChecking(false); } });
    }, 300);
    return () => clearTimeout(t);
  }, [setup]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const k = (e: KeyboardEvent) => e.key === "Escape" && onClose(); window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onClose]);

  const rows: AdjustmentRow[] = preview?.rows || prepared.adjustment_analysis?.rows || [];
  const used = new Set(setup.lines.map(l => l.factor));
  const extraRows = MORE.filter(f => used.has(f.key) || extra.includes(f.key) || rows.some(r => r.steps.some(s => s.factor === f.key)));

  // The valuer's own percentage for one factor and comparable, if any.
  const lineOf = (factor: AdjustmentFactor, id: string) => setup.lines.find(l => l.factor === factor && l.comparable_id === id && l.basis === "percent");
  function setCell(factor: AdjustmentFactor, id: string, text: string) {
    setNotice("");
    setSetup(s => {
      const rest = s.lines.filter(l => !(l.factor === factor && l.comparable_id === id && l.basis === "percent"));
      if (text.trim() === "" || text.trim() === "-") return { ...s, lines: rest };
      const value = Number(text.replace("−", "-").replace("%", ""));
      if (!Number.isFinite(value)) return s;
      const why = s.lines.find(l => l.factor === factor)?.rationale || DEFAULT_WHY;
      return { ...s, lines: [...rest, { comparable_id: id, factor, basis: "percent", amount: value / 100, rationale: why, source: null, status: "approved" }] };
    });
  }
  // What the calculation applied for a factor, including rules or the time rate set elsewhere.
  function applied(factor: AdjustmentFactor, r: AdjustmentRow) {
    const steps = r.steps.filter(s => s.factor === factor);
    if (!steps.length) return null;
    const base = steps[0].stage === "transactional" ? steps[0].base_sar_sqm : r.transaction_adjusted_sar_sqm;
    return steps.reduce((t, s) => t + s.delta_sar_sqm, 0) / base;
  }
  const manual = setup.weighting === "manual";
  const weightOf = (r: AdjustmentRow) => manual ? setup.manual_weights[r.id] ?? 0 : (r.weight ?? 1 / rows.length) * 100;
  const weightTotal = rows.reduce((t, r) => t + (manual ? setup.manual_weights[r.id] ?? 0 : 0), 0);
  function setWeight(id: string, text: string) {
    setNotice("");
    setSetup(s => {
      const start = s.weighting === "manual" ? s.manual_weights : Object.fromEntries(rows.map(r => [r.id, Math.round(((r.weight ?? 1 / rows.length) * 100) * 100) / 100]));
      const value = text === "" ? 0 : Math.max(0, Number(text));
      return { ...s, weighting: "manual", conclusion_basis: "weighted_mean", weighting_rationale: s.weighting_rationale || DEFAULT_WHY,
        manual_weights: { ...start, [id]: Number.isFinite(value) ? value : 0 } };
    });
  }
  const resetWeights = () => setSetup(s => ({ ...s, weighting: "equal", manual_weights: {}, weighting_rationale: null, conclusion_basis: s.conclusion_basis.startsWith("weighted") ? "mean" : s.conclusion_basis }));

  async function save() {
    setBusy(true); setError("");
    try {
      const p = await saveAdjustments(propertyId, { expected_revision: prepared.revision, reason: `Adjustment table: ${setup.lines.length} adjustment(s), ${manual ? "manual" : "equal"} weights${setup.round_to ? `, rounded to ${setup.round_to}` : ""}`, adjustments: clean(setup) });
      onSaved(p); setNotice("Saved. The valuation now uses this table.");
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  // The pick is owned by the Comparables section; keep whatever is saved now.
  function clean(s: AdjustmentSetup): AdjustmentSetup { return { ...s, selected: prepared.adjustment_setup?.selected ?? null }; }

  const a = preview;
  const rate = a?.concluded_sar_sqm ?? null; const exact = a?.concluded_unrounded_sar_sqm ?? rate;
  const basisLabel: Record<string, string> = { median: "median", mean: "average", weighted_mean: "weighted average", weighted_median: "weighted median" };
  const factorRow = (f: { key: AdjustmentFactor; label: string }) => <tr key={f.key}>
    <th scope="row" className="sheet-label">{f.label}{f.key === "size" && <button type="button" onClick={() => measureSize()} className="ml-2 rounded-full bg-[#0071E3]/10 px-2 py-0.5 text-[11.5px] font-semibold text-[#0062C4] hover:bg-[#0071E3]/15">Suggest from market</button>}</th>
    {rows.map(r => { const own = lineOf(f.key, r.id); const got = applied(f.key, r);
      return <td key={r.id} className="sheet-cell"><span className="relative inline-flex items-center">
        <input aria-label={`${f.label}, comparable ${rows.indexOf(r) + 1}, percent`} inputMode="decimal" className="sheet-input" placeholder={own || got == null ? "0" : (got * 100).toFixed(1).replace(/\.0$/, "")}
          defaultValue={own ? String(Number((own.amount * 100).toFixed(2))) : ""} key={`${f.key}-${r.id}-${own ? own.amount : "none"}`}
          onBlur={e => { if (e.target.value !== (own ? String(Number((own.amount * 100).toFixed(2))) : "")) setCell(f.key, r.id, e.target.value); }}
          onKeyDown={e => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} /><span className="pointer-events-none absolute right-2 text-[12px] text-[#5F5F64]">%</span></span>
        {!own && got != null && Math.abs(got) > 0.00005 && <span className="mt-0.5 block text-[10.5px] text-[#5F5F64]">from a rule</span>}</td>; })}
  </tr>;
  const resultRow = (label: string, values: (r: AdjustmentRow) => string, strong = false) => <tr className={strong ? "sheet-strong" : "sheet-total"}>
    <th scope="row" className="sheet-label">{label}</th>{rows.map(r => <td key={r.id} className="sheet-cell tabular-nums">{values(r)}</td>)}</tr>;
  const band = (label: string) => <tr><th colSpan={rows.length + 1} className="sheet-band">{label}</th></tr>;

  return createPortal(<div className="mizan-fade-in fixed inset-0 z-[1200] flex items-end justify-center bg-black/30 sm:items-center sm:p-6" role="dialog" aria-modal="true" aria-label="Adjustment table" onClick={onClose}>
    <div className="mizan-rise-in flex max-h-[92vh] w-full max-w-[1100px] flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:rounded-2xl" onClick={e => e.stopPropagation()}>
      <div className="flex items-center gap-3 border-b border-black/[0.06] px-5 py-3.5">
        <div className="flex-1"><h3 className="text-[17px] font-semibold text-[#1D1D1F]">Adjustment table</h3>
          <p className="text-[12.5px] text-[#5F5F64]">Type a percentage in a cell; use a minus for a worse comparable. {checking ? "Recalculating…" : dirty ? "Not saved yet." : "Saved."}</p></div>
        <button type="button" aria-label="Close" onClick={onClose} className="grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-[#1D1D1F] hover:bg-black/[0.08]"><X size={17} /></button>
      </div>

      {sizeOpen && <SizePanel result={size} busy={sizeBusy} error={sizeError} scope={sizeScope} rows={rows} onScope={measureSize} onUse={useSize} onClose={() => setSizeOpen(false)} />}
      <div className="overflow-auto">{rows.length === 0 ? <p className="p-8 text-center text-[14px] text-[#5F5F64]">Pick at least 3 comparables first.</p> :
        <table className="mizan-sheet w-full border-separate border-spacing-0 text-[13.5px]" style={{ minWidth: 220 + rows.length * 128 }}>
          <thead className="sticky top-0 z-10"><tr><th className="sheet-head sheet-label">Item</th>{rows.map((r, i) => <th key={r.id} className="sheet-head" title={r.title || ""}>
            Comparable {i + 1}{r.details?.kind === "listing" && <span className="block text-[10.5px] font-medium text-[#8A5200]">Asking price</span>}{r.attributes.is_demo && <span className="block text-[10.5px] font-medium text-[#8A5200]">Demo</span>}</th>)}</tr></thead>
          <tbody>
            {resultRow("Date of transaction", r => r.details?.kind === "listing" ? `Asking · ${monthYear(r.date)}` : monthYear(r.date))}
            {resultRow("District", r => r.details?.district || "—")}
            {resultRow("Area (m²)", r => num(r.area_sqm))}
            {resultRow("Value (SAR)", r => num(r.details?.price))}
            {resultRow("Rate per m² (SAR/m²)", r => num(r.raw_sar_sqm), true)}
            {band("Preliminary adjustments")}
            {PRELIMINARY.map(factorRow)}
            {resultRow("Total preliminary adjustments", r => pctText(r.transaction_adjusted_sar_sqm / r.raw_sar_sqm - 1))}
            {resultRow("Rate per m² after preliminary adjustments", r => num(r.transaction_adjusted_sar_sqm), true)}
            {band("Property adjustments")}
            {MAIN.map(factorRow)}
            {extraRows.map(factorRow)}
            <tr><th scope="row" className="sheet-label"><AddFactor options={MORE.filter(f => !extraRows.some(x => x.key === f.key))} onAdd={k => setExtra(x => [...x, k])} /></th><td colSpan={rows.length} /></tr>
            {resultRow("Total adjustments", r => pctText((r.adjusted_sar_sqm - r.transaction_adjusted_sar_sqm) / r.transaction_adjusted_sar_sqm))}
            {resultRow("Rate per m² after final adjustments", r => num(r.adjusted_sar_sqm), true)}
            <tr className="sheet-strong"><th scope="row" className="sheet-label">Weighting</th>{rows.map(r => <td key={r.id} className="sheet-cell">
              <span className="relative inline-flex items-center"><input aria-label={`Weight of comparable ${rows.indexOf(r) + 1}, percent`} inputMode="decimal" className="sheet-input font-semibold"
                defaultValue={String(Math.round(weightOf(r) * 10) / 10)} key={`w-${r.id}-${manual}-${weightOf(r)}`}
                onBlur={e => { if (Number(e.target.value) !== Math.round(weightOf(r) * 10) / 10) setWeight(r.id, e.target.value); }} onKeyDown={e => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} />
                <span className="pointer-events-none absolute right-2 text-[12px] text-[#5F5F64]">%</span></span></td>)}</tr>
          </tbody>
        </table>}

        {rows.length > 0 && <div className="space-y-2 px-5 py-4">
          {manual && Math.abs(weightTotal - 100) > 0.05 && <p className="text-[12.5px] text-[#8A5200]">Weights add up to {n0.format(weightTotal)}%. Mizan scales them to 100%.</p>}
          <dl className="mx-auto max-w-md divide-y divide-black/[0.06] rounded-xl bg-[#F5F5F7] px-4 text-[14px]">
            <div className="flex items-center justify-between py-2.5"><dt className="text-[#5F5F64]">Rate per m² for the subject <span className="text-[12px]">({basisLabel[a?.conclusion_basis || setup.conclusion_basis]})</span></dt><dd className="font-semibold tabular-nums">{num(exact)}</dd></div>
            <div className="flex items-center justify-between py-2.5"><dt className="flex items-center gap-2 text-[#5F5F64]">Rounded to
              <select aria-label="Round the rate" className="mizan-compact-input !h-8 !w-36 !text-[13px]" value={setup.round_to ?? 0} onChange={e => { setNotice(""); setSetup(s => ({ ...s, round_to: Number(e.target.value) || null })); }}>
                {ROUNDING.map(v => <option key={v} value={v}>{v ? `nearest ${n0.format(v)}` : "no rounding"}</option>)}</select></dt>
              <dd className="text-[17px] font-semibold tabular-nums text-[#1D1D1F]">{num(rate)} <span className="text-[12px] font-normal text-[#5F5F64]">SAR/m²</span></dd></div>
            <div className="flex items-center justify-between py-2.5"><dt className="text-[#5F5F64]">Value{subjectArea ? ` · ${n0.format(subjectArea)} m²` : ""}</dt><dd className="font-semibold tabular-nums">{a?.indication ? `SAR ${n0.format(a.indication.base)}` : "Needs the subject area"}</dd></div>
          </dl>
          {!manual ? <p className="text-center text-[12px] text-[#5F5F64]">Equal weights. Type a weight to set your own.</p>
            : <p className="text-center text-[12px]"><button type="button" className="text-[#0062C4]" onClick={resetWeights}>Use equal weights</button></p>}
          {!!a?.gaps.length && <ul className="mx-auto max-w-md list-disc rounded-xl bg-[rgba(255,159,10,0.12)] py-2 pl-7 pr-3 text-[13px] text-[#8A5200]">{a.gaps.map(g => <li key={g}>{g}</li>)}</ul>}
          {rows.some(r => r.notes.length) && <details className="mx-auto max-w-md text-[12.5px]"><summary className="cursor-pointer text-[#8A5200]">Notes on {rows.filter(r => r.notes.length).length} comparable(s)</summary>
            <ul className="mt-1 space-y-1 text-[#5F5F64]">{rows.map((r, i) => r.notes.map(n => <li key={`${r.id}${n}`}>Comparable {i + 1}: {n}</li>))}</ul></details>}
          <Reasons setup={setup} onChange={(factor, why) => setSetup(s => ({ ...s, lines: s.lines.map(l => l.factor === factor ? { ...l, rationale: why } : l) }))} />
        </div>}
      </div>

      <div className="flex items-center gap-3 border-t border-black/[0.06] px-5 py-3">
        <span className={`flex-1 text-[13px] ${error ? "text-[#C0271B]" : "text-[#17722F]"}`} role={error ? "alert" : "status"}>{error || notice}</span>
        {dirty && <button type="button" className="text-[14px] font-medium text-[#0062C4]" onClick={() => { setSetup(saved); setError(""); }}>Discard</button>}
        <button type="button" disabled={!dirty || busy || checking} onClick={save} className="h-10 rounded-[12px] bg-[#0071E3] px-5 text-[14.5px] font-semibold text-white transition-opacity disabled:opacity-40">{busy ? "Saving…" : "Save"}</button>
      </div>
    </div>
  </div>, document.body);
}

// What the evidence says about plot size, in words first, numbers second; nothing is applied until "Use".
function SizePanel({ result, busy, error, scope, rows, onScope, onUse, onClose }: { result: SizeEffect | null; busy: boolean; error: string; scope: { radius: number; years: number };
  rows: AdjustmentRow[]; onScope: (s: { radius: number; years: number }) => void; onUse: () => void; onClose: () => void }) {
  const m = result?.model; const per = m ? Math.abs(m.per_doubling * 100) : 0;
  return <div className="mizan-rise-in border-b border-black/[0.06] bg-[#F5F9FF] px-5 py-4">
    <div className="flex items-start gap-3">
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-semibold uppercase tracking-wide text-[#0062C4]">Area adjustment from the market</p>
        {busy ? <p className="mt-1 text-[14px] text-[#5F5F64]">Measuring how price per m² changes with area…</p>
          : error ? <p role="alert" className="mt-1 text-[14px] text-[#C0271B]">{error}</p>
          : m ? <>
            <p className="mt-1 text-[16px] font-semibold text-[#1D1D1F]">Price per m² {m.per_doubling < 0 ? "falls" : "rises"} about {per.toFixed(1)}% each time the area doubles</p>
            <p className="mt-0.5 text-[12.5px] leading-snug text-[#5F5F64]">From {result!.sales} sales{result!.listings ? ` and ${result!.listings} asking prices` : ""} within {result!.radius_km} km over {scope.years} year{scope.years === 1 ? "" : "s"}
              {result!.area_range ? ` (${n0.format(result!.area_range[0])}–${n0.format(result!.area_range[1])} m²)` : ""}. 95% range {pctText(m.per_doubling_low)} to {pctText(m.per_doubling_high)} per doubling · fit R² {m.r2 == null ? "—" : m.r2.toFixed(2)}
              {result!.outliers_removed ? ` · ${result!.outliers_removed} extreme ${result!.outliers_removed === 1 ? "price" : "prices"} left out` : ""}{m.asking_premium != null ? ` · asking prices ${pctText(m.asking_premium)} vs sales` : ""}.</p></>
          : result ? <p className="mt-1 text-[14px] text-[#1D1D1F]">Not enough evidence to measure a size effect.</p> : null}
        {!!result?.notes.length && !busy && <ul className="mt-2 space-y-0.5 text-[12.5px] text-[#8A5200]">{result.notes.map(n => <li key={n}>{n}</li>)}</ul>}
        {m && !busy && <div className="mt-3 flex flex-wrap gap-2">{rows.map((r, i) => { const s = result!.suggestions.find(x => x.comparable_id === r.id);
          return <span key={r.id} className="rounded-lg bg-white px-2.5 py-1.5 text-[12.5px] ring-1 ring-black/[0.06]"><span className="text-[#5F5F64]">Comparable {i + 1} · {num(r.area_sqm)} m² → </span>
            <span className="font-semibold tabular-nums text-[#1D1D1F]">{s?.percent == null ? "—" : pctText(s.percent)}</span></span>; })}</div>}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-[12.5px] text-[#5F5F64]">
          <label className="flex items-center gap-1.5">Within<select className="mizan-compact-input !h-8 !w-24 !text-[13px]" value={scope.radius} disabled={busy} onChange={e => onScope({ ...scope, radius: Number(e.target.value) })}>{[3, 5, 10, 20, 30].map(v => <option key={v} value={v}>{v} km</option>)}</select></label>
          <label className="flex items-center gap-1.5">over<select className="mizan-compact-input !h-8 !w-28 !text-[13px]" value={scope.years} disabled={busy} onChange={e => onScope({ ...scope, years: Number(e.target.value) })}>{[1, 2, 3, 5].map(v => <option key={v} value={v}>{v} year{v === 1 ? "" : "s"}</option>)}</select></label>
          <span className="flex-1" />
          <button type="button" className="h-9 px-3 text-[14px] text-[#5F5F64]" onClick={onClose}>Close</button>
          <button type="button" disabled={busy || !m || !result?.suggestions.some(x => x.percent != null)} onClick={onUse} className="h-9 rounded-[10px] bg-[#0071E3] px-4 text-[14px] font-semibold text-white disabled:opacity-40">Use for the Area row</button>
        </div>
        {m && !busy && <p className="mt-2 text-[11.5px] text-[#5F5F64]">Adjustment = (subject area ÷ comparable area)<sup>b</sup> − 1, with b = {m.elasticity.toFixed(3)} from {m.formula}. Time and location are not separated out; you can still edit each cell.</p>}
      </div>
    </div>
  </div>;
}

function AddFactor({ options, onAdd }: { options: { key: AdjustmentFactor; label: string }[]; onAdd: (k: AdjustmentFactor) => void }) {
  if (!options.length) return null;
  return <label className="inline-flex cursor-pointer items-center gap-1 text-[13px] font-medium text-[#0062C4]"><Plus size={14} />
    <select aria-label="Add another factor" className="cursor-pointer appearance-none bg-transparent text-[#0062C4] outline-none" value="" onChange={e => e.target.value && onAdd(e.target.value as AdjustmentFactor)}>
      <option value="">Add a factor</option>{options.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}</select></label>;
}

// One reason per factor, recorded with every adjustment for it.
function Reasons({ setup, onChange }: { setup: AdjustmentSetup; onChange: (factor: AdjustmentFactor, why: string) => void }) {
  const factors = setup.lines.map(l => l.factor).filter((f, i, all) => all.indexOf(f) === i);
  if (!factors.length) return null;
  const why = (f: AdjustmentFactor) => setup.lines.find(l => l.factor === f)?.rationale || "";
  return <details className="mx-auto max-w-md text-[13px]"><summary className="cursor-pointer text-[#0062C4]">Reasons for the adjustments</summary>
    <div className="mt-2 space-y-2">{factors.map(f => <Fragment key={f}><label className="block text-[12.5px] text-[#5F5F64]">{LABEL[f] || f}
      <input className="mizan-compact-input mt-1" defaultValue={why(f)} onBlur={e => { const v = e.target.value.trim(); if (v.length >= 3 && v !== why(f)) onChange(f, v); }} placeholder="Why, e.g. weaker access, smaller plot" /></label></Fragment>)}</div>
    <p className="mt-1 text-[11.5px] text-[#5F5F64]">Left as “{DEFAULT_WHY}” unless you say more. Saved with the valuation.</p></details>;
}

