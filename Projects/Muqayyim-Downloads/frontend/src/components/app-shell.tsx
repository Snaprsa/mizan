"use client";
// Navigation shell. The map workspace is full-bleed; other screens keep the existing padded layout.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Building2, ChevronsLeft, ChevronsRight, LayoutDashboard, MapPin, PlusCircle, SearchCode } from "lucide-react";
import { ToastProvider } from "@/hooks/use-toast";

const NAV = [
  { href: "/map", icon: MapPin, label: "Map & valuation" },
  { href: "/dashboard", icon: LayoutDashboard, label: "Cases" },
  { href: "/properties", icon: Building2, label: "Properties" },
  { href: "/data", icon: SearchCode, label: "Market data" },
  { href: "/cases/new", icon: PlusCircle, label: "New case" },
];
const KEY = "mizan.sidebarCollapsed";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname() || "";
  const fullBleed = path === "/map" || path.startsWith("/map/");
  const [collapsed, setCollapsed] = useState<boolean | null>(null);
  const [narrow, setNarrow] = useState(false);
  useEffect(() => { const q = window.matchMedia("(max-width: 767px)"); setNarrow(q.matches); const on = () => setNarrow(q.matches); q.addEventListener("change", on); return () => q.removeEventListener("change", on); }, []);
  useEffect(() => { try { const v = localStorage.getItem(KEY); setCollapsed(v == null ? null : v === "1"); } catch { /* storage unavailable */ } }, []);
  const isCollapsed = collapsed ?? narrow;
  const toggle = () => { const next = !isCollapsed; setCollapsed(next); try { localStorage.setItem(KEY, next ? "1" : "0"); } catch { /* ignore */ } };
  if (fullBleed) return <div className="h-screen overflow-hidden"><ToastProvider>{children}</ToastProvider></div>;
  return <div className="flex h-screen overflow-hidden bg-[#f5f5f7]">
    <aside className={`${isCollapsed ? "w-14" : "w-52"} flex flex-shrink-0 select-none flex-col border-r border-black/[0.06] bg-white/70 backdrop-blur-xl transition-[width] duration-100`} aria-label="Main navigation">
      <div className="flex h-14 items-center gap-2.5 px-3">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-[10px] bg-[#007AFF]"><Building2 className="h-4 w-4 text-white" /></div>
        {!isCollapsed && <div className="truncate text-[15px] font-semibold text-black/85">Mizan <span lang="ar" className="font-normal text-black/40">ميزان</span></div>}
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-2">
        {NAV.map(n => <NavLink key={n.href} {...n} active={path === n.href || path.startsWith(n.href + "/")} collapsed={isCollapsed} />)}
      </nav>
      <button type="button" onClick={toggle} className="flex h-10 items-center gap-2 px-4 text-[12px] text-black/40 hover:text-black/70" aria-label={isCollapsed ? "Expand navigation" : "Collapse navigation"}>
        {isCollapsed ? <ChevronsRight size={15} /> : <><ChevronsLeft size={15} /><span>Collapse</span></>}
      </button>
    </aside>
    <main className="min-w-0 flex-1 overflow-auto"><ToastProvider><div className="mx-auto max-w-5xl px-6 py-8 md:px-10">{children}</div></ToastProvider></main>
  </div>;
}

function NavLink({ href, icon: Icon, label, active, collapsed }: { href: string; icon: typeof MapPin; label: string; active: boolean; collapsed: boolean }) {
  return <Link href={href} title={collapsed ? label : undefined} aria-label={collapsed ? label : undefined} aria-current={active ? "page" : undefined}
    className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-[14px] ${active ? "bg-[#007AFF]/10 font-medium text-[#007AFF]" : "text-black/70 hover:bg-black/[0.04]"}`}>
    <Icon size={16} className="shrink-0" />{!collapsed && <span className="truncate">{label}</span>}
  </Link>;
}
