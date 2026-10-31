"use client";
// Portfolio dashboard. First screen: worth, change, what needs attention. Everything else is one tap further down.
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Download, FileText, RefreshCw } from "lucide-react";
import { listProperties, type PropertySummary } from "@/lib/api";
import { addAssets, ageLabel, assetsCsv, checkPortfolio, deletePortfolio, errorText, getDashboard, getStress, inRange, listAssets, patchPortfolio, pct, RANGES, sar, setAlertStatus, titleCase, type Alert, type AssetRow, type Dashboard, type RangeKey, type StressResult } from "@/lib/monitor";
import { BubbleScatter, ShareBars, ValueChart } from "@/components/monitor/charts";
import { AlertRow, Button, Card, DemoBanner, Field, GradeLabel, Movement, OriginBadge, SeverityLabel, Stat, inputClass } from "@/components/monitor/ui";
import { Segmented } from "@/components/ui/sheet-ui";

type Tab = "overview" | "assets" | "alerts" | "priority" | "stress" | "settings";
const TABS: { value: Tab; label: string }[] = [{ value: "overview", label: "Overview" }, { value: "assets", label: "Assets" }, { value: "alerts", label: "Alerts" }, { value: "priority", label: "Revalue first" }, { value: "stress", label: "Stress" }, { value: "settings", label: "Settings" }];

function PortfolioPage() {
  const { id } = useParams<{ id: string }>(); const params = useSearchParams(); const router = useRouter();
  const tab = (params.get("tab") as Tab) || "overview"; const attentionOnly = params.get("attention") === "1";
  const [board, setBoard] = useState<Dashboard | null>(null); const [error, setError] = useState(""); const [checking, setChecking] = useState(false); const [notice, setNotice] = useState("");
  const load = useCallback(() => getDashboard(id).then(setBoard).catch(e => setError(errorText(e))), [id]);
  // Monitoring runs when someone is here: assets whose frequency says they are due get checked on open.
  useEffect(() => { load().then(() => checkPortfolio(id, true).then(r => { if (r.updated) { setNotice(`${r.updated} ${r.updated === 1 ? "asset" : "assets"} updated from new evidence.`); load(); } }).catch(() => undefined)); }, [id, load]);
  const go = (next: Tab, extra = "") => router.push(`/monitor/${id}?tab=${next}${extra}`, { scroll: false });
  const check = async () => { setChecking(true); setNotice(""); try { const r = await checkPortfolio(id); setNotice(`Checked ${r.checked} ${r.checked === 1 ? "asset" : "assets"}: ${r.updated} changed, ${r.unchanged} unchanged.`); await load(); } catch (e) { setError(errorText(e)); } setChecking(false); };
  if (error && !board) return <p className="rounded-xl bg-[#FF3B30]/10 px-4 py-3 text-[14px] text-[#c4271d]">{error}</p>;
  if (!board) return <p className="py-16 text-center text-[14px] text-black/40">Loading…</p>;
  return <div>
    <Link href="/monitor" className="-ml-1.5 mb-2 inline-flex items-center text-[14px] text-[#007AFF]"><ChevronLeft size={18} />Monitor</Link>
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0"><h1 className="text-[28px] font-semibold leading-tight tracking-tight" dir="auto">{board.name}</h1>
        <p className="text-[13px] text-black/45" dir="auto">{[board.asset_manager, board.fund].filter((v, i, a) => v && a.indexOf(v) === i).join(" · ") || "Mizan Monitor"}{board.last_checked_at ? ` · Checked ${ageLabel(board.last_checked_at.slice(0, 10), board.as_of).toLowerCase()}` : ""}</p></div>
      <div className="flex gap-2"><Button onClick={check} disabled={checking}><RefreshCw size={14} className={checking ? "animate-spin" : ""} />{checking ? "Checking…" : "Check now"}</Button><Link href={`/monitor/${id}/report`} className="inline-flex items-center gap-1.5 rounded-full bg-black/[0.06] px-3.5 py-1.5 text-[13.5px] font-medium text-black/80 hover:bg-black/[0.09]"><FileText size={14} />Report</Link></div>
    </div>
    {board.is_demo && <DemoBanner />}
    {notice && <p className="mb-4 rounded-xl bg-[#007AFF]/10 px-4 py-2.5 text-[13px] text-[#0058b8]">{notice}</p>}
    {error && <p className="mb-4 rounded-xl bg-[#FF3B30]/10 px-4 py-2.5 text-[13px] text-[#c4271d]">{error}</p>}
    <div className="mb-5 overflow-x-auto"><div className="min-w-[520px]"><Segmented label="Portfolio view" value={tab} options={TABS} onChange={v => go(v)} /></div></div>
    {tab === "overview" && <Overview board={board} onAttention={() => go("assets", "&attention=1")} onAdd={() => go("settings")} onAlerts={() => go("alerts")} />}
    {tab === "assets" && <Assets id={id} attentionOnly={attentionOnly} clearAttention={() => go("assets")} />}
    {tab === "alerts" && <Alerts board={board} reload={load} />}
    {tab === "priority" && <RevalueFirst board={board} />}
    {tab === "stress" && <Stress id={id} />}
    {tab === "settings" && <Settings board={board} reload={load} />}
  </div>;
}

