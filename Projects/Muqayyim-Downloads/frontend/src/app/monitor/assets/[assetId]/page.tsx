"use client";
// One asset: its value, why it moved, the evidence, and what you can do about it. Audit detail is at the bottom.
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ExternalLink } from "lucide-react";
import { addOfficial, ageLabel, errorText, getAsset, getAudit, getCatalog, inRange, overrideInput, patchAsset, pct, RANGES, recordEvent, requestFormal, revalueAsset, sar, setAlertStatus, titleCase, triggerLabel, type Alert, type AssetDetail, type AuditEntry, type GradeDetail, type InputMeta, type RangeKey } from "@/lib/monitor";
import { DriverBars, ValueChart } from "@/components/monitor/charts";
import { AlertRow, Button, Card, DemoBanner, Field, GradeLabel, Movement, OriginBadge, Stat, inputClass } from "@/components/monitor/ui";
import { Segmented } from "@/components/ui/sheet-ui";

const today = () => new Date(Date.now() + 3 * 3600000).toISOString().slice(0, 10);
const showInput = (i: Pick<InputMeta, "unit" | "value">) => i.unit === "ratio" ? `${(i.value * 100).toFixed(2)}%` : `${i.value.toLocaleString("en-SA", { maximumFractionDigits: 2 })} ${i.unit}`;
type Panel = null | "formal" | "official" | "event";

