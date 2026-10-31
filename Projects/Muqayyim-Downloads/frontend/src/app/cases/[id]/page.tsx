"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getCase, listSources, addUrlSource, uploadPdfSource,
  startExtraction, getExtractionJob,
  listComparables, overrideField, updateComparableStatus,
  downloadExport,
} from "@/lib/api";
import type { Case, Source, Comparable, ExtractedField, ExtractionJob } from "@/lib/types";
import { RELIABILITY_LABELS, EVIDENCE_LABELS, confidenceColor, confidenceLabel } from "@/lib/types";
import {
  ArrowLeft, Link2, FileUp, Zap, Download,
  FileSpreadsheet, FileText, FileBarChart2,
  X, Pencil, ChevronRight,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

type Tab = "sources" | "comparables" | "export";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<Case | null>(null);
  const [tab, setTab] = useState<Tab>("sources");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCase(caseId).then(setCaseData).catch((e) => setError(e.message));
  }, [caseId]);

  if (error) return (
    <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>
  );
  if (!caseData) return (
    <div className="flex items-center gap-2 text-slate-400 py-12 justify-center">
      <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
      <span className="text-sm">Loading case…</span>
    </div>
  );

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "sources",     label: "Sources",     icon: <Link2 size={14} /> },
    { id: "comparables", label: "Comparables", icon: <FileBarChart2 size={14} /> },
    { id: "export",      label: "Export",      icon: <Download size={14} /> },
  ];

  return (
    <div className="animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-4">
        <Link href="/dashboard" className="hover:text-slate-600 transition-colors">Dashboard</Link>
        <ChevronRight size={12} />
        <span className="text-slate-600">{caseData.title}</span>
      </div>

      <Link href={`/map?case_id=${caseId}`} className="inline-block text-sm text-[#007AFF] mb-4">View this case on the map →</Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{caseData.title}</h1>
          {caseData.description && (
            <p className="text-sm text-slate-500 mt-1">{caseData.description}</p>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <Chip label={`${caseData.source_count} source${caseData.source_count !== 1 ? "s" : ""}`} />
          <Chip label={`${caseData.comparable_count} comp${caseData.comparable_count !== 1 ? "s" : ""}`} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 mb-6">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-all ${
              tab === t.id
                ? "border-blue-600 text-[#007AFF]"
                : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {tab === "sources"     && <SourcesTab caseId={caseId} />}
      {tab === "comparables" && <ComparablesTab caseId={caseId} />}
      {tab === "export"      && <ExportTab caseId={caseId} caseTitle={caseData.title} />}
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <span className="bg-slate-100 text-slate-500 px-2.5 py-1 rounded-full text-xs font-medium">{label}</span>
  );
}

// ─── Sources Tab ──────────────────────────────────────────────────────────────

function SourcesTab({ caseId }: { caseId: string }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [extractingIds, setExtractingIds] = useState<Set<string>>(new Set());
  const toast = useToast();

  const loadSources = useCallback(() => {
    listSources(caseId).then(setSources).catch(console.error);
  }, [caseId]);

  useEffect(() => { loadSources(); }, [loadSources]);

  async function handleAddUrl(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    try {
      await addUrlSource(caseId, { url: url.trim() });
      setUrl("");
      toast.success("Source added successfully");
      loadSources();
    } catch (e: any) {
      toast.error("Failed to add source: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      await uploadPdfSource(caseId, file);
      toast.success("PDF uploaded successfully");
      loadSources();
    } catch (err: any) {
      toast.error("Upload error: " + err.message);
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  }

  async function handleExtract(sourceId: string) {
    setExtractingIds((prev) => new Set(prev).add(sourceId));
    try {
      const res = await startExtraction(sourceId);

      // Check if extraction already completed (inline MVP) or failed
      if (res.status === "failed") {
        toast.error(res.message || "Extraction failed");
        setExtractingIds((prev) => {
          const next = new Set(prev);
          next.delete(sourceId);
          return next;
        });
        loadSources();
        return;
      }

      if (res.status === "completed") {
        toast.success(res.message || "Extraction completed");
        setExtractingIds((prev) => {
          const next = new Set(prev);
          next.delete(sourceId);
          return next;
        });
        loadSources();
        return;
      }

      // Poll for completion (async extraction)
      const poll = setInterval(async () => {
        const job = await getExtractionJob(res.job_id);
        if (job.status === "completed") {
          clearInterval(poll);
          toast.success("Extraction completed");
          setExtractingIds((prev) => {
            const next = new Set(prev);
            next.delete(sourceId);
            return next;
          });
          loadSources();
        } else if (job.status === "failed") {
          clearInterval(poll);
          toast.error(job.error_log || "Extraction failed");
          setExtractingIds((prev) => {
            const next = new Set(prev);
            next.delete(sourceId);
            return next;
          });
          loadSources();
        }
      }, 2000);
    } catch (e: any) {
      toast.error("Extraction error: " + e.message);
      setExtractingIds((prev) => {
        const next = new Set(prev);
        next.delete(sourceId);
        return next;
      });
    }
  }

  return (
    <div className="space-y-5">
      {/* Input card */}
      <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Add Comparable Source</h3>

        {/* URL input */}
        <form onSubmit={handleAddUrl} className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Link2 size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste listing URL (aqarsas.sa, paseetah.com, aqar.fm …)"
              className="w-full pl-8 pr-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-slate-400"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="px-4 py-2.5 bg-[#007AFF] text-white rounded-full text-sm font-medium hover:bg-[#0068d9] disabled:opacity-50 transition-colors shadow-sm whitespace-nowrap"
          >
            Add URL
          </button>
        </form>

        {/* PDF upload */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">or</span>
          <label className="inline-flex items-center gap-1.5 px-3 py-2 border border-dashed border-slate-300 rounded-lg text-xs text-slate-500 hover:border-blue-400 hover:text-[#007AFF] cursor-pointer transition-colors">
            <FileUp size={13} />
            Upload PDF
            <input type="file" accept=".pdf" onChange={handleUpload} className="hidden" />
          </label>
          {loading && (
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className="w-3 h-3 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
              Processing…
            </span>
          )}
        </div>
      </div>

      {/* Source list */}
      {sources.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-8">No sources added yet.</p>
      ) : (
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="text-left px-5 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">Source</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sources.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3 max-w-sm">
                    {s.url ? (
                      <a href={s.url} target="_blank" rel="noopener noreferrer"
                        className="text-[#007AFF] hover:underline text-xs truncate block">{s.url}</a>
                    ) : (
                      <span className="text-xs text-slate-600">{s.file_name || "—"}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      s.source_type === "url" ? "bg-blue-50 text-[#007AFF]" : "bg-purple-50 text-purple-600"
                    }`}>
                      {s.source_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <SourceStatusBadge status={s.status} errorMessage={s.error_message} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleExtract(s.id)}
                      disabled={extractingIds.has(s.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                      {extractingIds.has(s.id) ? (
                        <>
                          <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                          Extracting…
                        </>
                      ) : (
                        <>
                          <Zap size={11} /> Extract
                        </>
                      )}
                    </button>
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

function SourceStatusBadge({ status, errorMessage }: { status: string; errorMessage: string | null }) {
  const styles: Record<string, string> = {
    pending:   "bg-slate-100 text-slate-500",
    fetched:   "bg-blue-50 text-[#007AFF]",
    completed: "bg-green-50 text-green-700",
    failed:    "bg-red-50 text-red-600",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${styles[status] || styles.pending}`}
      title={errorMessage || undefined}
    >
      {status}
      {errorMessage && " ⚠"}
    </span>
  );
}

// ─── Field name aliases ───────────────────────────────────────────────────────

const FIELD_ALIASES: Record<string, string[]> = {
  city:             ["city", "city_en", "city_ar"],
  asking_price:     ["asking_price", "transacted_price"],
  primary_area_sqm: ["primary_area_sqm", "area_sqm"],
  listing_date:     ["listing_date", "transaction_date"],
};

// ─── Comparables Tab ──────────────────────────────────────────────────────────

function ComparablesTab({ caseId }: { caseId: string }) {
  const [comps, setComps] = useState<Comparable[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedField, setSelectedField] = useState<{ comp: Comparable; field: ExtractedField } | null>(null);
  const [overrideModal, setOverrideModal] = useState<{ comp: Comparable; field: ExtractedField } | null>(null);

  const loadComps = useCallback(() => {
    setLoading(true);
    listComparables(caseId)
      .then((res) => setComps(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [caseId]);

  useEffect(() => { loadComps(); }, [loadComps]);

  async function handleStatusChange(compId: string, status: "active" | "invalid" | "outlier") {
    await updateComparableStatus(compId, { status });
    loadComps();
  }

  if (loading) return (
    <div className="flex items-center gap-2 text-slate-400 py-12 justify-center">
      <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
      <span className="text-sm">Loading comparables…</span>
    </div>
  );

  if (comps.length === 0) return (
    <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
      <FileBarChart2 size={28} className="text-slate-300 mx-auto mb-3" />
      <p className="text-sm font-medium text-slate-500">No comparables yet</p>
      <p className="text-xs text-slate-400 mt-1">Add sources and run extraction to populate this table.</p>
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-slate-500">
          <span className="font-semibold text-slate-900">{comps.length}</span> comparable{comps.length !== 1 ? "s" : ""}
        </span>
        <span className="text-xs text-slate-400">Click any highlighted cell for citation • hover for override</span>
      </div>

      <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {[
                "Status", "★", "City", "District", "Type", "Evidence",
                "Asking (SAR)", "Transacted (SAR)", "Area m²", "SAR/m²", "Date", "Actions"
              ].map((h) => (
                <th key={h} className="text-left px-3 py-2.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {comps.map((comp) => (
              <tr key={comp.id} className={`hover:bg-slate-50 transition-colors ${comp.status === "invalid" ? "opacity-40" : ""}`}>
                <td className="px-3 py-2.5">
                  <select
                    value={comp.status}
                    onChange={(e) => handleStatusChange(comp.id, e.target.value as any)}
                    className="text-[11px] border border-slate-200 rounded-md px-1.5 py-1 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  >
                    <option value="active">Active</option>
                    <option value="draft">Draft</option>
                    <option value="invalid">Invalid</option>
                    <option value="outlier">Outlier</option>
                  </select>
                </td>
                <td className="px-3 py-2.5">
                  <span className="text-amber-400 text-sm" title={RELIABILITY_LABELS[comp.reliability_score]}>
                    {"★".repeat(comp.reliability_score)}
                    <span className="text-slate-200">{"★".repeat(5 - comp.reliability_score)}</span>
                  </span>
                </td>

                <FieldCell comp={comp} fieldName="city"             value={comp.city}           onCitation={setSelectedField} onOverride={setOverrideModal} />
                <FieldCell comp={comp} fieldName="district"         value={comp.district}       onCitation={setSelectedField} onOverride={setOverrideModal} />
                <FieldCell comp={comp} fieldName="property_type"    value={comp.property_type}  onCitation={setSelectedField} onOverride={setOverrideModal} />

                <td className="px-3 py-2.5">
                  <EvidenceBadge evidenceType={comp.evidence_type} />
                </td>

                <FieldCell comp={comp} fieldName="asking_price"     value={fmtSAR(comp.asking_price)}      onCitation={setSelectedField} onOverride={setOverrideModal} />
                <FieldCell comp={comp} fieldName="transacted_price" value={fmtSAR(comp.transacted_price)}  onCitation={setSelectedField} onOverride={setOverrideModal} />
                <FieldCell comp={comp} fieldName="primary_area_sqm" value={fmtNum(comp.primary_area_sqm)}  onCitation={setSelectedField} onOverride={setOverrideModal} />

                <td className="px-3 py-2.5 font-semibold text-slate-700">
                  {comp.price_per_sqm ? fmtSAR(comp.price_per_sqm) : <span className="text-slate-300">—</span>}
                </td>

                <FieldCell comp={comp} fieldName="listing_date"     value={comp.listing_date || comp.transaction_date} onCitation={setSelectedField} onOverride={setOverrideModal} />

                <td className="px-3 py-2.5">
                  <button
                    onClick={() => {
                      const f = comp.extracted_fields[0];
                      if (f) setSelectedField({ comp, field: f });
                    }}
                    className="text-[11px] text-[#007AFF] hover:underline"
                  >
                    All fields
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedField && (
        <CitationModal comp={selectedField.comp} field={selectedField.field} onClose={() => setSelectedField(null)} />
      )}
      {overrideModal && (
        <OverrideModal comp={overrideModal.comp} field={overrideModal.field} onClose={() => setOverrideModal(null)} onSaved={loadComps} />
      )}
    </div>
  );
}

function fmtSAR(n: number | null | undefined) {
  if (n == null) return null;
  return n.toLocaleString("en-SA");
}
function fmtNum(n: number | null | undefined) {
  if (n == null) return null;
  return n.toLocaleString("en-SA");
}

function EvidenceBadge({ evidenceType }: { evidenceType: string | null }) {
  const styles: Record<string, string> = {
    transaction_achieved: "bg-green-50 text-green-700 border border-green-200",
    listing_asking:       "bg-amber-50 text-amber-700 border border-amber-200",
    official_record:      "bg-blue-50 text-[#007AFF] border border-blue-200",
  };
  const label = EVIDENCE_LABELS[evidenceType || "unknown"] || evidenceType || "—";
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${styles[evidenceType || ""] || "bg-slate-100 text-slate-500"}`}>
      {label}
    </span>
  );
}

function FieldCell({
  comp, fieldName, value, onCitation, onOverride,
}: {
  comp: Comparable;
  fieldName: string;
  value: string | number | null | undefined;
  onCitation: (d: { comp: Comparable; field: ExtractedField }) => void;
  onOverride: (d: { comp: Comparable; field: ExtractedField }) => void;
}) {
  const aliases = FIELD_ALIASES[fieldName] ?? [fieldName];
  const field = comp.extracted_fields.find((f) => aliases.includes(f.field_name));
  const conf = field?.confidence ?? 0;
  const display = value != null && value !== "" ? String(value) : null;

  return (
    <td className="px-3 py-2.5 group relative">
      <span
        className={`cursor-pointer px-1 py-0.5 rounded text-[11px] transition-colors ${
          field ? `${confidenceColor(conf)} hover:ring-1 ring-current/20` : "text-slate-400"
        }`}
        title={field ? `${(conf * 100).toFixed(0)}% confidence — click for citation` : undefined}
        onClick={() => field && onCitation({ comp, field })}
      >
        {display ?? "—"}
      </span>
      {field && (
        <button
          onClick={(e) => { e.stopPropagation(); onOverride({ comp, field }); }}
          className="hidden group-hover:inline-flex ml-1 text-slate-300 hover:text-blue-500 transition-colors"
          title="Override value"
        >
          <Pencil size={10} />
        </button>
      )}
    </td>
  );
}

// ─── Citation Modal ───────────────────────────────────────────────────────────

function CitationModal({ comp, field, onClose }: { comp: Comparable; field: ExtractedField; onClose: () => void }) {
  const cit = field.citation;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg m-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Citation</p>
            <h3 className="font-semibold text-slate-900 text-sm mt-0.5">{field.field_name}</h3>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors">
            <X size={15} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-2 text-sm max-h-[60vh] overflow-y-auto">
          <Row label="Raw value"    value={field.raw_value} />
          <Row label="Normalized"   value={field.normalized_value} />
          <Row label="Display"      value={field.display_value} />
          <Row label="Confidence"   value={`${(field.confidence * 100).toFixed(0)}% — ${confidenceLabel(field.confidence)}`} />
          <Row label="Classification" value={field.classification} />
          {field.is_overridden && <Row label="Override" value={field.override_value} highlight />}

          {cit && (
            <>
              <hr className="border-slate-100 my-2" />
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Provenance</p>
              <Row label="Source"        value={cit.source_url_or_name} />
              <Row label="Type"          value={cit.source_type} />
              <Row label="Retrieved"     value={cit.retrieval_timestamp} />
              <Row label="Locator"       value={cit.locator} />
              <Row label="Extractor"     value={`${cit.extractor_name} v${cit.extractor_version}`} />
              <Row label="Parse conf"    value={`${(cit.parse_confidence * 100).toFixed(0)}%`} />
              {cit.llm_confidence != null && <Row label="LLM conf" value={`${(cit.llm_confidence * 100).toFixed(0)}%`} />}
              {cit.snippet && (
                <div>
                  <p className="text-[11px] font-medium text-slate-400 mb-1">Snippet</p>
                  <pre className="text-[11px] bg-slate-50 border border-slate-200 p-2.5 rounded-lg font-mono whitespace-pre-wrap max-h-28 overflow-auto text-slate-600">
                    {cit.snippet}
                  </pre>
                </div>
              )}
              {cit.normalization_notes && <Row label="Normalization" value={cit.normalization_notes} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, highlight }: { label: string; value: string | null | undefined; highlight?: boolean }) {
  return (
    <div className="flex gap-3">
      <span className="text-slate-400 w-28 shrink-0 text-xs">{label}</span>
      <span className={`text-xs break-all ${highlight ? "text-[#007AFF] font-semibold" : "text-slate-700"}`}>{value || "—"}</span>
    </div>
  );
}

// ─── Override Modal ───────────────────────────────────────────────────────────

function OverrideModal({
  comp, field, onClose, onSaved,
}: {
  comp: Comparable;
  field: ExtractedField;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [newValue, setNewValue] = useState(field.display_value || field.normalized_value || "");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  async function handleSave() {
    if (!reason.trim()) { toast.warning("Reason is required for all overrides."); return; }
    setSaving(true);
    try {
      await overrideField(comp.id, field.id, { new_value: newValue, reason: reason.trim() });
      toast.success("Field overridden successfully");
      onSaved();
      onClose();
    } catch (e: any) {
      toast.error("Override failed: " + e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md m-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Override</p>
            <h3 className="font-semibold text-slate-900 text-sm mt-0.5">{field.field_name}</h3>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 transition-colors">
            <X size={15} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="text-xs text-slate-500 font-medium block mb-1">Current value</label>
            <div className="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-600">
              {field.display_value || field.raw_value || <span className="italic text-slate-400">empty</span>}
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 font-medium block mb-1">New value</label>
            <input
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 font-medium block mb-1">
              Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Why is this value being changed?"
              rows={2}
              className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        </div>

        <div className="px-5 py-4 border-t border-slate-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !reason.trim()}
            className="px-4 py-2 bg-[#007AFF] text-white rounded-full text-sm font-medium hover:bg-[#0068d9] disabled:opacity-50 transition-colors"
          >
            {saving ? "Saving…" : "Save Override"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Export Tab ───────────────────────────────────────────────────────────────

function ExportTab({ caseId, caseTitle }: { caseId: string; caseTitle: string }) {
  return (
    <div className="max-w-lg">
      <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] p-6">
        <h3 className="font-semibold text-slate-900 mb-1">Export Comparables</h3>
        <p className="text-sm text-slate-500 mb-6">
          Download all active comparables with extracted values, confidence scores, and source citations.
        </p>

        <div className="grid grid-cols-3 gap-3">
          <ExportButton
            label="XLSX"
            sub="Excel workbook"
            icon={<FileSpreadsheet size={20} />}
            format="xlsx"
            caseId={caseId}
            color="bg-green-600 hover:bg-green-700"
          />
          <ExportButton
            label="CSV"
            sub="Spreadsheet data"
            icon={<FileText size={20} />}
            format="csv"
            caseId={caseId}
            color="bg-[#007AFF] hover:bg-[#0068d9]"
          />
          <ExportButton
            label="PDF"
            sub="Summary report"
            icon={<FileBarChart2 size={20} />}
            format="pdf"
            caseId={caseId}
            color="bg-red-500 hover:bg-red-600"
          />
        </div>

        <p className="text-xs text-slate-400 mt-4">
          Invalid comparables are excluded from exports.
        </p>
      </div>
    </div>
  );
}

function ExportButton({
  label, sub, icon, format, caseId, color,
}: {
  label: string;
  sub: string;
  icon: React.ReactNode;
  format: "csv" | "xlsx" | "pdf";
  caseId: string;
  color: string;
}) {
  return (
    <button
      onClick={() => downloadExport(caseId, format)}
      className={`flex flex-col items-center gap-2 p-4 text-white rounded-xl text-sm font-medium transition-colors shadow-sm ${color}`}
    >
      {icon}
      <span className="font-semibold">{label}</span>
      <span className="text-[10px] opacity-80 text-center leading-tight">{sub}</span>
    </button>
  );
}