function Overview({ board, onAttention, onAdd, onAlerts }: { board: Dashboard; onAttention: () => void; onAdd: () => void; onAlerts: () => void }) {
  const t = board.totals; const [range, setRange] = useState<RangeKey>("all");
  if (!t.asset_count) return <div className="rounded-2xl bg-white px-6 py-10 text-center ring-1 ring-black/[0.05]"><h2 className="text-[17px] font-semibold">No assets yet</h2><p className="mx-auto mt-1 mb-4 max-w-md text-[14px] text-black/50">Add properties you have already set up in Mizan. Their saved valuation inputs are what Monitor watches.</p><Button tone="primary" onClick={onAdd}>Add properties</Button></div>;
  const history = inRange(board.history, range, board.as_of);
  const confidence = (["high", "medium", "low"] as const).filter(k => t.confidence_share[k]);
  const notValued = t.official_only_count + t.unvalued_count;
  return <>
    <section className="mb-5 rounded-2xl bg-white p-5 ring-1 ring-black/[0.05]">
      <div className="flex flex-wrap items-center gap-2 text-[13px] text-black/50">Portfolio value <OriginBadge origin={t.origin === "demo" ? "demo" : "derived"} /></div>
      <div className="mt-0.5 text-[44px] font-semibold leading-none tracking-tight text-black/90">{sar(t.value)}</div>
      {t.change != null ? <p className="mt-2 text-[16px]"><Movement value={t.change}><b className="font-semibold">{sar(t.change, true)}</b> · {pct(t.change_pct, 2)}</Movement> <span className="text-black/50">against {sar(t.like_official)} official{t.compared_count < t.asset_count ? `, on the ${t.compared_count} of ${t.asset_count} assets that have one` : ""}</span></p> : <p className="mt-2 text-[14px] text-black/50">No official valuations recorded yet, so there is nothing to compare with.</p>}
      {notValued > 0 && <p className="mt-1 text-[12.5px] text-black/45">{t.indicative_count} of {t.asset_count} assets have a Mizan value{t.official_only_count ? `; ${t.official_only_count} use their official value` : ""}{t.unvalued_count ? `; ${t.unvalued_count} are not counted because they have no value` : ""}.</p>}
      {board.attention_count > 0 ? <button type="button" onClick={onAttention} className="mt-4 flex w-full items-center justify-between rounded-xl bg-[#FF3B30]/[0.08] px-4 py-3 text-left hover:bg-[#FF3B30]/[0.12]"><span className="text-[15px] font-semibold text-[#c4271d]">{board.attention_count} {board.attention_count === 1 ? "asset needs" : "assets need"} attention</span><ChevronRight size={18} className="text-[#c4271d]/60" /></button>
        : <p className="mt-4 rounded-xl bg-[#34C759]/10 px-4 py-3 text-[14px] text-[#1c7a3a]">Nothing needs attention right now.</p>}
      <div className="mt-4 grid grid-cols-2 gap-4 border-t border-black/[0.06] pt-4 sm:grid-cols-4">
        <Stat label="Properties" value={t.asset_count} /><Stat label="Rising" value={t.up} detail={`above +${board.settings.stable_band_pct}%`} /><Stat label="Stable" value={t.stable} /><Stat label="Falling" value={t.down} detail={t.not_comparable ? `${t.not_comparable} not comparable` : undefined} />
      </div>
    </section>
    <Card title="Value over time" action={<div className="w-[220px]"><Segmented label="Period" value={range} options={RANGES.map(r => ({ value: r.value, label: r.label }))} onChange={setRange} /></div>}
      footer="Each asset's last known value carried forward, at your ownership share. Assets join a line when their first value exists, so the official line leaves out assets without an official valuation.">
      <ValueChart points={history} label="Portfolio value over time" /></Card>
    <Card title="Fund" footer="At your ownership share. Debt is held at its recorded balance. A figure covers only the assets that have it, as shown.">
      <div className="grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-4">
        <Stat label="Indicative NAV" value={sar(t.nav)} detail={t.nav != null ? `${t.debt_count} assets with debt` : "No debt recorded"} />
        <Stat label="Official NAV" value={sar(board.official_nav_sar ?? t.official_nav)} detail={board.official_nav_sar != null ? "As entered" : t.official_nav != null ? "Official values less debt" : undefined} />
        <Stat label="Debt" value={sar(t.debt_count ? t.debt : null)} />
        <Stat label="LTV" value={pct(t.ltv_pct, 1, false)} />
        <Stat label="NOI" value={sar(t.noi_count ? t.noi : null)} detail={`${t.noi_count} of ${t.asset_count} assets`} />
        <Stat label="Implied cap rate" value={pct(t.cap_rate_pct, 2, false)} detail="NOI ÷ value" />
        <Stat label="Occupancy" value={pct(t.occupancy_pct, 1, false)} detail={`${t.occupancy_count} of ${t.asset_count} assets`} />
        <Stat label="Unrealised gain" value={sar(t.unrealised, true)} detail={t.cost_count ? `On ${sar(t.cost)} cost` : "No cost recorded"} />
      </div></Card>
    <div className="grid gap-x-5 md:grid-cols-3">
      <Card title="Confidence" footer="Share of value by evidence grade. Rule-based, not a statistical probability.">
        {confidence.length ? <ul className="m-0 list-none space-y-2 p-0 text-[14px]">{confidence.map(k => <li key={k} className="flex justify-between"><GradeLabel grade={k} /><span className="tabular-nums text-black/60">{t.confidence_share[k]!.toFixed(0)}%</span></li>)}</ul> : <p className="text-[13px] text-black/45">No Mizan values yet.</p>}</Card>
      <Card title="Sector"><ShareBars rows={t.by_type} /></Card>
      <Card title="Geography"><ShareBars rows={t.by_city} /></Card>
    </div>
    {board.alerts.length > 0 && <Card title="Latest alerts" action={<button type="button" className="text-[13px] text-[#007AFF]" onClick={onAlerts}>All {board.alerts.length}</button>}>
      <div className="-my-2.5 divide-y divide-black/[0.06]">{board.alerts.slice(0, 4).map(a => <AlertRow key={a.id} alert={a} href={a.asset_id ? `/monitor/assets/${a.asset_id}` : undefined} />)}</div></Card>}
  </>;
}