export default function AssetPage() {
  const { assetId } = useParams<{ assetId: string }>();
  const [a, setA] = useState<AssetDetail | null>(null); const [error, setError] = useState(""); const [notice, setNotice] = useState(""); const [panel, setPanel] = useState<Panel>(null); const [range, setRange] = useState<RangeKey>("all"); const [window_, setWindow] = useState<"official" | "last">("official"); const [editing, setEditing] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const load = useCallback(() => getAsset(assetId).then(setA).catch(e => setError(errorText(e))), [assetId]);
  useEffect(() => { load(); }, [load]);
  const run = async (fn: () => Promise<AssetDetail | void>, done?: string) => { setBusy(true); setError(""); setNotice(""); try { const r = await fn(); if (r) setA(r); else await load(); if (done) setNotice(done); setPanel(null); setEditing(null); } catch (e) { setError(errorText(e)); } setBusy(false); };
  const points = useMemo(() => {
    if (!a) return [];
    let official: number | null = null; const rows = new Map<string, { date: string; indicative: number | null; official: number | null; low: number | null; high: number | null }>(); let last: number | null = null;
    for (const s of a.history) { const row = rows.get(s.valued_on) ?? { date: s.valued_on, indicative: last, official, low: null, high: null };
      if (s.kind === "official") { official = s.value; row.official = s.value; } else { last = s.value; row.indicative = s.value; row.low = s.low; row.high = s.high; if (official != null && row.official == null) row.official = official; }
      rows.set(s.valued_on, row); }
    return Array.from(rows.values()).sort((x, y) => x.date.localeCompare(y.date));
  }, [a]);
  if (error && !a) return <p className="rounded-xl bg-[#FF3B30]/10 px-4 py-3 text-[14px] text-[#c4271d]">{error}</p>;
  if (!a) return <p className="py-16 text-center text-[14px] text-black/40">Loading…</p>;
  const s = a.summary; const asOf = today();
  const attribution = window_ === "official" && a.attribution_since_official ? a.attribution_since_official : a.attribution;
  const onAlert = (x: Alert, status: Alert["status"]) => run(async () => { await setAlertStatus(x.id, status, status === "accepted" ? "Reviewed on the asset page" : undefined); });
  const openAlerts = a.alerts.filter(x => x.status !== "resolved");
  return <div>
    <Link href={`/monitor/${a.portfolio.id}`} className="-ml-1.5 mb-2 inline-flex items-center text-[14px] text-[#007AFF]" dir="auto"><ChevronLeft size={18} />{a.portfolio.name}</Link>
    <h1 className="text-[26px] font-semibold leading-tight tracking-tight" dir="auto">{a.name}</h1>
    <p className="mb-4 text-[13px] text-black/45">{[a.district, a.city, titleCase(a.property_type)].filter(Boolean).join(" · ")}{a.ownership_pct !== 100 ? ` · ${a.ownership_pct}% owned` : ""}</p>
    {a.is_demo && <DemoBanner />}
    {notice && <p className="mb-4 rounded-xl bg-[#007AFF]/10 px-4 py-2.5 text-[13px] text-[#0058b8]">{notice}</p>}
    {error && <p className="mb-4 rounded-xl bg-[#FF3B30]/10 px-4 py-2.5 text-[13px] text-[#c4271d]">{error}</p>}

    <section className="mb-5 rounded-2xl bg-white p-5 ring-1 ring-black/[0.05]">
      <div className="flex items-center gap-2 text-[13px] text-black/50">Current Mizan value <OriginBadge origin={a.origin} /></div>
      {a.value != null ? <>
        <div className="mt-0.5 text-[40px] font-semibold leading-none tracking-tight text-black/90">{sar(a.value)}</div>
        {a.change_vs_official_pct != null ? <p className="mt-2 text-[16px]"><Movement value={a.change_vs_official_pct}><b className="font-semibold">{pct(a.change_vs_official_pct)}</b></Movement> <span className="text-black/50">against the official valuation of {sar(a.official_value)}</span></p> : <p className="mt-2 text-[14px] text-black/50">No official valuation recorded.</p>}
        <div className="mt-4 grid grid-cols-2 gap-4 border-t border-black/[0.06] pt-4 sm:grid-cols-4">
          <Stat label="Range" value={a.low != null ? <span className="text-[16px]">{sar(a.low).replace("SAR ", "")} to {sar(a.high).replace("SAR ", "")}</span> : "—"} detail={a.low != null ? "Across methods and sales. Not a probability" : "One method, no range"} />
          <Stat label="Confidence" value={<GradeLabel grade={a.confidence} />} detail={s.confidence_total ? `${s.confidence_passed} of ${s.confidence_total} checks strong` : undefined} />
          <Stat label="Previous Mizan value" value={sar(s.previous_value)} detail={s.change_pct != null ? `${pct(s.change_pct)} since ${s.previous_on}` : undefined} />
          <Stat label="Last material update" value={<span className="text-[16px]">{ageLabel(a.valued_on, asOf)}</span>} detail={triggerLabel(s.trigger)} />
        </div></> : <div className="mt-2"><p className="text-[17px] font-semibold text-black/80">No Mizan value yet</p><p className="mt-1 text-[14px] text-black/55">Mizan will not estimate one without reviewed inputs. {a.gaps.length ? "Still needed:" : "Save inputs in the valuation first."}</p>
        {a.gaps.length > 0 && <ul className="mt-1 list-disc pl-5 text-[13.5px] text-black/60">{a.gaps.map(g => <li key={g}>{g}</li>)}</ul>}
        {a.official_value != null && <p className="mt-2 text-[14px] text-black/60">Latest official valuation: {sar(a.official_value)} on {a.official_on}.</p>}</div>}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button tone={panel === "formal" ? "primary" : "plain"} onClick={() => setPanel(panel === "formal" ? null : "formal")}>{a.formal_requested_at ? "Formal valuation recommended ✓" : "Recommend formal valuation"}</Button>
        <Button onClick={() => setPanel(panel === "official" ? null : "official")}>Record official valuation</Button>
        <Button onClick={() => setPanel(panel === "event" ? null : "event")}>Record event</Button>
        <Button disabled={busy} onClick={() => run(async () => { const r = await revalueAsset(a.id); setNotice(r.changed ? "New valuation recorded." : "No evidence or input has changed, so no new valuation was recorded."); return r.asset; })}>Check now</Button>
        <Link className="inline-flex items-center gap-1.5 rounded-full bg-black/[0.06] px-3.5 py-1.5 text-[13.5px] font-medium text-black/80 hover:bg-black/[0.09]" href={`/map?analysis=${a.property_id}`}>Open valuation<ExternalLink size={13} /></Link>
      </div>
      {panel === "formal" && <SimpleForm label="Why should this be formally revalued?" cta="Recommend" busy={busy} onSubmit={v => run(() => requestFormal(a.id, v), "Recommendation recorded in the audit trail.")} initial={openAlerts[0]?.title ?? ""} />}
      {panel === "official" && <OfficialForm busy={busy} onSubmit={b => run(() => addOfficial(a.id, b), "Official valuation recorded.")} />}
      {panel === "event" && <EventForm busy={busy} onSubmit={b => run(async () => { await recordEvent(a.id, b); }, "Event recorded. It does not change the value unless an input changes too.")} />}
    </section>

    {openAlerts.length > 0 && <Card title="Needs attention"><div className="-my-2.5 divide-y divide-black/[0.06]">{openAlerts.map(x => <AlertRow key={x.id} alert={x} onStatus={st => onAlert(x, st)} />)}</div></Card>}

    {attribution && <Card title="Why it changed" action={a.attribution_since_official && a.attribution ? <div className="w-[230px]"><Segmented label="Period" value={window_} options={[{ value: "official", label: "Since official" }, { value: "last", label: "Last update" }]} onChange={setWindow} /></div> : undefined} footer={attribution.note}>
      <p className="mb-3 text-[15px]">Mizan&apos;s value moved <Movement value={attribution.total}><b className="font-semibold">{sar(attribution.total, true)}</b></Movement>{attribution.from_date ? ` since ${attribution.from_date}` : " in the last update"}.</p>
      {attribution.drivers.length ? <DriverBars drivers={attribution.drivers} /> : <p className="text-[13.5px] text-black/50">{attribution.total ? "This change could not be split into drivers." : "No input or evidence moved the value."}</p>}
      {attribution.gap_at_official != null && <p className="mt-3 border-t border-black/[0.06] pt-2 text-[12.5px] text-black/50">On {attribution.official_on} Mizan read {sar(attribution.model_value_at_official)} against the official {sar(attribution.official_value)}. That gap of {sar(attribution.gap_at_official, true)} is part of the difference from official, but cannot be attributed, since an official valuation does not record model inputs.</p>}
    </Card>}

    <Card title="Value history" action={<div className="w-[220px]"><Segmented label="Period" value={range} options={RANGES.map(r => ({ value: r.value, label: r.label }))} onChange={setRange} /></div>}>
      <ValueChart points={inRange(points, range, asOf)} label="Asset value over time" /></Card>

    {a.methods.length > 0 && <Card title="Methods" footer={a.reconciliation?.basis === "reviewer_weights" ? "Reconciled with your weights." : a.methods.length > 1 ? "Reconciled as the median of the available methods, because no reviewer weights are set. Set weights below if you prefer." : "Only one method has complete evidence, so it stands alone."}>
      {a.divergence && a.alerts.some(x => x.kind === "method_divergence" && x.status !== "resolved") && <p className="mb-3 rounded-xl bg-[#FF9500]/12 px-3 py-2 text-[13px] text-[#8a4e00]"><b>Methods disagree by {a.divergence.spread_pct.toFixed(0)}%.</b> Before relying on the reconciled value, look for an unusual sale, abnormal rent, stale comparables, redevelopment potential or a cost anomaly.</p>}
      <ul className="m-0 list-none divide-y divide-black/[0.05] p-0">{a.methods.map(m => <li key={m.key} className="flex items-baseline justify-between py-1.5 text-[14.5px]"><span className="text-black/70">{m.label}{m.weight != null ? <span className="ml-2 text-[12px] text-black/45">{(m.weight * 100).toFixed(0)}%</span> : null}</span><span className="tabular-nums text-black/85">{sar(m.value)}</span></li>)}
        <li className="flex items-baseline justify-between pt-2 text-[14.5px] font-semibold"><span>Reconciled value</span><span className="tabular-nums">{sar(a.value)}</span></li></ul>
      {a.methods.length > 1 && <WeightsForm methods={a.methods} current={a.method_weights} busy={busy} onSubmit={w => run(() => patchAsset(a.id, { method_weights: w }), "Weights saved and recorded as a new valuation.")} />}
    </Card>}

    {a.evidence.length > 0 && <Card title={`Comparable sales · ${a.evidence.length}`} footer="Eligible sales behind the latest value. New means it arrived since the official valuation.">
      <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-[13.5px]"><thead><tr className="text-left text-[12px] text-black/45"><th className="py-1 font-medium">Sale</th><th className="py-1 font-medium">Date</th><th className="py-1 text-right font-medium">SAR/m²</th><th className="py-1 text-right font-medium">vs this asset</th><th className="py-1 text-right font-medium">Source</th></tr></thead>
        <tbody className="divide-y divide-black/[0.05]">{a.evidence.map(c => <tr key={c.id}><td className="max-w-[230px] truncate py-1.5" dir="auto">{c.title}{c.is_new && <span className="ml-2 rounded bg-[#007AFF]/10 px-1.5 py-[1px] text-[10.5px] font-semibold text-[#0058b8]">NEW</span>}</td><td className="whitespace-nowrap py-1.5 text-black/55">{c.date}</td><td className="py-1.5 text-right tabular-nums">{Math.round(c.price_per_sqm).toLocaleString("en-SA")}</td><td className="py-1.5 text-right tabular-nums"><Movement value={c.vs_implied_pct}>{pct(c.vs_implied_pct)}</Movement></td><td className="py-1.5 text-right"><OriginBadge origin={c.origin} /></td></tr>)}</tbody></table></div></Card>}

    {a.methods.length > 0 && <Card title="Assumptions" footer="An override keeps the reviewed value, and records who changed it, when and why. It takes effect straight away as a new valuation.">
      <Inputs methods={a.methods} asOf={asOf} editing={editing} setEditing={setEditing} busy={busy} onSave={(field, value, reason) => run(() => overrideInput(a.id, { field, value, reason }), "Assumption changed. Why it changed is now in the audit trail.")} /></Card>}

    <div className="grid gap-x-5 md:grid-cols-2">
      {a.confidence_detail && <GradeCard grade={a.confidence_detail} />}
      <Card title="Data freshness" footer="Shown so old evidence can be told from new.">
        <ul className="m-0 list-none space-y-1.5 p-0 text-[13.5px]">{[["Comparable sales", s.freshness?.newest_sale], ["Newest input", s.freshness?.newest_input], ["Oldest input", s.freshness?.oldest_input], ["Official valuation", a.official_on], ["Last checked", a.last_checked_at?.slice(0, 10)]].filter(([, d]) => d !== undefined).map(([l, d]) => <li key={l} className="flex justify-between gap-3"><span className="text-black/60">{l}</span><span className="text-black/80">{d ? ageLabel(d, asOf) : "None"}</span></li>)}</ul></Card>
    </div>

    <Card title="Holding" footer="Facts you enter here are labelled user provided. Where NOI or occupancy are blank, Mizan shows what the saved income inputs imply and labels it derived."><HoldingForm a={a} busy={busy} onSubmit={b => run(() => patchAsset(a.id, b), "Saved.")} /></Card>

    <Timeline a={a} />
  </div>;
}

