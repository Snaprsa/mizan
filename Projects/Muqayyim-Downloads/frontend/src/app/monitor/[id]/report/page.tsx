"use client";
// A printable portfolio monitor report: what changed, how much, why, which assets, how sure, what to do.
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ChevronLeft, Printer } from "lucide-react";
import { errorText, getAsset, getDashboard, listAssets, pct, sar, type AssetDetail, type AssetRow, type Dashboard } from "@/lib/monitor";
import { Button, DemoBanner, GradeLabel } from "@/components/monitor/ui";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [board, setBoard] = useState<Dashboard | null>(null); const [rows, setRows] = useState<AssetRow[]>([]); const [detail, setDetail] = useState<AssetDetail[]>([]); const [error, setError] = useState("");
  useEffect(() => { (async () => { try {
    const [b, assets] = await Promise.all([getDashboard(id), listAssets(id, { sort: "change", limit: "5000" })]); setBoard(b); setRows(assets.data);
    setDetail(await Promise.all(b.priority.slice(0, 5).map(a => getAsset(a.id))));
  } catch (e) { setError(errorText(e)); } })(); }, [id]);
  if (error) return <p className="text-[14px] text-[#c4271d]">{error}</p>;
  if (!board) return <p className="py-16 text-center text-[14px] text-black/40">Preparing the report…</p>;
  const t = board.totals;
  const moves = rows.filter(r => r.change_vs_official_pct != null && Math.abs(r.change_vs_official_pct) >= board.settings.move_watch_pct);
  const low = rows.filter(r => r.confidence === "low");
  return <div className="report text-[14px] text-black/80">
    <div className="mb-4 flex items-center justify-between print:hidden"><Link href={`/monitor/${id}`} className="-ml-1.5 inline-flex items-center text-[14px] text-[#007AFF]"><ChevronLeft size={18} />Back</Link><Button tone="primary" onClick={() => window.print()}><Printer size={14} />Print or save as PDF</Button></div>
    <h1 className="text-[26px] font-semibold tracking-tight" dir="auto">Portfolio Valuation Monitor</h1>
    <p className="mb-4 text-black/50" dir="auto">{board.name} · as of {board.as_of}</p>
    {board.is_demo && <DemoBanner />}
    <h2 className="mt-5 mb-1.5 text-[17px] font-semibold">Summary</h2>
    <p>Indicative portfolio value is <b>{sar(t.value)}</b> across {t.asset_count} assets{t.change != null ? <>, <b>{sar(t.change, true)} ({pct(t.change_pct, 2)})</b> against official valuations on the assets that have both</> : ""}. {t.up} are rising, {t.stable} stable and {t.down} falling. {board.attention_count} need attention.</p>
    {t.nav != null && <p className="mt-1">Indicative NAV is {sar(t.nav)} after {sar(t.debt)} of attributable debt, an LTV of {pct(t.ltv_pct, 1, false)}.</p>}
    <p className="mt-1">By value, {Object.entries(t.confidence_share).map(([k, v]) => `${v!.toFixed(0)}% is ${k} confidence`).join(", ") || "no asset has a confidence grade yet"}.</p>
    <h2 className="mt-5 mb-1.5 text-[17px] font-semibold">Material valuation movements</h2>
    {moves.length ? <table className="w-full text-[13px]"><thead><tr className="border-b text-left text-black/50"><th className="py-1 font-medium">Asset</th><th className="text-right font-medium">Official</th><th className="text-right font-medium">Mizan</th><th className="text-right font-medium">Change</th><th className="pl-3 font-medium">Confidence</th></tr></thead><tbody>{moves.map(r => <tr key={r.id} className="border-b border-black/[0.05]"><td className="py-1" dir="auto">{r.name}</td><td className="text-right tabular-nums">{sar(r.official_value)}</td><td className="text-right tabular-nums">{sar(r.value)}</td><td className="text-right tabular-nums">{pct(r.change_vs_official_pct)}</td><td className="pl-3"><GradeLabel grade={r.confidence} /></td></tr>)}</tbody></table> : <p>No asset has moved past the {board.settings.move_watch_pct}% threshold.</p>}
    <h2 className="mt-5 mb-1.5 text-[17px] font-semibold">Assets to revalue first, and why</h2>
    {detail.length ? detail.map(a => { const why = a.attribution_since_official ?? a.attribution; return <div key={a.id} className="mb-3 break-inside-avoid">
      <div className="font-medium" dir="auto">{a.name} · {sar(a.value)}{a.change_vs_official_pct != null ? ` (${pct(a.change_vs_official_pct)} vs official)` : ""}</div>
      <div className="text-[13px] text-black/60">{a.priority.reasons.map(r => r.reason).join("; ")}.</div>
      {why?.drivers?.length ? <div className="text-[13px] text-black/60">Drivers: {why.drivers.slice(0, 4).map(d => `${d.label} ${sar(d.amount, true)}`).join("; ")}.</div> : null}
      {a.evidence.some(c => c.is_new) && <div className="text-[13px] text-black/60">{a.evidence.filter(c => c.is_new).length} new comparable sales since the official valuation.</div>}
      <div className="text-[13px] text-black/60">Recommended action: {a.priority.band === "high" ? "commission a formal valuation" : "review the evidence before the next scheduled valuation"}.</div></div>; }) : <p>No asset currently stands out.</p>}
    <h2 className="mt-5 mb-1.5 text-[17px] font-semibold">Low-confidence values</h2>
    {low.length ? <ul className="list-disc pl-5 text-[13px]">{low.map(r => <li key={r.id} dir="auto">{r.name}: {sar(r.value)}</li>)}</ul> : <p>None.</p>}
    <h2 className="mt-5 mb-1.5 text-[17px] font-semibold">Basis and limits</h2>
    <p className="text-[12.5px] leading-relaxed text-black/55">Indicative values are calculated by Mizan from saved inputs and recorded evidence. They are not formal valuations and have not been established as compliant with TAQEEM, IVS or IFRS requirements. Confidence is a rule-based grade of the evidence, not a calibrated probability. Ranges come from the spread between methods and sales and are not confidence intervals. Priority points are a ranking aid.</p>
  </div>;
}
