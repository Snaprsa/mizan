"use client";

import { SearchCode, Construction } from "lucide-react";
import Link from "next/link";

export default function DiscoveryPage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-4">
        <Link href="/" className="hover:text-slate-600 transition-colors">Dashboard</Link>
        <span>›</span>
        <span className="text-slate-600">Discovery</span>
      </div>

      <div className="text-center py-24 bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <SearchCode size={28} className="text-green-400" />
        </div>
        <h1 className="text-xl font-bold text-slate-900 mb-2">Comparable Discovery</h1>
        <p className="text-sm text-slate-500 max-w-md mx-auto mb-4">
          Automated search across provider plugins (Aqar, Paseetah, AqarSAS) to discover
          relevant comparables matching your subject property criteria.
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-lg text-sm font-medium border border-amber-200">
          <Construction size={15} />
          Stage 4 — Coming Soon
        </div>
      </div>
    </div>
  );
}