function GradeCard({ grade }: { grade: GradeDetail }) {
  const color: Record<string, string> = { good: "text-[#1c7a3a]", fair: "text-[#a85f00]", poor: "text-[#c4271d]" };
  return <Card title="Why this confidence" footer={grade.basis}><ul className="m-0 list-none space-y-1.5 p-0 text-[13.5px]">{grade.checks.map(c => <li key={c.key} className="flex items-baseline justify-between gap-3"><span className="text-black/60">{c.label}<span className="block text-[12px] text-black/40">{c.detail}</span></span><span className={`font-medium capitalize ${color[c.state] ?? ""}`}>{c.state}</span></li>)}</ul></Card>;
}

function Inputs({ methods, asOf, editing, setEditing, busy, onSave }: { methods: AssetDetail["methods"]; asOf: string; editing: string | null; setEditing: (k: string | null) => void; busy: boolean; onSave: (field: string, value: number | null, reason: string) => void }) {
  const [showAll, setShowAll] = useState(false);
  const unique = new Map<string, InputMeta>(); methods.forEach(m => m.inputs?.forEach(i => { if (!unique.has(i.key)) unique.set(i.key, i); }));
  const all = Array.from(unique.values());
  // The inputs that move value most often come first; the rest stay one tap away unless one is overridden or open.
  const KEY = ["annual_rent", "vacancy", "operating_expenses", "cap_rate", "discount_rate", "exit_cap_rate", "area_sqm", "land_value", "construction_cost"];
  const main = all.filter(i => KEY.includes(i.key) || i.override || i.key === editing).sort((x, y) => (KEY.indexOf(x.key) + 99) % 99 - (KEY.indexOf(y.key) + 99) % 99).slice(0, Math.max(5, all.filter(i => i.override || i.key === editing).length));
  const list = showAll ? all : main;
  return <><ul className="m-0 list-none divide-y divide-black/[0.05] p-0">{list.map(i => <li key={i.key} className="py-2">
    <div className="flex flex-wrap items-baseline justify-between gap-x-3"><span className="text-[14px] text-black/75">{i.label}{i.override && <span className="ml-2 rounded bg-[#007AFF]/10 px-1.5 py-[1px] text-[10.5px] font-semibold text-[#0058b8]">OVERRIDDEN</span>}</span>
      <span className="flex items-baseline gap-3"><span className="tabular-nums text-[14px] font-medium">{showInput(i)}</span><button type="button" className="text-[13px] text-[#007AFF]" onClick={() => setEditing(editing === i.key ? null : i.key)}>Adjust</button></span></div>
    <div className="text-[12px] text-black/45" dir="auto">{i.source ?? "No source"} · {ageLabel(i.as_of, asOf)} · {titleCase(i.status)}</div>
    {editing === i.key && <OverrideForm input={i} busy={busy} onSubmit={(v, r) => onSave(i.key, v, r)} />}
  </li>)}</ul>
  {all.length > main.length && <button type="button" className="mt-2 text-[13px] text-[#007AFF]" onClick={() => setShowAll(v => !v)}>{showAll ? "Show fewer" : `Show all ${all.length}`}</button>}</>;
}

