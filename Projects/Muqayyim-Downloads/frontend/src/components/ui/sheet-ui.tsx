"use client";
// Small, quiet UI primitives in the spirit of Apple's Human Interface Guidelines:
// grouped lists, switches, segmented controls and translucent surfaces.
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

export function Glass({ className = "", children, ...rest }: { className?: string; children: ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`mizan-card ${className}`} {...rest}>{children}</div>;
}

export function SheetHeader({ title, subtitle, onBack, backLabel = "Back", trailing }: { title: string; subtitle?: string; onBack?: () => void; backLabel?: string; trailing?: ReactNode }) {
  return <div className="px-4 pt-3 pb-2">
    {onBack && <button type="button" onClick={onBack} className="-ml-1.5 mb-1 inline-flex items-center text-[15px] text-[#0071E3] active:opacity-60"><ChevronLeft size={20} strokeWidth={2.2} />{backLabel}</button>}
    <div className="flex items-start gap-2"><div className="min-w-0 flex-1">
      <h2 className="text-[22px] font-semibold tracking-tight leading-tight text-black/90" dir="auto">{title}</h2>
      {subtitle && <p className="text-[13px] text-black/50 mt-0.5" dir="auto">{subtitle}</p>}</div>{trailing}</div>
  </div>;
}

export function Section({ title, footer, children, className = "" }: { title?: string; footer?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`px-4 py-2 ${className}`}>
    {title && <h3 className="px-1 pb-1.5 text-[13px] font-medium text-black/45 uppercase tracking-wide">{title}</h3>}
    <div className="rounded-xl bg-white overflow-hidden ring-1 ring-black/[0.05] divide-y divide-black/[0.06]">{children}</div>
    {footer && <div className="px-1 pt-1.5 text-[12px] leading-snug text-black/45">{footer}</div>}
  </section>;
}

export function Row({ label, detail, value, onClick, chevron, leading, destructive, children, ariaLabel }: {
  label: ReactNode; detail?: ReactNode; value?: ReactNode; onClick?: () => void; chevron?: boolean; leading?: ReactNode; destructive?: boolean; children?: ReactNode; ariaLabel?: string }) {
  const body = <><span className="flex items-center gap-3 min-w-0 flex-1">{leading}
      <span className="min-w-0 flex-1"><span className={`block text-[15px] leading-snug truncate ${destructive ? "text-[#FF3B30]" : "text-black/85"}`} dir="auto">{label}</span>
        {detail && <span className="block text-[12.5px] text-black/45 truncate" dir="auto">{detail}</span>}</span></span>
    {value != null && <span className="text-[15px] text-black/45 whitespace-nowrap">{value}</span>}{children}
    {chevron && <ChevronRight size={16} className="text-black/25 shrink-0" />}</>;
  const cls = "w-full min-h-[44px] flex items-center gap-2 px-3.5 py-2 text-left";
  return onClick ? <button type="button" aria-label={ariaLabel} onClick={onClick} className={`${cls} hover:bg-black/[0.03] active:bg-black/[0.06]`}>{body}</button> : <div className={cls}>{body}</div>;
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return <button type="button" role="switch" aria-checked={checked} aria-label={label} onClick={() => onChange(!checked)}
    className={`relative h-[26px] w-[44px] shrink-0 rounded-full transition-colors ${checked ? "bg-[#34C759]" : "bg-black/15"} focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#0071E3]`}>
    <span className={`absolute top-[2px] h-[22px] w-[22px] rounded-full bg-white shadow transition-[left] ${checked ? "left-[20px]" : "left-[2px]"}`} />
  </button>;
}

export function Segmented<T extends string>({ value, options, onChange, label }: { value: T; options: { value: T; label: string; disabled?: boolean }[]; onChange: (v: T) => void; label: string }) {
  return <div role="radiogroup" aria-label={label} className="flex gap-[2px] rounded-[10px] bg-[rgba(120,120,128,0.12)] p-[2px]">
    {options.map(o => <button key={o.value} type="button" role="radio" aria-checked={value === o.value} disabled={o.disabled} onClick={() => onChange(o.value)}
      className={`h-9 flex-1 whitespace-nowrap rounded-[8px] px-2 text-[13px] transition ${value === o.value ? "bg-white font-semibold text-[#1D1D1F] shadow-[0_1px_3px_rgba(0,0,0,0.18)]" : "font-medium text-[#5F5F64]"} disabled:opacity-35`}>{o.label}</button>)}
  </div>;
}

export function PrimaryButton({ children, className = "", ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className={`flex h-[50px] w-full items-center justify-center rounded-[14px] bg-[#0071E3] px-5 text-[16px] font-semibold text-white active:opacity-80 disabled:bg-black/10 disabled:text-black/35 ${className}`} {...rest}>{children}</button>;
}

export function Dot({ color }: { color: string }) {
  return <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color }} />;
}
