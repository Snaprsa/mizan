"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createCase } from "@/lib/api";
import { ArrowLeft, Briefcase } from "lucide-react";

export default function NewCasePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const newCase = await createCase({ title: title.trim(), description: description.trim() || undefined });
      router.push(`/cases/${newCase.id}`);
    } catch (e: any) {
      setError(e.message || "Failed to create case");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade-in max-w-lg">
      {/* Back */}
      <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors mb-6">
        <ArrowLeft size={14} /> Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
          <Briefcase size={18} className="text-[#007AFF]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-900">New Valuation Case</h1>
          <p className="text-sm text-slate-500">Start a new real estate valuation project</p>
        </div>
      </div>

      {/* Form card */}
      <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Case Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Villa Valuation — Al Nakheel, Riyadh"
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder-slate-400"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Description
              <span className="text-slate-400 font-normal ml-1">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the valuation scope, client, or property details…"
              rows={3}
              className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder-slate-400 resize-none"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="flex items-center gap-3 pt-1">
            <button
              type="submit"
              disabled={loading || !title.trim()}
              className="px-5 py-2.5 bg-[#007AFF] text-white rounded-full text-sm font-medium hover:bg-[#0068d9] disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Creating…
                </span>
              ) : "Create Case"}
            </button>
            <button
              type="button"
              onClick={() => router.push("/")}
              className="px-4 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      {/* Hint */}
      <p className="text-xs text-slate-400 mt-4 leading-relaxed">
        After creating the case you can add comparable sources (URLs or PDFs) and run extraction to populate the comparables table.
      </p>
    </div>
  );
}
