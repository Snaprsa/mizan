import "./globals.css";
import type { Metadata } from "next";
import AppShell from "@/components/app-shell";

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
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
