"use client";
// Dependency-free SVG charts. One axis, thin marks, recessive grid, hover readout; the Assets table is the table view.
import { useMemo, useRef, useState } from "react";
import { pct, sar } from "@/lib/monitor";

const BLUE = "#007AFF"; const INK = "#5B5B60";
type Point = { date: string; indicative: number | null; official: number | null; low?: number | null; high?: number | null };
const day = (d: string) => Date.parse(`${d}T00:00:00Z`);
function niceTicks(min: number, max: number, count = 4) {
  const span = max - min || Math.abs(max) || 1; const raw = span / count; const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) ?? raw;
  const out: number[] = []; for (let v = Math.floor(min / step) * step; v <= max + step * .5; v += step) out.push(v);
  return out;
}
const short = (iso: string) => new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", { month: "short", year: "2-digit", timeZone: "UTC" });

/** Value through time. Mizan is the line; official valuations are stepped, dashed and dotted so they read differently without colour. */
export function ValueChart({ points, height = 230, label }: { points: Point[]; height?: number; label: string }) {
  const [hover, setHover] = useState<number | null>(null); const ref = useRef<SVGSVGElement>(null);
  const W = 720, L = 64, R = 14, T = 12, B = 26;
  const chart = useMemo(() => {
    const values = points.flatMap(p => [p.indicative, p.official, p.low, p.high]).filter((v): v is number => v != null);
    if (points.length < 2 || !values.length) return null;
    const pad = (Math.max(...values) - Math.min(...values)) * .12 || Math.max(...values) * .05 || 1;
    const ticks = niceTicks(Math.min(...values) - pad, Math.max(...values) + pad);
    const y0 = ticks[0], y1 = ticks[ticks.length - 1], t0 = day(points[0].date), t1 = day(points[points.length - 1].date);
    const x = (d: string) => L + (day(d) - t0) / (t1 - t0 || 1) * (W - L - R);
    const y = (v: number) => T + (1 - (v - y0) / (y1 - y0 || 1)) * (height - T - B);
    const line = (key: "indicative" | "official") => points.filter(p => p[key] != null).map((p, i) => `${i ? "L" : "M"}${x(p.date).toFixed(1)} ${y(p[key]!).toFixed(1)}`).join(" ");
    const banded = points.filter(p => p.low != null && p.high != null);
    const band = banded.length > 1 ? `${banded.map((p, i) => `${i ? "L" : "M"}${x(p.date).toFixed(1)} ${y(p.high!).toFixed(1)}`).join(" ")} ${[...banded].reverse().map(p => `L${x(p.date).toFixed(1)} ${y(p.low!).toFixed(1)}`).join(" ")} Z` : null;
    const labels = points.length <= 6 ? points : Array.from({ length: 6 }, (_, i) => points[Math.round(i * (points.length - 1) / 5)]);
    return { ticks, x, y, indicative: line("indicative"), official: line("official"), band, labels };
  }, [points, height]);
  if (!chart) return <p className="py-10 text-center text-[13px] text-black/45">Not enough history in this period to draw a chart.</p>;
  const hasOfficial = points.some(p => p.official != null);
  const point = hover != null ? points[hover] : null;
  const move = (e: React.MouseEvent<SVGSVGElement>) => { const box = ref.current!.getBoundingClientRect(); const px = (e.clientX - box.left) / box.width * W;
    let best = 0, gap = Infinity; points.forEach((p, i) => { const g = Math.abs(chart.x(p.date) - px); if (g < gap) { gap = g; best = i; } }); setHover(best); };
  return <figure className="m-0">
    <div className="mb-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-black/55">
      <span className="inline-flex items-center gap-1.5"><svg width="18" height="4" aria-hidden><line x1="0" x2="18" y1="2" y2="2" stroke={BLUE} strokeWidth="2" /></svg>Mizan indicative</span>
      {hasOfficial && <span className="inline-flex items-center gap-1.5"><svg width="18" height="4" aria-hidden><line x1="0" x2="18" y1="2" y2="2" stroke={INK} strokeWidth="2" strokeDasharray="4 3" /></svg>Official</span>}
      {chart.band && <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-4 rounded-sm" style={{ background: "rgba(0,122,255,.13)" }} />Range</span>}
    </div>
    <svg ref={ref} viewBox={`0 0 ${W} ${height}`} className="block w-full touch-none" role="img" aria-label={label} onMouseMove={move} onMouseLeave={() => setHover(null)}>
      {chart.ticks.map(t => <g key={t}><line x1={L} x2={W - R} y1={chart.y(t)} y2={chart.y(t)} stroke="rgba(0,0,0,.06)" /><text x={L - 8} y={chart.y(t) + 4} textAnchor="end" fontSize="11" fill="rgba(0,0,0,.45)">{sar(t).replace("SAR ", "")}</text></g>)}
      {chart.labels.map((p, i) => <text key={p.date} x={chart.x(p.date)} y={height - 7} textAnchor={i === chart.labels.length - 1 ? "end" : "middle"} fontSize="11" fill="rgba(0,0,0,.45)">{short(p.date)}</text>)}
      {chart.band && <path d={chart.band} fill="rgba(0,122,255,.13)" />}
      {hasOfficial && <path d={chart.official} fill="none" stroke={INK} strokeWidth="2" strokeDasharray="4 3" />}
      <path d={chart.indicative} fill="none" stroke={BLUE} strokeWidth="2" strokeLinejoin="round" />
      {point && <g><line x1={chart.x(point.date)} x2={chart.x(point.date)} y1={T} y2={height - B} stroke="rgba(0,0,0,.25)" />
        {point.indicative != null && <circle cx={chart.x(point.date)} cy={chart.y(point.indicative)} r="4" fill={BLUE} stroke="#fff" strokeWidth="2" />}
        {point.official != null && <circle cx={chart.x(point.date)} cy={chart.y(point.official)} r="4" fill={INK} stroke="#fff" strokeWidth="2" />}</g>}
    </svg>
    <figcaption className="h-5 text-[12.5px] text-black/60">{point ? <>{point.date} · Mizan {sar(point.indicative)}{hasOfficial ? ` · Official ${sar(point.official)}` : ""}{point.low != null ? ` · Range ${sar(point.low)} to ${sar(point.high)}` : ""}</> : <span className="text-black/35">Hover for values</span>}</figcaption>
  </figure>;
}

/** Each driver of a value change as one signed bar from a shared zero. Labels carry the sign, so colour is not alone. */
export function DriverBars({ drivers }: { drivers: { key: string; label: string; amount: number; pct: number | null }[] }) {
  const max = Math.max(...drivers.map(d => Math.abs(d.amount)), 1);
  return <ul className="m-0 list-none space-y-2 p-0">{drivers.map(d => <li key={d.key} className="grid grid-cols-[minmax(110px,170px)_1fr_auto] items-center gap-3 text-[13.5px]">
    <span className="truncate text-black/70">{d.label}</span>
    <span className="relative block h-3"><span className="absolute inset-y-0 left-1/2 w-px bg-black/15" />
      <span className="absolute inset-y-[1px] rounded" style={{ width: `${Math.abs(d.amount) / max * 50}%`, background: d.amount >= 0 ? "#34C759" : "#FF3B30", ...(d.amount >= 0 ? { left: "50%" } : { right: "50%" }) }} /></span>
    <span className="whitespace-nowrap text-right tabular-nums text-black/80">{d.pct != null ? pct(d.pct) : ""}<span className="ml-2 text-black/45">{sar(d.amount, true)}</span></span>
  </li>)}</ul>;
}

export type ScatterPoint = { id: string; name: string; x: number; y: number; flagged: boolean };
/** Value against change since official, so an outlier stands out. Filled dots are low confidence. */
export function BubbleScatter({ points, onOpen }: { points: ScatterPoint[]; onOpen: (id: string) => void }) {
  const [hover, setHover] = useState<ScatterPoint | null>(null);
  const W = 720, H = 300, L = 48, R = 14, T = 12, B = 34;
  if (!points.length) return <p className="py-10 text-center text-[13px] text-black/45">No assets have both a Mizan value and an official valuation.</p>;
  const xs = points.map(p => p.x), ys = points.map(p => p.y);
  const xMax = Math.max(...xs) * 1.06, yTicks = niceTicks(Math.min(0, ...ys) - 1, Math.max(0, ...ys) + 1, 5), xTicks = niceTicks(0, xMax, 5).filter(t => t <= xMax);
  const x = (v: number) => L + v / xMax * (W - L - R), y = (v: number) => T + (1 - (v - yTicks[0]) / (yTicks[yTicks.length - 1] - yTicks[0])) * (H - T - B);
  const r = (v: number) => 3.5 + Math.sqrt(v / Math.max(...xs)) * 12;
  return <figure className="m-0">
    <div className="mb-1 flex flex-wrap gap-x-4 text-[12px] text-black/55"><span className="inline-flex items-center gap-1.5"><svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill="rgba(0,122,255,.25)" stroke={BLUE} /></svg>Asset (size = value)</span><span className="inline-flex items-center gap-1.5"><svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill={BLUE} /></svg>Low confidence</span></div>
    <svg viewBox={`0 0 ${W} ${H}`} className="block w-full" role="img" aria-label="Assets by value and change since official valuation">
      {yTicks.map(t => <g key={t}><line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke={t === 0 ? "rgba(0,0,0,.3)" : "rgba(0,0,0,.06)"} /><text x={L - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="rgba(0,0,0,.45)">{pct(t, 0)}</text></g>)}
      {xTicks.map(t => <text key={t} x={x(t)} y={H - 16} textAnchor="middle" fontSize="11" fill="rgba(0,0,0,.45)">{sar(t).replace("SAR ", "")}</text>)}
      <text x={(W + L) / 2} y={H - 2} textAnchor="middle" fontSize="11" fill="rgba(0,0,0,.45)">Indicative value (SAR)</text>
      {[...points].sort((a, b) => b.x - a.x).map(p => <circle key={p.id} cx={x(p.x)} cy={y(p.y)} r={r(p.x)} fill={p.flagged ? BLUE : "rgba(0,122,255,.25)"} stroke={p.flagged ? "#fff" : BLUE} strokeWidth={p.flagged ? 1.5 : 1} className="cursor-pointer"
        tabIndex={0} role="link" aria-label={`${p.name}: ${pct(p.y)}`} onMouseEnter={() => setHover(p)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(p)} onClick={() => onOpen(p.id)} onKeyDown={e => { if (e.key === "Enter") onOpen(p.id); }} />)}
    </svg>
    <figcaption className="h-5 truncate text-[12.5px] text-black/60" dir="auto">{hover ? `${hover.name} · ${sar(hover.x)} · ${pct(hover.y)} against official` : <span className="text-black/35">Hover an asset; click to open it</span>}</figcaption>
  </figure>;
}

export function ShareBars({ rows }: { rows: { key: string; label: string; share_pct: number; value: number }[] }) {
  return <ul className="m-0 list-none space-y-2 p-0">{rows.slice(0, 6).map(r => <li key={r.key} className="text-[13.5px]">
    <div className="flex justify-between gap-3"><span className="truncate text-black/70">{r.label}</span><span className="tabular-nums text-black/55">{r.share_pct.toFixed(0)}%</span></div>
    <div className="mt-1 h-1.5 rounded-full bg-black/[0.06]"><div className="h-full rounded-full bg-[#007AFF]" style={{ width: `${r.share_pct}%` }} /></div>
  </li>)}</ul>;
}
