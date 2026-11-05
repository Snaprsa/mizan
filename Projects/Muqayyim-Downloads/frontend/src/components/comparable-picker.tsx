"use client";
// Choose the 3 to 6 sales a sales-comparison valuation uses, and see every detail of them in one table.
// The API decides eligibility and does all arithmetic; this component only records the valuer's pick.
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { Check, Table2, X } from "lucide-react";
import { errorText } from "@/lib/monitor";
import { saveAdjustments, saveComparableAttributes, type AdjustmentRow, type AdjustmentSetup, type Candidate, type ComparableAttributes, type PreparedAnalysis } from "@/lib/api";

export const MIN_PICK = 3, MAX_PICK = 6;
const EMPTY: AdjustmentSetup = { lines: [], rules: [], time: null, weighting: "equal", manual_weights: {}, weighting_rationale: null, conclusion_basis: "median", exclusions: {} };
const n0 = new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 });
const num = (v: number | null | undefined, unit = "") => v == null || !Number.isFinite(v) ? "—" : `${n0.format(v)}${unit}`;
const km = (v: number | null | undefined) => v == null ? "—" : v < 1 ? `${Math.round(v * 1000)} m` : `${v.toFixed(1)} km`;
const monthYear = (d: string | null) => { if (!d) return "—"; const t = new Date(`${d}T00:00:00`); return Number.isNaN(t.getTime()) ? d : t.toLocaleDateString("en-GB", { month: "short", year: "numeric" }); };
const title = (s: string | null | undefined) => s ? s.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()) : "—";
const name = (c: Candidate) => (c.title || c.id).replace(/^DEMO · /, "");
const isDemo = (c: Candidate) => /^DEMO · /.test(c.title || "") || !!c.attributes?.is_demo;
const EVIDENCE: Record<string, string> = { transaction_achieved: "Transaction", transaction_registered: "Registered transaction", listing_asking: "Listing" };
const USES = ["residential", "commercial", "mixed", "industrial", "agricultural", "other"] as const;
const sourceText = (s: string) => /^https?:\/\//.test(s) ? new URL(s).hostname.replace(/^www\./, "") : s;

type Props = { propertyId: string; prepared: PreparedAnalysis; disabled: boolean; onSaved: (p: PreparedAnalysis) => void; onSelectEvidence: (id: string) => void; onEvidenceChanged: () => void };