function OverrideForm({ input, busy, onSubmit }: { input: InputMeta; busy: boolean; onSubmit: (value: number | null, reason: string) => void }) {
  const ratio = input.unit === "ratio";
  const submit = (e: FormEvent<HTMLFormElement>) => { e.preventDefault(); const f = new FormData(e.currentTarget); const n = Number(f.get("value")); onSubmit(ratio ? n / 100 : n, String(f.get("reason"))); };
  return <form onSubmit={submit} className="mt-2 grid gap-2 rounded-xl bg-black/[0.03] p-3 sm:grid-cols-[140px_1fr_auto] sm:items-end">
    <Field label={`New value${ratio ? " (%)" : ` (${input.unit})`}`}><input name="value" type="number" step="any" required defaultValue={ratio ? +(input.value * 100).toFixed(4) : input.value} className={inputClass} /></Field>
    <Field label="Why?"><input name="reason" required minLength={3} maxLength={500} className={inputClass} placeholder="Your justification" /></Field>
    <div className="flex gap-1.5"><Button type="submit" tone="primary" disabled={busy}>Apply</Button>{input.override && <Button disabled={busy} onClick={() => onSubmit(null, "Returned to the reviewed value")}>Remove override</Button>}</div>
  </form>;
}

function SimpleForm({ label, cta, initial, busy, onSubmit }: { label: string; cta: string; initial: string; busy: boolean; onSubmit: (v: string) => void }) {
  return <form onSubmit={e => { e.preventDefault(); onSubmit(String(new FormData(e.currentTarget).get("v"))); }} className="mt-3 grid gap-2 rounded-xl bg-black/[0.03] p-3 sm:grid-cols-[1fr_auto] sm:items-end"><Field label={label}><input name="v" required minLength={3} maxLength={500} defaultValue={initial} className={inputClass} /></Field><Button type="submit" tone="primary" disabled={busy}>{cta}</Button></form>;
}