function Assets({ id, attentionOnly, clearAttention }: { id: string; attentionOnly: boolean; clearAttention: () => void }) {
  const router = useRouter();
  const [rows, setRows] = useState<AssetRow[]>([]); const [total, setTotal] = useState(0); const [facets, setFacets] = useState<{ cities: string[]; types: string[] }>({ cities: [], types: [] });
  const [q, setQ] = useState(""); const [city, setCity] = useState(""); const [type, setType] = useState(""); const [confidence, setConfidence] = useState(""); const [movement, setMovement] = useState(""); const [sort, setSort] = useState("priority"); const [view, setView] = useState<"table" | "chart">("table"); const [limit, setLimit] = useState(100);
  useEffect(() => { let on = true; listAssets(id, { q, city, property_type: type, confidence, movement, sort, attention: attentionOnly ? "true" : "", limit: String(limit) }).then(r => { if (on) { setRows(r.data); setTotal(r.total); setFacets(r.facets); } }); return () => { on = false; }; }, [id, q, city, type, confidence, movement, sort, attentionOnly, limit]);
  const points = useMemo(() => rows.filter(r => r.value != null && r.change_vs_official_pct != null).map(r => ({ id: r.id, name: r.name, x: r.value!, y: r.change_vs_official_pct!, flagged: r.confidence === "low" })), [rows]);
  const download = () => { const url = URL.createObjectURL(new Blob([assetsCsv(rows)], { type: "text/csv;charset=utf-8" })); const a = document.createElement("a"); a.href = url; a.download = "mizan-monitor-assets.csv"; a.click(); URL.revokeObjectURL(url); };
  const select = "rounded-lg border border-black/10 bg-white px-2 py-1.5 text-[13px]";
  return <>
    {attentionOnly && <div className="mb-3 flex items-center justify-between rounded-xl bg-[#FF3B30]/[0.08] px-4 py-2 text-[13.5px] text-[#c4271d]"><span>Assets with a warning or critical alert, highest priority first</span><button type="button" className="text-[#007AFF]" onClick={clearAttention}>Show all</button></div>}
    <div className="mb-3 flex flex-wrap items-center gap-2">
      <input aria-label="Search assets" value={q} onChange={e => setQ(e.target.value)} placeholder="Search" className={`${select} w-36`} />
      <select aria-label="City" className={select} value={city} onChange={e => setCity(e.target.value)}><option value="">All cities</option>{facets.cities.map(c => <option key={c}>{c}</option>)}</select>
      <select aria-label="Type" className={select} value={type} onChange={e => setType(e.target.value)}><option value="">All types</option>{facets.types.map(c => <option key={c} value={c}>{titleCase(c)}</option>)}</select>
      <select aria-label="Confidence" className={select} value={confidence} onChange={e => setConfidence(e.target.value)}><option value="">Any confidence</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
      <select aria-label="Movement" className={select} value={movement} onChange={e => setMovement(e.target.value)}><option value="">Any movement</option><option value="up">Rising</option><option value="stable">Stable</option><option value="down">Falling</option></select>
      <select aria-label="Sort" className={select} value={sort} onChange={e => setSort(e.target.value)}>{[["priority", "Sort: priority"], ["value", "Sort: value"], ["change", "Sort: biggest fall"], ["confidence", "Sort: lowest confidence"], ["ltv", "Sort: LTV"], ["occupancy", "Sort: lowest occupancy"], ["cap_rate", "Sort: cap rate"], ["age", "Sort: oldest official"], ["name", "Sort: name"]].map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
      <div className="ml-auto flex items-center gap-2"><div className="w-[130px]"><Segmented label="Asset view" value={view} options={[{ value: "table", label: "Table" }, { value: "chart", label: "Chart" }]} onChange={setView} /></div><Button onClick={download} aria-label="Download assets as CSV"><Download size={14} />CSV</Button></div>
    </div>
    {view === "chart" ? <Card footer={total > rows.length ? `Showing the first ${rows.length} of ${total} matching assets.` : undefined}><BubbleScatter points={points} onOpen={a => router.push(`/monitor/assets/${a}`)} /></Card> :
      <div className="overflow-x-auto rounded-2xl bg-white ring-1 ring-black/[0.05]"><table className="w-full min-w-[820px] text-[13.5px]">
        <thead><tr className="border-b border-black/[0.06] text-left text-[12px] text-black/45"><th className="px-4 py-2 font-medium">Asset</th><th className="px-2 py-2 text-right font-medium">Mizan value</th><th className="px-2 py-2 text-right font-medium">Official</th><th className="px-2 py-2 text-right font-medium">Change</th><th className="px-2 py-2 font-medium">Confidence</th><th className="px-2 py-2 text-right font-medium">LTV</th><th className="px-2 py-2 text-right font-medium">Occupancy</th><th className="px-3 py-2 font-medium">Why it is here</th></tr></thead>
        <tbody className="divide-y divide-black/[0.05]">{rows.map(r => <tr key={r.id} className="cursor-pointer hover:bg-black/[0.02]" onClick={() => router.push(`/monitor/assets/${r.id}`)}>
          <td className="max-w-[240px] px-4 py-2"><Link href={`/monitor/assets/${r.id}`} className="block truncate font-medium text-black/85" dir="auto" onClick={e => e.stopPropagation()}>{r.name}</Link><span className="text-[12px] text-black/45">{[r.city, titleCase(r.property_type)].filter(Boolean).join(" · ")}{r.ownership_pct !== 100 ? ` · ${r.ownership_pct}% owned` : ""}</span></td>
          <td className="px-2 py-2 text-right tabular-nums">{sar(r.value)}</td><td className="px-2 py-2 text-right tabular-nums text-black/55">{sar(r.official_value)}</td>
          <td className="px-2 py-2 text-right tabular-nums"><Movement value={r.change_vs_official_pct}>{pct(r.change_vs_official_pct)}</Movement></td>
          <td className="px-2 py-2"><GradeLabel grade={r.confidence} /></td><td className="px-2 py-2 text-right tabular-nums text-black/55">{pct(r.ltv_pct, 0, false)}</td><td className="px-2 py-2 text-right tabular-nums text-black/55">{pct(r.occupancy_pct, 0, false)}</td>
          <td className="max-w-[230px] truncate px-3 py-2 text-[12.5px] text-black/50">{r.priority.reasons[0]?.reason ?? (r.value == null ? "No Mizan value yet" : "")}</td></tr>)}
          {!rows.length && <tr><td colSpan={8} className="px-4 py-8 text-center text-black/45">No assets match.</td></tr>}</tbody></table></div>}
    <p className="mt-2 px-1 text-[12.5px] text-black/45">{rows.length} of {total} {total > rows.length && <button type="button" className="ml-2 text-[#007AFF]" onClick={() => setLimit(l => l + 200)}>Show more</button>}</p>
  </>;
}

function Alerts({ board, reload }: { board: Dashboard; reload: () => void }) {
  const update = (a: Alert, status: Alert["status"]) => setAlertStatus(a.id, status, status === "accepted" ? "Accepted from the portfolio view" : undefined).then(reload);
  if (!board.alerts.length) return <p className="rounded-2xl bg-white px-4 py-10 text-center text-[14px] text-black/45 ring-1 ring-black/[0.05]">No open alerts.</p>;
  return <>
    <div className="mb-3 flex flex-wrap gap-4 px-1">{(["critical", "warning", "watch", "info"] as const).filter(s => board.alert_counts[s]).map(s => <span key={s} className="inline-flex items-center gap-1.5 text-[13px] text-black/55"><SeverityLabel severity={s} />{board.alert_counts[s]}</span>)}</div>
    <div className="divide-y divide-black/[0.06] rounded-2xl bg-white px-4 ring-1 ring-black/[0.05]">{board.alerts.map(a => <AlertRow key={a.id} alert={a} href={a.asset_id ? `/monitor/assets/${a.asset_id}` : undefined} onStatus={s => update(a, s)} />)}</div>
    <p className="mt-2 px-1 text-[12px] text-black/45">Accepted alerts stay quiet unless they get worse. An alert closes itself once its condition no longer holds. Thresholds are in Settings.</p>
  </>;
}

function RevalueFirst({ board }: { board: Dashboard }) {
  const groups = (["high", "medium"] as const).map(band => ({ band, rows: board.priority.filter(r => r.priority.band === band) })).filter(g => g.rows.length);
  if (!groups.length) return <p className="rounded-2xl bg-white px-4 py-10 text-center text-[14px] text-black/45 ring-1 ring-black/[0.05]">No asset currently stands out for formal revaluation.</p>;
  return <>{groups.map(g => <Card key={g.band} title={`${g.band === "high" ? "High" : "Medium"} priority`}><div className="-my-2 divide-y divide-black/[0.06]">{g.rows.map(r => <Link key={r.id} href={`/monitor/assets/${r.id}`} className="block py-2.5 hover:opacity-80">
    <div className="flex items-baseline justify-between gap-3"><span className="truncate text-[14.5px] font-medium text-black/85" dir="auto">{r.name}</span><span className="whitespace-nowrap text-[12.5px] tabular-nums text-black/45">{r.priority.score} points · {sar(r.value)}</span></div>
    <ul className="m-0 mt-0.5 flex list-none flex-wrap gap-x-3 p-0 text-[12.5px] text-black/55">{r.priority.reasons.map(x => <li key={x.reason}>{x.reason}</li>)}</ul></Link>)}</div></Card>)}
    <p className="px-1 text-[12px] text-black/45">Points are a transparent ranking aid set by Mizan&apos;s rules, not a measure of risk. Each reason shows what added to the score.</p></>;
}

function Stress({ id }: { id: string }) {
  const [data, setData] = useState<StressResult | null>(null); const [open, setOpen] = useState<string | null>(null); const [error, setError] = useState("");
  useEffect(() => { getStress(id).then(setData).catch(e => setError(errorText(e))); }, [id]);
  if (error) return <p className="text-[14px] text-[#c4271d]">{error}</p>;
  if (!data) return <p className="py-10 text-center text-[14px] text-black/40">Running each asset through the engine…</p>;
  return <Card footer={data.notice}><div className="mb-3 flex gap-8"><Stat label="Today" value={sar(data.base_value)} detail={`${data.asset_count} assets`} /><Stat label="LTV today" value={pct(data.base_ltv_pct, 1, false)} /></div>
    <div className="divide-y divide-black/[0.06]">{data.scenarios.map(s => <div key={s.key} className="py-2"><button type="button" aria-expanded={open === s.key} className="grid w-full grid-cols-[1fr_auto_auto_auto] items-baseline gap-x-5 text-left text-[14px]" onClick={() => setOpen(open === s.key ? null : s.key)}>
      <span className="font-medium text-black/85">{s.label}<span className="ml-2 text-[12px] font-normal text-black/45">{s.affected} assets move</span></span><span className="tabular-nums text-black/70">{sar(s.value)}</span><span className="w-16 text-right tabular-nums"><Movement value={s.change_pct}>{pct(s.change_pct)}</Movement></span><span className="w-20 text-right tabular-nums text-black/55">LTV {pct(s.ltv_pct, 1, false)}</span></button>
      {open === s.key && <ul className="m-0 mt-2 list-none space-y-1 p-0 pl-3 text-[13px]">{s.worst.map(w => <li key={w.id} className="flex justify-between gap-3"><Link href={`/monitor/assets/${w.id}`} className="truncate text-[#007AFF]" dir="auto">{w.name}</Link><span className="whitespace-nowrap tabular-nums text-black/60">{pct(w.change_pct)}{w.ltv_after != null ? ` · LTV ${pct(w.ltv_after, 0, false)}` : ""}</span></li>)}{!s.worst.length && <li className="text-black/45">No asset uses this input.</li>}</ul>}</div>)}</div></Card>;
}

const THRESHOLDS: [string, string][] = [["stable_band_pct", "Stable within (±%)"], ["move_watch_pct", "Move: watch (%)"], ["move_warning_pct", "Move: warning (%)"], ["move_critical_pct", "Move: critical (%)"], ["divergence_watch_pct", "Method spread: watch (%)"], ["divergence_warning_pct", "Method spread: warning (%)"], ["ltv_warning_pct", "LTV: warning (%)"], ["ltv_critical_pct", "LTV: critical (%)"], ["stale_evidence_days", "Evidence stale after (days)"], ["official_age_months", "Official is old after (months)"], ["comparable_gap_pct", "New sale gap (%)"], ["concentration_watch_pct", "Concentration: watch (%)"]];

function Settings({ board, reload }: { board: Dashboard; reload: () => void }) {
  const router = useRouter();
  const [props, setProps] = useState<PropertySummary[]>([]); const [picked, setPicked] = useState<Set<string>>(new Set()); const [q, setQ] = useState(""); const [msg, setMsg] = useState(""); const [busy, setBusy] = useState(false); const [values, setValues] = useState(board.settings);
  useEffect(() => { if (!board.is_demo) listProperties(q).then(r => setProps(r.data)).catch(() => undefined); }, [q, board.is_demo]);
  const add = async () => { setBusy(true); setMsg(""); try { const r = await addAssets(board.id, Array.from(picked)); setMsg(`Added ${r.added}.`); setPicked(new Set()); reload(); } catch (e) { setMsg(errorText(e)); } setBusy(false); };
  const save = async () => { setMsg(""); try { await patchPortfolio(board.id, { settings: values }); setMsg("Thresholds saved."); reload(); } catch (e) { setMsg(errorText(e)); } };
  const drop = async () => { if (!window.confirm("Delete this portfolio? Its properties and valuation history are kept.")) return; await deletePortfolio(board.id); router.push("/monitor"); };
  return <>
    {msg && <p className="mb-3 rounded-xl bg-[#007AFF]/10 px-4 py-2 text-[13px] text-[#0058b8]">{msg}</p>}
    {!board.is_demo && <Card title="Add properties" footer="Monitor values an asset from the inputs you reviewed in its valuation. A property without complete inputs joins with no Mizan value until they are saved.">
      <input aria-label="Search properties" value={q} onChange={e => setQ(e.target.value)} placeholder="Search your properties" className={`${inputClass} mb-2`} />
      <div className="max-h-64 divide-y divide-black/[0.05] overflow-y-auto">{props.map(p => <label key={p.id} className="flex cursor-pointer items-center gap-2.5 py-2 text-[14px]"><input type="checkbox" checked={picked.has(p.id)} onChange={e => setPicked(s => { const n = new Set(s); if (e.target.checked) n.add(p.id); else n.delete(p.id); return n; })} /><span className="truncate" dir="auto">{p.name}</span><span className="ml-auto whitespace-nowrap text-[12px] text-black/40">{titleCase(p.property_type)}</span></label>)}{!props.length && <p className="py-4 text-center text-[13px] text-black/45">No properties found.</p>}</div>
      <div className="mt-3"><Button tone="primary" disabled={!picked.size || busy} onClick={add}>Add {picked.size || ""}</Button></div></Card>}
    <Card title="Alert thresholds" footer="These are this portfolio's settings, not market benchmarks. Changing them re-evaluates alerts straight away.">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{THRESHOLDS.map(([k, l]) => <Field key={k} label={l}><input type="number" min={0} className={inputClass} value={values[k] ?? ""} onChange={e => setValues(v => ({ ...v, [k]: Number(e.target.value) }))} /></Field>)}</div>
      <div className="mt-3"><Button tone="primary" onClick={save}>Save thresholds</Button></div></Card>
    {!board.is_demo && <Button tone="danger" onClick={drop}>Delete portfolio</Button>}
  </>;
}

export default function Page() { return <Suspense fallback={<p className="py-16 text-center text-[14px] text-black/40">Loading…</p>}><PortfolioPage /></Suspense>; }