export default function ComparablePicker({ propertyId, prepared, disabled, onSaved, onSelectEvidence, onEvidenceChanged }: Props) {
  const usable = useMemo(() => prepared.candidates.filter(c => c.eligible).sort((a, b) => a.distance_km - b.distance_km), [prepared.candidates]);
  const unusable = prepared.candidates.filter(c => !c.eligible);
  const saved = prepared.adjustment_setup?.selected ?? null;
  const savedKey = JSON.stringify(saved);
  const [chosen, setChosen] = useState<string[]>(saved ?? []);
  useEffect(() => { setChosen(saved ?? []); }, [savedKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [table, setTable] = useState(false);
  const changed = JSON.stringify([...chosen].sort()) !== JSON.stringify([...(saved ?? [])].sort());
  const full = chosen.length >= MAX_PICK;

  async function store(selected: string[] | null) {
    setBusy(true); setError("");
    try {
      const reason = selected ? `Picked ${selected.length} comparable sales` : "Use every usable sale";
      onSaved(await saveAdjustments(propertyId, { expected_revision: prepared.revision, reason, adjustments: { ...EMPTY, ...(prepared.adjustment_setup || {}), selected } }));
    } catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  const toggle = (id: string) => setChosen(c => c.includes(id) ? c.filter(x => x !== id) : c.length >= MAX_PICK ? c : [...c, id]);

  // The table shows the sales the valuation uses now: the saved pick, or every usable sale before picking.
  const used = saved ? usable.filter(c => saved.includes(c.id)) : usable;
  const rows = prepared.adjustment_analysis ? new Map([...prepared.adjustment_analysis.rows, ...prepared.adjustment_analysis.excluded].map(r => [r.id, r])) : new Map<string, AdjustmentRow>();

  return <div className="space-y-3">
    <p className="text-[12.5px] leading-snug text-black/55">
      {saved ? `This valuation uses the ${saved.length} sales you picked.` : usable.length ? `All ${usable.length} usable sales within ${prepared.radius_km} km are used. Pick ${MIN_PICK} to ${MAX_PICK} to use only those.` : `No usable sales within ${prepared.radius_km} km.`}
    </p>
    {usable.length > 0 && <button type="button" onClick={() => setTable(true)} className="inline-flex items-center gap-1.5 text-[13.5px] font-medium text-[#0062C4]"><Table2 size={15} />See all details of {saved ? "the picked" : "these"} sales</button>}

    <ul className="max-h-[22rem] divide-y divide-black/[0.06] overflow-auto rounded-xl ring-1 ring-black/[0.06]">{usable.map(c => {
      const on = chosen.includes(c.id); const off = !on && full;
      return <li key={c.id} className="flex items-center gap-3 bg-white px-3 py-2.5">
        <button type="button" role="checkbox" aria-checked={on} aria-label={`Pick ${name(c)}`} disabled={off || disabled || busy} onClick={() => toggle(c.id)}
          className={`grid h-6 w-6 shrink-0 place-items-center rounded-full ring-1 transition-colors duration-150 ${on ? "bg-[#0071E3] text-white ring-[#0071E3]" : "bg-white ring-black/20"} disabled:opacity-35`}>{on && <Check size={14} strokeWidth={3} />}</button>
        <button type="button" className="min-w-0 flex-1 text-left" onClick={() => onSelectEvidence(c.id)}>
          <span className="line-clamp-2 text-[14px] font-medium leading-snug text-[#1D1D1F]" dir="auto">{name(c)}</span>
          <span className="block text-[12px] text-[#5F5F64]">{[km(c.distance_km), monthYear(c.date), c.district, c.area_sqm == null ? null : `${n0.format(c.area_sqm)} m²`, isDemo(c) ? "Demo" : null].filter(Boolean).join(" · ")}</span>
        </button>
        <span className="text-right text-[14px] font-semibold tabular-nums text-[#1D1D1F]">{num(c.price_per_sqm)}<span className="block text-[11px] font-normal text-[#5F5F64]">SAR/m²</span></span>
      </li>; })}</ul>

    {usable.length > 0 && <div className="flex flex-wrap items-center gap-3">
      <span className={`flex-1 text-[13px] ${chosen.length && chosen.length < MIN_PICK ? "text-[#8A5200]" : "text-[#5F5F64]"}`}>
        {chosen.length ? `${chosen.length} picked${chosen.length < MIN_PICK ? ` · pick ${MIN_PICK - chosen.length} more` : full ? " · the most you can pick" : ""}` : `Pick ${MIN_PICK} to ${MAX_PICK}`}</span>
      {saved && <button type="button" disabled={busy || disabled} className="text-[13.5px] text-[#5F5F64] disabled:opacity-40" onClick={() => store(null)}>Use all usable</button>}
      {changed && <button type="button" disabled={busy || disabled || chosen.length < MIN_PICK} onClick={() => store(chosen)}
        className="h-9 rounded-[10px] bg-[#0071E3] px-3.5 text-[14px] font-semibold text-white disabled:opacity-40">{busy ? "Saving…" : `Use these ${chosen.length}`}</button>}
    </div>}
    {error && <p role="alert" className="text-[12.5px] text-[#C0271B]">{error}</p>}

    {unusable.length > 0 && <details><summary className="cursor-pointer text-[12.5px] text-[#5F5F64]">{unusable.length} nearby not usable as sales</summary>
      <ul className="mt-1 max-h-48 divide-y divide-black/[0.05] overflow-auto">{unusable.slice(0, 40).map(c => <li key={c.id}><button type="button" className="block w-full py-1.5 text-left" onClick={() => onSelectEvidence(c.id)}>
        <span className="block truncate text-[13px] text-black/75" dir="auto">{name(c)}</span><span className="block text-[11.5px] text-black/45">{km(c.distance_km)} · {c.exclusion_reasons.join("; ")}</span></button></li>)}</ul></details>}

    {table && <ComparablesTable sales={used} rows={rows} picked={!!saved} onClose={() => setTable(false)} onSelect={id => { setTable(false); onSelectEvidence(id); }} onChanged={onEvidenceChanged} />}
  </div>;
}

// Every detail of the sales in use, as a valuer's comparables table. Missing details show "—" and can be added in place.
function ComparablesTable({ sales, rows, picked, onClose, onSelect, onChanged }: { sales: Candidate[]; rows: Map<string, AdjustmentRow>; picked: boolean; onClose: () => void; onSelect: (id: string) => void; onChanged: () => void }) {
  useEffect(() => { const k = (e: KeyboardEvent) => e.key === "Escape" && onClose(); window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onClose]);
  const adjusted = sales.some(c => rows.get(c.id) && Math.abs(rows.get(c.id)!.adjusted_sar_sqm - rows.get(c.id)!.raw_sar_sqm) > 0.5);
  const head = ["#", "Type", "City", "District", "Area (m²)", "Rate per m² (SAR/m²)", "Value (SAR)", "No. of frontages", "Frontage width (m)", "Street width (m)", "Corner", "Comparable type", "Transaction date", "Use", "Source", "Distance", ...(adjusted ? ["Adjusted rate (SAR/m²)"] : [])];
  // Portalled to the page so the map card's own layout cannot clip or contain it.
  return createPortal(<div className="mizan-fade-in fixed inset-0 z-[1200] flex items-end justify-center bg-black/30 p-0 sm:items-center sm:p-6" role="dialog" aria-modal="true" aria-label="Comparables table" onClick={onClose}>
    <div className="mizan-rise-in flex max-h-[88vh] w-full max-w-[1400px] flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:rounded-2xl" onClick={e => e.stopPropagation()}>
      <div className="flex items-center gap-3 border-b border-black/[0.06] px-5 py-3.5">
        <div className="flex-1"><h3 className="text-[17px] font-semibold text-[#1D1D1F]">Comparables</h3>
          <p className="text-[12.5px] text-[#5F5F64]">{sales.length} {picked ? "picked" : "usable"} sales · nearest first · tap a dash to add a missing detail</p></div>
        <button type="button" aria-label="Close" onClick={onClose} className="grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-[#1D1D1F] hover:bg-black/[0.08]"><X size={17} /></button>
      </div>
      <div className="overflow-auto">
        <table className="w-full min-w-[1280px] border-separate border-spacing-0 text-[13px] tabular-nums">
          <thead className="sticky top-0 z-10"><tr>{head.map(h => <th key={h} scope="col" className="whitespace-nowrap border-b border-black/[0.08] bg-[#F5F5F7] px-2.5 py-2.5 text-center text-[12px] font-semibold text-[#1D1D1F]">{h}</th>)}</tr></thead>
          <tbody>{sales.map((c, i) => { const row = rows.get(c.id);
            return <tr key={c.id} className="text-center text-[#1D1D1F] [&>td]:border-b [&>td]:border-black/[0.05] [&>td]:px-2.5 [&>td]:py-2.5 hover:bg-[#0071E3]/[0.03]">
              <td className="font-medium text-[#5F5F64]">{i + 1}</td>
              <td className="whitespace-nowrap text-left"><button type="button" className="font-medium text-[#0062C4] hover:underline" title={name(c)} onClick={() => onSelect(c.id)}>{title(c.property_type === "land" ? "vacant land" : c.property_type)}</button>{isDemo(c) && <span className="ml-1.5 rounded px-1 text-[10.5px] font-semibold text-[#8A5200] ring-1 ring-[#8A5200]/40">DEMO</span>}</td>
              <td>{c.city || "—"}</td>
              <td className="whitespace-nowrap" dir="auto">{c.district || "—"}</td>
              <td>{num(c.area_sqm)}</td>
              <td className="font-semibold">{num(c.price_per_sqm)}</td>
              <td>{num(c.price)}</td>
              <td><Detail sale={c} field="frontages" onChanged={onChanged} /></td>
              <td><Detail sale={c} field="frontage_m" onChanged={onChanged} /></td>
              <td><Detail sale={c} field="street_width_m" onChanged={onChanged} /></td>
              <td><Detail sale={c} field="corner" onChanged={onChanged} /></td>
              <td>{c.kind === "transaction" ? EVIDENCE[c.evidence_type || ""] || "Transaction" : title(c.kind)}</td>
              <td className="whitespace-nowrap">{monthYear(c.date)}</td>
              <td><Detail sale={c} field="use" onChanged={onChanged} /></td>
              <td className="max-w-[220px] truncate text-left">{/^https?:\/\//.test(c.source) ? <a className="text-[#0062C4] hover:underline" href={c.source} target="_blank" rel="noreferrer noopener">{sourceText(c.source)}</a> : <span title={c.source}>{c.source}</span>}</td>
              <td className="whitespace-nowrap text-[#5F5F64]">{km(c.distance_km)}</td>
              {adjusted && <td className="font-semibold">{row ? num(row.adjusted_sar_sqm) : "—"}</td>}
            </tr>; })}</tbody>
        </table>
        {!sales.length && <p className="p-6 text-center text-[14px] text-[#5F5F64]">No sales to show.</p>}
      </div>
      <p className="border-t border-black/[0.06] px-5 py-2.5 text-[11.5px] text-[#5F5F64]">Rate per m² is price ÷ recorded area. Details you add are saved to the sale with a reason and change its adjustments. Demo rows are synthetic, not market evidence.</p>
    </div>
  </div>, document.body);
}

type DetailField = "frontages" | "frontage_m" | "street_width_m" | "corner" | "use";
// One editable detail cell. The whole attribute set is sent, since the API replaces it.
function Detail({ sale, field, onChanged }: { sale: Candidate; field: DetailField; onChanged: () => void }) {
  const attrs: ComparableAttributes = sale.attributes || {};
  const value = attrs[field];
  const [editing, setEditing] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const shown = value == null ? "—" : field === "corner" ? (value ? "Yes" : "No") : field === "use" ? title(String(value)) : n0.format(Number(value));
  async function save(next: ComparableAttributes[DetailField]) {
    setBusy(true); setError("");
    const { is_demo: _demo, ...rest } = attrs;
    try { await saveComparableAttributes(sale.entity_id, { ...rest, [field]: next }, "Added in the comparables table"); setEditing(false); onChanged(); }
    catch (e) { setError(errorText(e)); } finally { setBusy(false); }
  }
  if (!editing) return <button type="button" onClick={() => setEditing(true)} className={`min-w-[2.5rem] rounded-md px-1.5 py-0.5 hover:bg-black/[0.05] ${value == null ? "text-[#5F5F64]" : ""}`} title="Edit">{shown}</button>;
  const cls = "mizan-compact-input !h-8 !w-28 text-center !text-[13px]";
  const cancel = () => { setEditing(false); setError(""); };
  const field_ = field === "corner"
    ? <select autoFocus aria-label="Corner" className={cls} defaultValue={value == null ? "" : value ? "yes" : "no"} disabled={busy} onBlur={cancel} onChange={e => save(e.target.value === "" ? null : e.target.value === "yes")}><option value="">Not set</option><option value="yes">Yes</option><option value="no">No</option></select>
    : field === "use"
    ? <select autoFocus aria-label="Use" className={cls} defaultValue={(value as string) ?? ""} disabled={busy} onBlur={cancel} onChange={e => save((e.target.value || null) as ComparableAttributes["use"])}><option value="">Not set</option>{USES.map(u => <option key={u} value={u}>{title(u)}</option>)}</select>
    : <input autoFocus aria-label={field} className={cls} type="number" min={field === "frontages" ? 1 : 0} max={field === "frontages" ? 4 : undefined} step={field === "frontages" ? 1 : "any"} defaultValue={value == null ? "" : String(value)} disabled={busy}
        onKeyDown={e => { if (e.key === "Escape") { e.stopPropagation(); cancel(); } if (e.key === "Enter") { const v = (e.target as HTMLInputElement).value; save(v === "" ? null : field === "frontages" ? Math.trunc(Number(v)) : Number(v)); } }}
        onBlur={e => { const v = e.target.value; const next = v === "" ? null : field === "frontages" ? Math.trunc(Number(v)) : Number(v); if (next === (value ?? null)) cancel(); else save(next); }} />;
  return <span className="inline-flex flex-col items-center">{field_}{error && <span role="alert" className="mt-0.5 max-w-[10rem] text-[11px] text-[#C0271B]">{error}</span>}</span>;
}