function OfficialForm({ busy, onSubmit }: { busy: boolean; onSubmit: (b: { value_sar: number; valued_on: string; valuer: string; note?: string }) => void }) {
  return <form onSubmit={e => { e.preventDefault(); const f = new FormData(e.currentTarget); onSubmit({ value_sar: Number(f.get("value")), valued_on: String(f.get("date")), valuer: String(f.get("valuer")), note: String(f.get("note") || "") || undefined }); }} className="mt-3 grid gap-2 rounded-xl bg-black/[0.03] p-3 sm:grid-cols-4 sm:items-end">
    <Field label="Value (SAR)"><input name="value" type="number" min="1" step="any" required className={inputClass} /></Field><Field label="Valuation date"><input name="date" type="date" required max={today()} className={inputClass} /></Field><Field label="Valuer"><input name="valuer" required maxLength={255} className={inputClass} /></Field><Field label="Note (optional)"><input name="note" maxLength={1000} className={inputClass} /></Field>
    <div className="sm:col-span-4"><Button type="submit" tone="primary" disabled={busy}>Record</Button></div></form>;
}

function EventForm({ busy, onSubmit }: { busy: boolean; onSubmit: (b: { event_type: string; occurred_on: string; summary: string }) => void }) {
  const [types, setTypes] = useState<string[]>([]);
  useEffect(() => { getCatalog().then(c => setTypes(Object.keys(c.event_types))).catch(() => undefined); }, []);
  return <form onSubmit={e => { e.preventDefault(); const f = new FormData(e.currentTarget); onSubmit({ event_type: String(f.get("type")), occurred_on: String(f.get("date")), summary: String(f.get("summary")) }); }} className="mt-3 grid gap-2 rounded-xl bg-black/[0.03] p-3 sm:grid-cols-[170px_150px_1fr_auto] sm:items-end">
    <Field label="What happened"><select name="type" className={inputClass}>{types.map(t => <option key={t} value={t}>{titleCase(t)}</option>)}</select></Field><Field label="When"><input name="date" type="date" required defaultValue={today()} className={inputClass} /></Field><Field label="Details"><input name="summary" required minLength={3} maxLength={1000} className={inputClass} /></Field><Button type="submit" tone="primary" disabled={busy}>Record</Button></form>;
}

