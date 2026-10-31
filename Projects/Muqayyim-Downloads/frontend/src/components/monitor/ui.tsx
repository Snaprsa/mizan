"use client";
// Monitor's small shared pieces. Provenance is always a word on screen, never only a colour.
import { AlertOctagon, AlertTriangle, Eye, Info } from "lucide-react";
import type { ReactNode } from "react";
import type { Alert, Grade, Origin, Severity } from "@/lib/monitor";

const ORIGIN: Record<string, { label: string; className: string; title: string }> = {
  demo: { label: "DEMO DATA", className: "bg-[#FF9500]/15 text-[#a85f00]", title: "Synthetic. Not market data." },
  real: { label: "REAL DATA", className: "bg-[#34C759]/15 text-[#1c7a3a]", title: "From a recorded source." },
  user_provided: { label: "USER PROVIDED", className: "bg-black/[0.06] text-black/60", title: "Entered by a user." },
  derived: { label: "DERIVED", className: "bg-[#007AFF]/10 text-[#0058b8]", title: "Calculated by Mizan from saved inputs and evidence." },
  detected: { label: "DETECTED", className: "bg-[#007AFF]/10 text-[#0058b8]", title: "Found by comparing evidence with the last valuation." },
  estimated: { label: "ESTIMATED", className: "bg-black/[0.06] text-black/60", title: "An estimate, not an observation." },
};
export function OriginBadge({ origin }: { origin: Origin | "estimated" }) {
  const o = origin ? ORIGIN[origin] : null;
  if (!o) return null;
  return <span title={o.title} className={`inline-block whitespace-nowrap rounded px-1.5 py-[1px] text-[10.5px] font-semibold tracking-wide ${o.className}`}>{o.label}</span>;
}

export function DemoBanner() {
  return <div className="mb-5 rounded-xl bg-[#FF9500]/12 px-4 py-2.5 text-[13px] text-[#8a4e00]"><b>Demo data.</b> This fund, its properties, sales and official valuations are made up. The calculations are real, the inputs are not, so nothing here describes the Saudi market.</div>;
}

const GRADE: Record<Grade, { label: string; dot: string }> = { high: { label: "High", dot: "#34C759" }, medium: { label: "Medium", dot: "#FF9500" }, low: { label: "Low", dot: "#FF3B30" } };
export function GradeLabel({ grade }: { grade: Grade | null | undefined }) {
  if (!grade) return <span className="text-black/35">—</span>;
  return <span className="inline-flex items-center gap-1.5 whitespace-nowrap"><span className="h-2 w-2 rounded-full" style={{ background: GRADE[grade].dot }} />{GRADE[grade].label}</span>;
}

const SEVERITY: Record<Severity, { label: string; color: string; Icon: typeof Info }> = {
  critical: { label: "Critical", color: "#D70015", Icon: AlertOctagon }, warning: { label: "Warning", color: "#C93400", Icon: AlertTriangle },
  watch: { label: "Watch", color: "#8a6d00", Icon: Eye }, info: { label: "Info", color: "#6e6e73", Icon: Info } };
export function SeverityLabel({ severity }: { severity: Severity }) {
  const { label, color, Icon } = SEVERITY[severity];
  return <span className="inline-flex items-center gap-1 whitespace-nowrap text-[12px] font-medium" style={{ color }}><Icon size={13} aria-hidden />{label}</span>;
}

export function Card({ title, footer, action, children, className = "" }: { title?: string; footer?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`mb-5 ${className}`}>
    {(title || action) && <div className="mb-1.5 flex items-end justify-between gap-3 px-1">{title && <h2 className="text-[13px] font-medium uppercase tracking-wide text-black/45">{title}</h2>}{action}</div>}
    <div className="rounded-2xl bg-white p-4 ring-1 ring-black/[0.05]">{children}</div>
    {footer && <p className="px-1 pt-1.5 text-[12px] leading-snug text-black/45">{footer}</p>}
  </section>;
}

export function Stat({ label, value, detail }: { label: string; value: ReactNode; detail?: ReactNode }) {
  return <div className="min-w-0"><div className="text-[12.5px] text-black/45">{label}</div><div className="truncate text-[19px] font-semibold tracking-tight text-black/85">{value}</div>{detail && <div className="text-[12px] text-black/45">{detail}</div>}</div>;
}

export const Movement = ({ value, children }: { value: number | null | undefined; children: ReactNode }) =>
  <span style={{ color: value == null || value === 0 ? undefined : value > 0 ? "#1c7a3a" : "#c4271d" }}>{children}</span>;

export function Button({ children, tone = "plain", className = "", ...rest }: { tone?: "primary" | "plain" | "danger" } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const tones = { primary: "bg-[#007AFF] text-white hover:bg-[#0068d9]", plain: "bg-black/[0.06] text-black/80 hover:bg-black/[0.09]", danger: "bg-transparent text-[#FF3B30] hover:bg-[#FF3B30]/10" };
  return <button type="button" className={`inline-flex items-center justify-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13.5px] font-medium disabled:opacity-40 ${tones[tone]} ${className}`} {...rest}>{children}</button>;
}

export const inputClass = "w-full rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[14px] outline-none focus:border-[#007AFF]";
export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block text-[12.5px] text-black/55"><span className="mb-1 block">{label}</span>{children}</label>;
}

export function AlertRow({ alert, href, onStatus }: { alert: Alert; href?: string; onStatus?: (status: Alert["status"]) => void }) {
  return <div className="flex flex-wrap items-start gap-x-3 gap-y-1 py-2.5">
    <div className="w-[76px] shrink-0 pt-0.5"><SeverityLabel severity={alert.severity} /></div>
    <div className="min-w-[200px] flex-1">
      <div className="text-[14px] font-medium text-black/85" dir="auto">{href ? <a className="hover:underline" href={href}>{alert.title}</a> : alert.title}</div>
      <div className="text-[13px] leading-snug text-black/55" dir="auto">{alert.message}</div>
      {alert.status === "investigating" && <div className="mt-0.5 text-[12px] font-medium text-[#0058b8]">Being investigated</div>}
      {alert.status === "accepted" && <div className="mt-0.5 text-[12px] text-black/45">Accepted{alert.note ? `: ${alert.note}` : ""}</div>}
    </div>
    {onStatus && alert.status !== "resolved" && <div className="flex gap-1.5">
      {alert.status !== "accepted" && <Button onClick={() => onStatus("accepted")}>Accept</Button>}
      {alert.status === "open" && <Button onClick={() => onStatus("investigating")}>Investigate</Button>}
      {alert.status !== "open" && <Button onClick={() => onStatus("open")}>Reopen</Button>}
    </div>}
  </div>;
}
