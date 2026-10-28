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
  const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
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
    <header><h1 className="text-2xl font-semibold">Properties <span lang="ar" dir="rtl" className="text-slate-400 text-lg">العقارات</span></h1>
      <p className="text-sm text-slate-500 mt-1">Permanent workspaces · Saudi Arabia · SAR · {total} assets</p></header>
    {error && <p role="alert" className="mizan-error">{error}</p>}
    <form onSubmit={create} className="mizan-panel flex flex-wrap gap-3 items-end">
      <label className="mizan-label">Property name<input className="mizan-input" name="name" required maxLength={255} /></label>
      <label className="mizan-label">City<input className="mizan-input" name="city" /></label>
      <label className="mizan-label">Plot number<input className="mizan-input" name="plot" /></label>
      <button disabled={saving} className="mizan-button">{saving ? "Creating…" : "Add property"}</button>
      <p className="w-full text-xs text-slate-500">Start with a name. Add coordinates, address, source URL and property details in the workspace.</p>
    </form>
    <label className="mizan-label">Search name, city, district, address or plot<input className="mizan-input max-w-md" type="search" value={q} onChange={e => { setQ(e.target.value); setOffset(0); }} /></label>
    <div className="mizan-panel overflow-x-auto"><table className="mizan-table"><thead><tr>{["Property", "City / district", "Type", "Revision", "Updated"].map(h => <th key={h}>{h}</th>)}</tr></thead>
      <tbody>{rows.map(r => <tr key={r.id}><td><Link className="text-blue-700 font-medium" href={`/properties/${r.id}`}>{r.name}</Link></td>
        <td>{[r.city, r.district].filter(Boolean).join(" / ") || "Unknown"}</td><td>{r.property_type || "Unknown"}</td><td>{r.revision}</td><td>{new Date(r.updated_at).toLocaleDateString()}</td></tr>)}</tbody></table>
      {loading && <p className="text-sm py-4" role="status">Loading properties…</p>}
      {!loading && !rows.length && <p className="text-sm py-4 text-slate-500">No properties found. Add your first asset above.</p>}
      <div className="flex gap-3 mt-3 text-sm"><button disabled={!offset} onClick={() => setOffset(offset - 50)}>Previous</button><span>{total ? offset + 1 : 0}–{offset + rows.length} of {total}</span><button disabled={offset + 50 >= total} onClick={() => setOffset(offset + 50)}>Next</button></div>
    </div>
  </div>;
}
