"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCases } from "@/lib/api";
import type { Case } from "@/lib/types";
import { FolderOpen, Layers, CheckSquare, Plus, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCases()
      .then((res) => setCases(res.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const totalSources = cases.reduce((s, c) => s + c.source_count, 0);
  const totalComps   = cases.reduce((s, c) => s + c.comparable_count, 0);
  const activeCases  = cases.filter((c) => c.status === "in_progress" || c.status === "review").length;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Valuation Cases</h1>
          <p className="text-sm text-slate-500 mt-1">Manage your real estate valuation projects</p>
        </div>
        <Link
          href="/cases/new"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
        >
          <Plus size={15} />
          New Case
        </Link>
      </div>

      {/* Stats */}
      {!loading && cases.length > 0 && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <StatCard icon={<FolderOpen size={18} />}  label="Total Cases"   value={cases.length}  color="blue" />
          <StatCard icon={<TrendingUp size={18} />}   label="Active"        value={activeCases}   color="green" />
          <StatCard icon={<Layers size={18} />}       label="Sources"       value={totalSources}  color="purple" />
          <StatCard icon={<CheckSquare size={18} />}  label="Comparables"   value={totalComps}    color="orange" />
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-slate-400 py-12 justify-center">
          <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-sm">Loading cases…</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {!loading && cases.length === 0 && (
        <div className="text-center py-24 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mx-auto mb-4">
            <FolderOpen size={22} className="text-slate-400" />
          </div>
          <p className="text-slate-700 font-medium mb-1">No cases yet</p>
          <p className="text-slate-400 text-sm mb-5">Create your first valuation case to get started</p>
          <Link
            href="/cases/new"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Plus size={14} /> Create Case
          </Link>
        </div>
      )}

      {cases.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Case</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Sources</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Comps</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors cursor-pointer group">
                  <td className="px-5 py-3.5">
                    <Link href={`/cases/${c.id}`} className="block">
                      <div className="font-medium text-slate-900 group-hover:text-blue-600 transition-colors">{c.title}</div>
                      {c.description && (
                        <div className="text-xs text-slate-400 mt-0.5 truncate max-w-sm">{c.description}</div>
                      )}
                    </Link>
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span className="text-slate-600 font-medium">{c.source_count}</span>
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span className="text-slate-600 font-medium">{c.comparable_count}</span>
                  </td>
                  <td className="px-4 py-3.5 text-slate-400 text-xs">
                    {new Date(c.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon, label, value, color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: "blue" | "green" | "purple" | "orange";
}) {
  const colors = {
    blue:   "bg-blue-50 text-blue-600",
    green:  "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
    orange: "bg-orange-50 text-orange-600",
  };
  return (
    <div className="bg-white rounded-xl border border-slate-200 px-5 py-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-500 font-medium">{label}</span>
        <span className={`p-1.5 rounded-lg ${colors[color]}`}>{icon}</span>
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    draft:       "bg-slate-100 text-slate-500",
    in_progress: "bg-blue-50 text-blue-700 border border-blue-200",
    review:      "bg-amber-50 text-amber-700 border border-amber-200",
    completed:   "bg-green-50 text-green-700 border border-green-200",
    archived:    "bg-slate-100 text-slate-400",
  };
  const labels: Record<string, string> = {
    draft: "Draft", in_progress: "In Progress",
    review: "Review", completed: "Completed", archived: "Archived",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.draft}`}>
      {labels[status] || status}
    </span>
  );
}
