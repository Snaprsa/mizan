import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import {
  LayoutDashboard, PlusCircle, UserSquare2,
  SlidersHorizontal, SearchCode, FileBarChart2, Building2, MapPin,
} from "lucide-react";
import { ToastProvider } from "@/hooks/use-toast";

export const metadata: Metadata = {
  title: "Mizan — Real Estate Intelligence",
  description: "Saudi Real Estate Intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Remove browser-extension attributes (e.g. Kantu's data-kantu) before React hydrates
            to prevent "Extra attributes from server" hydration mismatches. */}
        <script dangerouslySetInnerHTML={{ __html: `(function(){var h=document.documentElement;h.removeAttribute('data-kantu');var o=new MutationObserver(function(ms){ms.forEach(function(m){if(m.attributeName==='data-kantu')h.removeAttribute('data-kantu');});});o.observe(h,{attributes:true});})();` }} />
      </head>
      <body className="bg-slate-50 text-slate-900 antialiased" suppressHydrationWarning>
        <div className="flex h-screen overflow-hidden">
          {/* ── Sidebar ── */}
          <aside className="w-60 flex-shrink-0 bg-slate-900 flex flex-col select-none">
            {/* Logo */}
            <div className="px-5 py-4 border-b border-slate-700/60">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg">
                  <Building2 className="w-4 h-4 text-white" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-white leading-tight">Mizan ميزان</div>
                  <div className="text-xs text-slate-400 leading-tight mt-0.5">Real Estate Intelligence</div>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
              <NavLink href="/map" icon={<MapPin size={15} />} label="Start valuation" />
              <NavLink href="/dashboard" icon={<LayoutDashboard size={15} />} label="Cases & Dashboard" />
              <NavLink href="/properties" icon={<Building2 size={15} />} label="Properties" />
              <NavLink href="/data" icon={<SearchCode size={15} />} label="Market Data" />
              <NavLink href="/cases/new" icon={<PlusCircle size={15} />} label="New Case" />

              <div className="pt-5 mt-5 border-t border-slate-700/60">
                <p className="px-3 pb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
                  Not yet implemented
                </p>
                <NavLink href="/subject" icon={<UserSquare2 size={15} />} label="Subject Profile" />
                <NavLink href="/adjustments" icon={<SlidersHorizontal size={15} />} label="Adjustments" />
                <NavLink href="/discovery" icon={<SearchCode size={15} />} label="Discovery" />
                <NavLink href="/reports" icon={<FileBarChart2 size={15} />} label="Reports" />
              </div>
            </nav>

            {/* Footer */}
            <div className="px-5 py-3 border-t border-slate-700/60">
              <span className="text-[11px] text-slate-500">v0.2 · Property foundation</span>
            </div>
          </aside>

          {/* ── Main ── */}
          <main className="flex-1 overflow-auto bg-slate-50">
            <div className="max-w-7xl mx-auto px-8 py-8">
              <ToastProvider>{children}</ToastProvider>
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-all group"
    >
      <span className="group-hover:text-blue-400 transition-colors">{icon}</span>
      {label}
    </Link>
  );
}