function WeightsForm({ methods, current, busy, onSubmit }: { methods: AssetDetail["methods"]; current: Record<string, number> | null; busy: boolean; onSubmit: (w: Record<string, number> | null) => void }) {
  const [open, setOpen] = useState(false);
  if (!open) return <button type="button" className="mt-2 text-[13px] text-[#007AFF]" onClick={() => setOpen(true)}>{current ? "Change weights" : "Set weights"}</button>;
  return <form onSubmit={e => { e.preventDefault(); const f = new FormData(e.currentTarget); onSubmit(Object.fromEntries(methods.map(m => [m.key, Number(f.get(m.key))]))); }} className="mt-3 grid gap-2 rounded-xl bg-black/[0.03] p-3 sm:grid-cols-4 sm:items-end">
    {methods.map(m => <Field key={m.key} label={`${m.label} (relative)`}><input name={m.key} type="number" min="0.01" step="any" required defaultValue={current?.[m.key] ?? 1} className={inputClass} /></Field>)}
    <div className="flex gap-1.5 sm:col-span-4"><Button type="submit" tone="primary" disabled={busy}>Apply weights</Button>{current && <Button disabled={busy} onClick={() => onSubmit(null)}>Back to median</Button>}</div></form>;
}

function HoldingForm({ a, busy, onSubmit }: { a: AssetDetail; busy: boolean; onSubmit: (b: Record<string, unknown>) => void }) {
  const number = (f: FormData, k: string) => { const v = String(f.get(k) ?? ""); return v === "" ? null : Number(v); };
  return <form onSubmit={e => { e.preventDefault(); const f = new FormData(e.currentTarget); onSubmit({ ownership_pct: number(f, "own") ?? 100, debt_sar: number(f, "debt"), acquisition_cost_sar: number(f, "cost"), book_value_sar: number(f, "book"), noi_sar_year: number(f, "noi"), occupancy_pct: number(f, "occ"), wault_years: number(f, "wault"), next_formal_on: String(f.get("next") || "") || null, monitoring_frequency: f.get("mon"), formal_frequency: f.get("formal") }); }} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
    <Field label="Ownership (%)"><input name="own" type="number" min="0.01" max="100" step="any" defaultValue={a.ownership_pct} className={inputClass} /></Field>
    <Field label="Debt (SAR, 100% basis)"><input name="debt" type="number" min="0" step="any" defaultValue={a.debt_sar ?? ""} className={inputClass} /></Field>
    <Field label="Acquisition cost (SAR)"><input name="cost" type="number" min="0" step="any" defaultValue={a.acquisition_cost_sar ?? ""} className={inputClass} /></Field>
    <Field label="Book value (SAR)"><input name="book" type="number" min="0" step="any" defaultValue={a.book_value_sar ?? ""} className={inputClass} /></Field>
    <Field label="NOI (SAR/year)"><input name="noi" type="number" step="any" defaultValue={a.facts?.noi_sar_year ?? ""} placeholder={a.summary.model_noi != null ? `${Math.round(a.summary.model_noi).toLocaleString("en-SA")} derived` : ""} className={inputClass} /></Field>
    <Field label="Occupancy (%)"><input name="occ" type="number" min="0" max="100" step="any" defaultValue={a.facts?.occupancy_pct ?? ""} placeholder={a.summary.model_occupancy_pct != null ? `${a.summary.model_occupancy_pct.toFixed(1)} derived` : ""} className={inputClass} /></Field>
    <Field label="WAULT (years)"><input name="wault" type="number" min="0" step="any" defaultValue={a.facts?.wault_years ?? ""} className={inputClass} /></Field>
    <Field label="Next formal valuation"><input name="next" type="date" defaultValue={a.next_formal_on ?? ""} className={inputClass} /></Field>
    <Field label="Look for evidence"><select name="mon" defaultValue={a.monitoring_frequency} className={inputClass}>{["event_driven", "daily", "weekly", "monthly", "quarterly"].map(x => <option key={x} value={x}>{titleCase(x)}</option>)}</select></Field>
    <Field label="Formal valuation every"><select name="formal" defaultValue={a.formal_frequency} className={inputClass}>{["monthly", "quarterly"].map(x => <option key={x} value={x}>{titleCase(x)}</option>)}</select></Field>
    <div className="col-span-2 flex items-end sm:col-span-2"><Button type="submit" tone="primary" disabled={busy}>Save holding</Button></div></form>;
}

