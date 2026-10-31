"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createProperty, listProperties, PropertySummary } from "@/lib/api";

export default function PropertiesPage() {
  const router = useRouter();
  const [rows, setRows] = useState<PropertySummary[]>([]);
  const [q, setQ] = useState(""); const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0); const [loading, setLoading] = useState(true);
  const [error, setError] = useState(""); const [saving, setSaving] = useState(false); const [adding, setAdding] = useState(false);
  useEffect(() => { let active = true; setLoading(true);
    listProperties(q, offset).then(r => { if (active) { setRows(r.data); setTotal(r.total); } })
      .catch(e => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [q, offset]);
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
      <p className="mt-0.5 text-[14px] text-black/50">{total} {total === 1 ? "property" : "properties"}</p></div>
      <button type="button" className="mizan-button" onClick={() => setAdding(v => !v)}>{adding ? "Cancel" : "Add property"}</button></header>
    {error && <p role="alert" className="mizan-error">{error}</p>}
    {adding && <form onSubmit={create} className="mizan-panel flex flex-wrap items-end gap-3">
      <label className="mizan-label flex-1 min-w-[180px]">Property name<input className="mizan-input" name="name" required maxLength={255} autoFocus /></label>
      <label className="mizan-label flex-1 min-w-[140px]">City<input className="mizan-input" name="city" /></label>
      <label className="mizan-label flex-1 min-w-[120px]">Plot number<input className="mizan-input" name="plot" /></label>
      <button disabled={saving} className="mizan-button">{saving ? "Creating…" : "Create"}</button>
    </form>}
    <input aria-label="Search properties" placeholder="Search name, city, district, address or plot" className="mizan-input max-w-md !rounded-[10px]" type="search" value={q} onChange={e => { setQ(e.target.value); setOffset(0); }} />
    <div className="mizan-panel overflow-x-auto"><table className="mizan-table"><thead><tr>{["Property", "City / district", "Type", "Revision", "Updated"].map(h => <th key={h}>{h}</th>)}</tr></thead>
      <tbody>{rows.map(r => <tr key={r.id}><td><Link className="font-medium" dir="auto" href={`/properties/${r.id}`}>{r.name}</Link></td>
        <td>{[r.city, r.district].filter(Boolean).join(" / ") || "Unknown"}</td><td>{r.property_type || "Unknown"}</td><td className="text-black/45">{r.revision}</td><td>{new Date(r.updated_at).toLocaleDateString()}</td></tr>)}</tbody></table>
      {loading && <p className="text-sm py-4" role="status">Loading properties…</p>}
      {!loading && !rows.length && <p className="text-sm py-4 text-slate-500">No properties found.</p>}
      <div className="flex gap-3 mt-3 text-sm"><button disabled={!offset} onClick={() => setOffset(offset - 50)}>Previous</button><span>{total ? offset + 1 : 0}–{offset + rows.length} of {total}</span><button disabled={offset + 50 >= total} onClick={() => setOffset(offset + 50)}>Next</button></div>
    </div>
  </div>;
}
