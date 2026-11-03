"use client";
// Monitor's small shared pieces. Provenance is always a word on screen, never only a colour.
import { AlertOctagon, AlertTriangle, Eye, Info } from "lucide-react";
import type { ReactNode } from "react";
import type { Alert, Grade, Origin, Severity } from "@/lib/monitor";

// Outlined labels; demo is dashed amber so it can never be mistaken for evidence.
const QUIET = "border border-[rgba(60,60,67,0.34)] text-[#5F5F64]";
const ORIGIN: Record<string, { label: string; className: string; title: string }> = {
  demo: { label: "DEMO DATA", className: "border border-dashed border-[#8A5200] bg-[rgba(255,159,10,0.16)] text-[#8A5200]", title: "Synthetic. Not market data." },
  real: { label: "REAL DATA", className: QUIET, title: "From a recorded source." },
  user_provided: { label: "USER PROVIDED", className: QUIET, title: "Entered by a user." },
  derived: { label: "DERIVED", className: QUIET, title: "Calculated by Mizan from saved inputs and evidence." },
  detected: { label: "DETECTED", className: QUIET, title: "Found by comparing evidence with the last valuation." },
  estimated: { label: "ESTIMATED", className: QUIET, title: "An estimate, not an observation." },
};
export function OriginBadge({ origin }: { origin: Origin | "estimated" }) {
  const o = origin ? ORIGIN[origin] : null;
  if (!o) return null;
  return <span title={o.title} className={`inline-flex h-5 items-center whitespace-nowrap rounded-[6px] px-[7px] text-[10.5px] font-semibold tracking-[0.05em] ${o.className}`}>{o.label}</span>;
}

export function DemoBanner() {
  return <div className="mb-5 rounded-xl border border-dashed border-[#8A5200]/60 bg-[rgba(255,159,10,0.12)] px-4 py-2.5 text-[13px] text-[#8A5200]"><b>Demo data.</b> This fund, its properties, sales and official valuations are made up. The calculations are real, the inputs are not, so nothing here describes the Saudi market.</div>;
}

// The word carries the grade; the bars repeat it as a level, so it never depends on colour.
const GRADE: Record<Grade, { label: string; level: number }> = { high: { label: "High", level: 3 }, medium: { label: "Medium", level: 2 }, low: { label: "Low", level: 1 } };
export function GradeLabel({ grade }: { grade: Grade | null | undefined }) {
  if (!grade) return <span className="text-black/35">—</span>;
  return <span className="inline-flex items-center gap-2 whitespace-nowrap font-semibold">{GRADE[grade].label}
    <span className="inline-flex gap-[3px]" aria-hidden>{[1, 2, 3].map(i => <i key={i} className={`h-1.5 w-3.5 rounded-[3px] ${i <= GRADE[grade].level ? "bg-[#1D1D1F]" : "bg-[rgba(60,60,67,0.34)]"}`} />)}</span></span>;
}

const SEVERITY: Record<Severity, { label: string; className: string; Icon: typeof Info }> = {
  critical: { label: "Critical", className: "border-2 border-[#C0271B] bg-[rgba(255,59,48,0.10)] text-[#C0271B]", Icon: AlertOctagon },
  warning: { label: "Warning", className: "border border-[#8A5200] bg-[rgba(255,159,10,0.16)] text-[#8A5200]", Icon: AlertTriangle },
  watch: { label: "Watch", className: "border border-transparent bg-[rgba(120,120,128,0.12)] text-[#1D1D1F]", Icon: Eye },
  info: { label: "Info", className: "border border-transparent bg-[rgba(0,113,227,0.10)] text-[#0062C4]", Icon: Info } };
export function SeverityLabel({ severity }: { severity: Severity }) {
  const { label, className, Icon } = SEVERITY[severity];
  return <span className={`inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-[8px] px-2.5 text-[13px] font-semibold ${className}`}><Icon size={14} aria-hidden />{label}</span>;
}

export function Card({ title, footer, action, children, className = "" }: { title?: string; footer?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`mb-5 ${className}`}>
    {(title || action) && <div className="mb-1.5 flex items-end justify-between gap-3 px-1">{title && <h2 className="text-[13px] font-medium uppercase tracking-wide text-black/45">{title}</h2>}{action}</div>}
    <div className="rounded-[20px] bg-white p-5">{children}</div>
    {footer && <p className="px-1 pt-1.5 text-[12px] leading-snug text-black/45">{footer}</p>}
  </section>;
}

export function Stat({ label, value, detail }: { label: string; value: ReactNode; detail?: ReactNode }) {
  return <div className="min-w-0"><div className="text-[12.5px] text-black/45">{label}</div><div className="truncate text-[19px] font-semibold tracking-tight text-black/85">{value}</div>{detail && <div className="text-[12px] text-black/45">{detail}</div>}</div>;
}

export const Movement = ({ value, children }: { value: number | null | undefined; children: ReactNode }) =>
  <span style={{ color: value == null || value === 0 ? undefined : value > 0 ? "#17722F" : "#C0271B" }}>{children}</span>;

export function Button({ children, tone = "plain", className = "", ...rest }: { tone?: "primary" | "plain" | "danger" } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const tones = { primary: "bg-[#0071E3] text-white hover:bg-[#0062C4]", plain: "bg-black/[0.06] text-black/80 hover:bg-black/[0.09]", danger: "bg-transparent text-[#FF3B30] hover:bg-[#FF3B30]/10" };
  return <button type="button" className={`inline-flex items-center justify-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13.5px] font-medium disabled:opacity-40 ${tones[tone]} ${className}`} {...rest}>{children}</button>;
}

export const inputClass = "w-full rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[14px] outline-none focus:border-[#0071E3]";
export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block text-[12.5px] text-black/55"><span className="mb-1 block">{label}</span>{children}</label>;
}

export function AlertRow({ alert, href, onStatus }: { alert: Alert; href?: string; onStatus?: (status: Alert["status"]) => void }) {
  return <div className="flex flex-wrap items-start gap-x-3 gap-y-1 py-2.5">
    <div className="w-[96px] shrink-0"><SeverityLabel severity={alert.severity} /></div>
    <div className="min-w-[200px] flex-1">
      <div className="text-[14px] font-medium text-black/85" dir="auto">{href ? <a className="hover:underline" href={href}>{alert.title}</a> : alert.title}</div>
      <div className="text-[13px] leading-snug text-black/55" dir="auto">{alert.message}</div>
      {alert.status === "investigating" && <div className="mt-0.5 text-[12px] font-medium text-[#0062C4]">Being investigated</div>}
      {alert.status === "accepted" && <div className="mt-0.5 text-[12px] text-black/45">Accepted{alert.note ? `: ${alert.note}` : ""}</div>}
    </div>
    {onStatus && alert.status !== "resolved" && <div className="flex gap-1.5">
      {alert.status !== "accepted" && <Button onClick={() => onStatus("accepted")}>Accept</Button>}
      {alert.status === "open" && <Button onClick={() => onStatus("investigating")}>Investigate</Button>}
      {alert.status !== "open" && <Button onClick={() => onStatus("open")}>Reopen</Button>}
    </div>}
  </div>;
}
