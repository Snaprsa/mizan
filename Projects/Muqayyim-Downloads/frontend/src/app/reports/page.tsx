"use client";

import { FileBarChart2, Construction } from "lucide-react";
import Link from "next/link";

export default function ReportsPage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-4">
        <Link href="/" className="hover:text-slate-600 transition-colors">Dashboard</Link>
        <span>›</span>
        <span className="text-slate-600">Reports</span>
      </div>

      <div className="text-center py-24 bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="w-14 h-14 bg-orange-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <FileBarChart2 size={28} className="text-orange-400" />
        </div>
        <h1 className="text-xl font-bold text-slate-900 mb-2">Valuation Reports</h1>
        <p className="text-sm text-slate-500 max-w-md mx-auto mb-4">
          Generate full professional valuation reports combining subject profile, comparables,
          adjustments, and final value opinion — RICS/TAQEEM format ready.
        </p>
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 rounded-lg text-sm font-medium border border-amber-200">
          <Construction size={15} />
          Stage 5 — Coming Soon
        </div>
      </div>
    </div>
  );
}