function Timeline({ a }: { a: AssetDetail }) {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const show = () => getAudit(a.id).then(r => setEntries(r.entries));
  return <Card title="Audit trail" footer={entries ? "Newest first. Snapshots are immutable: a change always adds a record." : undefined}>
    {entries === null ? <button type="button" className="text-[14px] text-[#007AFF]" onClick={show}>Show every valuation, trigger and action</button> :
      <ol className="m-0 max-h-[520px] list-none space-y-2 overflow-y-auto p-0">{entries.map((e, i) => <li key={i} className="grid grid-cols-[86px_1fr] gap-3 text-[13.5px]"><time className="tabular-nums text-black/45">{e.on}</time><div><span className={e.kind === "valuation" || e.kind === "official" ? "font-medium text-black/85" : "text-black/70"} dir="auto">{e.text}{e.after != null && <> {e.before != null ? `${sar(e.before)} → ` : ""}{sar(e.after)}</>}</span>
        {e.kind === "valuation" && <span className="block text-[12px] text-black/45">{triggerLabel(e.trigger)} · {e.model} · {e.calculation_version}</span>}
        {e.details?.reason && <span className="block text-[12px] text-black/45" dir="auto">Reason: {e.details.reason}{e.details.changes ? ` · ${e.details.changes.map((c: { label: string; before: number; after: number }) => `${c.label} ${c.before} → ${c.after}`).join(", ")}` : ""}</span>}</div></li>)}</ol>}
  </Card>;
}
