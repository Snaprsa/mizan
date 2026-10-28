"use client";
// Navigation shell. The map workspace is full-bleed; other screens keep the existing padded layout.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Building2, ChevronsLeft, ChevronsRight, FileBarChart2, LayoutDashboard, MapPin, PlusCircle, SearchCode, SlidersHorizontal, UserSquare2 } from "lucide-react";
import { ToastProvider } from "@/hooks/use-toast";

const NAV = [
  { href: "/map", icon: MapPin, label: "Map & valuation" },
  { href: "/dashboard", icon: LayoutDashboard, label: "Cases & Dashboard" },
  { href: "/properties", icon: Building2, label: "Properties" },
  { href: "/data", icon: SearchCode, label: "Market Data" },
  { href: "/cases/new", icon: PlusCircle, label: "New Case" },
];
const LATER = [
  { href: "/subject", icon: UserSquare2, label: "Subject Profile" },
  { href: "/adjustments", icon: SlidersHorizontal, label: "Adjustments" },
  { href: "/discovery", icon: SearchCode, label: "Discovery" },
  { href: "/reports", icon: FileBarChart2, label: "Reports" },
];
const KEY = "mizan.sidebarCollapsed";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname() || "";
  const fullBleed = path === "/map" || path.startsWith("/map/");
  const [collapsed, setCollapsed] = useState<boolean | null>(null);
  useEffect(() => { try { const v = localStorage.getItem(KEY); setCollapsed(v == null ? null : v === "1"); } catch { /* storage unavailable */ } }, []);
  const isCollapsed = collapsed ?? fullBleed; // The map defaults to an icon rail to leave room for the canvas.
  const toggle = () => { const next = !isCollapsed; setCollapsed(next); try { localStorage.setItem(KEY, next ? "1" : "0"); } catch { /* ignore */ } };
  return <div className="flex h-screen overflow-hidden">
    <aside className={`${isCollapsed ? "w-14" : "w-56"} flex-shrink-0 bg-slate-900 flex flex-col select-none transition-[width] duration-100`} aria-label="Main navigation">
      <div className="h-12 px-3 flex items-center gap-2 border-b border-slate-700/60">
        <div className="w-8 h-8 shrink-0 rounded-md bg-blue-600 flex items-center justify-center"><Building2 className="w-4 h-4 text-white" /></div>
        {!isCollapsed && <div className="min-w-0"><div className="text-sm font-semibold text-white leading-tight">Mizan <span lang="ar">ميزان</span></div>
          <div className="text-[11px] text-slate-400 leading-tight">Real estate intelligence</div></div>}
      </div>
      <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-0.5">
        {NAV.map(n => <NavLink key={n.href} {...n} active={path === n.href || (n.href !== "/" && path.startsWith(n.href + "/"))} collapsed={isCollapsed} />)}
        <div className="pt-4 mt-4 border-t border-slate-700/60">
          {!isCollapsed && <p className="px-3 pb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">Not yet implemented</p>}
          {LATER.map(n => <NavLink key={n.href} {...n} active={path === n.href} collapsed={isCollapsed} muted />)}
        </div>
      </nav>
      <button type="button" onClick={toggle} className="h-10 flex items-center gap-2 px-4 text-xs text-slate-400 hover:text-white border-t border-slate-700/60"
        aria-label={isCollapsed ? "Expand navigation" : "Collapse navigation"}>
        {isCollapsed ? <ChevronsRight size={15} /> : <><ChevronsLeft size={15} /> <span>Collapse · v0.3</span></>}
      </button>
    </aside>
    <main className={`flex-1 min-w-0 bg-slate-50 ${fullBleed ? "overflow-hidden" : "overflow-auto"}`}>
      <ToastProvider>{fullBleed ? children : <div className="max-w-7xl mx-auto px-8 py-8">{children}</div>}</ToastProvider>
    </main>
  </div>;
}

function NavLink({ href, icon: Icon, label, active, collapsed, muted }: { href: string; icon: typeof MapPin; label: string; active: boolean; collapsed: boolean; muted?: boolean }) {
  return <Link href={href} title={collapsed ? label : undefined} aria-label={collapsed ? label : undefined} aria-current={active ? "page" : undefined}
    className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm ${active ? "bg-slate-800 text-white" : muted ? "text-slate-500 hover:text-slate-200 hover:bg-slate-800" : "text-slate-300 hover:text-white hover:bg-slate-800"}`}>
    <Icon size={15} className="shrink-0" />{!collapsed && <span className="truncate">{label}</span>}
  </Link>;
}
