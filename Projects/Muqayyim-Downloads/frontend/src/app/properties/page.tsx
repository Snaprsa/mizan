"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { createProperty, deleteProperty, listProperties, PropertySummary, restoreProperty } from "@/lib/api";
import { errorText } from "@/lib/monitor";

export default function PropertiesPage() {
  const router = useRouter();
  const [rows, setRows] = useState<PropertySummary[]>([]);
  const [q, setQ] = useState(""); const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0); const [loading, setLoading] = useState(true);
  const [error, setError] = useState(""); const [saving, setSaving] = useState(false); const [adding, setAdding] = useState(false);
  const [showDeleted, setShowDeleted] = useState(false); const [confirm, setConfirm] = useState<string | null>(null);
  const [undo, setUndo] = useState<PropertySummary | null>(null); const [busy, setBusy] = useState(""); const [reload, setReload] = useState(0);
  useEffect(() => { let active = true; setLoading(true);
    listProperties(q, offset, showDeleted).then(r => { if (active) { setRows(r.data); setTotal(r.total); } })
      .catch(e => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [q, offset, showDeleted, reload]);
  // Deleting hides a property; nothing is erased, so it can always be restored.
  async function remove(r: PropertySummary) {
    setBusy(r.id); setError("");
    try { await deleteProperty(r.id); setConfirm(null); setUndo(r); setReload(n => n + 1); }
    catch (e) { setError(errorText(e)); } finally { setBusy(""); }
  }
  async function restore(r: PropertySummary) {
    setBusy(r.id); setError("");
    try { await restoreProperty(r.id); setUndo(null); setReload(n => n + 1); }
    catch (e) { setError(errorText(e)); } finally { setBusy(""); }
  }
  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setSaving(true); setError("");
    const f = new FormData(e.currentTarget);
    try {
      const p = await createProperty({ name: String(f.get("name")), case_id: null, country: "SA", currency: "SAR", locale: "en-SA", property_type: null,
        location: { city: f.get("city") || null, plot_number: f.get("plot") || null }, land: {}, planning: {}, building: {}, financial: {},
        provenance: { source: "User input" } });
      router.push(`/properties/${p.id}`);
    } catch (err) { setError((err as Error).message); } finally { setSaving(false); }
  }
  return <div className="space-y-5">
    <header className="flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-[28px] font-semibold tracking-tight">Properties</h1>
      <p className="mt-0.5 text-[14px] text-black/50">{total} {showDeleted ? "deleted" : ""} {total === 1 ? "property" : "properties"}</p></div>
      <div className="flex items-center gap-3">
        <button type="button" className="text-[14px] font-medium text-[#0062C4]" onClick={() => { setShowDeleted(v => !v); setOffset(0); setConfirm(null); }}>{showDeleted ? "Back to properties" : "Deleted"}</button>
        {!showDeleted && <button type="button" className="mizan-button" onClick={() => setAdding(v => !v)}>{adding ? "Cancel" : "Add property"}</button>}</div></header>
    {undo && <div role="status" className="mizan-rise-in flex items-center gap-3 rounded-xl bg-[#1D1D1F] px-4 py-3 text-[14px] text-white">
      <span className="flex-1" dir="auto">Deleted “{undo.name}”. Its history is kept.</span>
      <button type="button" disabled={busy === undo.id} className="font-semibold text-[#64B5FF]" onClick={() => restore(undo)}>Undo</button>
      <button type="button" aria-label="Dismiss" className="text-white/60" onClick={() => setUndo(null)}>✕</button></div>}
    {error && <p role="alert" className="mizan-error">{error}</p>}
    {adding && <form onSubmit={create} className="mizan-panel flex flex-wrap items-end gap-3">
      <label className="mizan-label flex-1 min-w-[180px]">Property name<input className="mizan-input" name="name" required maxLength={255} autoFocus /></label>
      <label className="mizan-label flex-1 min-w-[140px]">City<input className="mizan-input" name="city" /></label>
      <label className="mizan-label flex-1 min-w-[120px]">Plot number<input className="mizan-input" name="plot" /></label>
      <button disabled={saving} className="mizan-button">{saving ? "Creating…" : "Create"}</button>
    </form>}
    <input aria-label="Search properties" placeholder="Search name, city, district, address or plot" className="mizan-input max-w-md !rounded-[10px]" type="search" value={q} onChange={e => { setQ(e.target.value); setOffset(0); }} />
    <div className="mizan-panel overflow-x-auto"><table className="mizan-table"><thead><tr>{["Property", "City / district", "Type", "Revision", showDeleted ? "Deleted" : "Updated", ""].map(h => <th key={h}>{h}</th>)}</tr></thead>
      <tbody>{rows.map(r => <tr key={r.id}><td><Link className="font-medium" dir="auto" href={`/properties/${r.id}`}>{r.name}</Link></td>
        <td>{[r.city, r.district].filter(Boolean).join(" / ") || "Unknown"}</td><td>{r.property_type || "Unknown"}</td><td className="text-black/45">{r.revision}</td><td>{new Date((showDeleted && r.deleted_at) || r.updated_at).toLocaleDateString()}</td>
        <td className="whitespace-nowrap text-right">{showDeleted ? <button type="button" disabled={busy === r.id} className="text-[14px] font-medium text-[#0062C4] disabled:opacity-40" onClick={() => restore(r)}>{busy === r.id ? "Restoring…" : "Restore"}</button>
          : confirm === r.id ? <span className="inline-flex items-center gap-3 text-[14px]"><span className="text-black/55">Delete?</span>
            <button type="button" disabled={busy === r.id} className="font-semibold text-[#C0271B] disabled:opacity-40" onClick={() => remove(r)}>{busy === r.id ? "Deleting…" : "Delete"}</button>
            <button type="button" className="text-black/55" onClick={() => setConfirm(null)}>Cancel</button></span>
          : <button type="button" aria-label={`Delete ${r.name}`} title="Delete" className="grid h-8 w-8 place-items-center rounded-full text-black/40 hover:bg-[#C0271B]/10 hover:text-[#C0271B]" onClick={() => setConfirm(r.id)}><Trash2 size={16} /></button>}</td></tr>)}</tbody></table>
      {loading && <p className="text-sm py-4" role="status">Loading properties…</p>}
      {!loading && !rows.length && <p className="text-sm py-4 text-slate-500">{showDeleted ? "Nothing deleted." : "No properties found."}</p>}
      {showDeleted && rows.length > 0 && <p className="pt-3 text-[12.5px] text-black/45">Deleted properties are hidden from the map and lists. Their history and saved valuations are kept; restore one to use it again.</p>}
      <div className="flex gap-3 mt-3 text-sm"><button disabled={!offset} onClick={() => setOffset(offset - 50)}>Previous</button><span>{total ? offset + 1 : 0}–{offset + rows.length} of {total}</span><button disabled={offset + 50 >= total} onClick={() => setOffset(offset + 50)}>Next</button></div>
    </div>
  </div>;
}
