"use client";
// One search box: coordinates (exact as entered), saved Mizan records, and authorised address geocoding.
import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import type { MapRecord } from "@/lib/api";
import { parseCoordinates, type LatLng } from "@/lib/geo";
import { LAYER } from "@/lib/map-evidence";
import type { GeocodeResult } from "./types";

type Props = {
  records: MapRecord[]; geocodingAvailable: boolean; geocodingNote: string;
  geocode: (q: string) => Promise<GeocodeResult[]>;
  onCoordinates: (p: LatLng) => void; onRecord: (r: MapRecord) => void; onGeocoded: (r: GeocodeResult) => void;
};
const PRECISION: Record<GeocodeResult["precision"], string> = { rooftop: "Rooftop (provider)", range_interpolated: "Interpolated on street",
  geometric_center: "Area centre", approximate: "Approximate area" };

export default function MapSearch({ records, geocodingAvailable, geocodingNote, geocode, onCoordinates, onRecord, onGeocoded }: Props) {
  const [q, setQ] = useState(""); const [open, setOpen] = useState(false);
  const [geo, setGeo] = useState<GeocodeResult[] | null>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => { setGeo(null); setError(""); }, [q]);
  useEffect(() => { const close = (e: MouseEvent) => { if (!root.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close); return () => document.removeEventListener("mousedown", close); }, []);
  const coords = q.trim() ? parseCoordinates(q) : null;
  const term = q.trim().toLocaleLowerCase();
  const matches = term.length >= 2 && !coords ? records.filter(r => [r.title, r.district, r.city].some(v => v?.toLocaleLowerCase().includes(term))).slice(0, 6) : [];
  const plotLike = /\b(plot|parcel|plan|block|قطعة|مخطط)\b/i.test(q);
  async function runGeocode() {
    setBusy(true); setError("");
    try { setGeo(await geocode(q.trim())); } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  const done = () => { setOpen(false); setQ(""); };
  return <div ref={root} className="relative w-full max-w-md" onKeyDown={e => { if (e.key === "Escape") setOpen(false); }}>
    <label className="sr-only" htmlFor="map-search">Search coordinates, address or saved records</label>
    <div className="flex items-center h-8 rounded border border-slate-300 bg-white focus-within:ring-2 focus-within:ring-blue-500">
      <Search size={14} className="mx-2 text-slate-400 shrink-0" aria-hidden />
      <input id="map-search" value={q} onChange={e => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)}
        onKeyDown={e => { if (e.key === "Enter") { if (coords?.ok) { onCoordinates(coords.value); done(); } else if (geocodingAvailable && q.trim().length > 2) runGeocode(); } }}
        placeholder="24.7136, 46.6753 · address · saved property" className="flex-1 min-w-0 text-sm bg-transparent outline-none pr-2" autoComplete="off"
        role="combobox" aria-autocomplete="list" aria-expanded={open && !!q.trim()} aria-controls="map-search-results" />
    </div>
    {open && q.trim() && <div id="map-search-results" className="absolute z-[1200] mt-1 w-full rounded border border-slate-200 bg-white shadow-lg text-sm max-h-96 overflow-auto">
      {coords?.ok && <button type="button" className="w-full text-left px-3 py-2 hover:bg-blue-50" onClick={() => { onCoordinates(coords.value); done(); }}>
        Go to {coords.value.map(n => n.toFixed(6)).join(", ")} <span className="text-xs text-slate-500">· latitude, longitude · exact as entered</span>
        {coords.warning && <span className="block text-xs text-amber-700">{coords.warning}</span>}</button>}
      {coords && !coords.ok && <div className="px-3 py-2 text-xs text-red-700">{coords.error}
        {coords.swapped && <button type="button" className="block mt-1 text-blue-700 underline" onClick={() => { onCoordinates(coords.swapped!); done(); }}>
          Use {coords.swapped.map(n => n.toFixed(6)).join(", ")} (latitude, longitude)</button>}</div>}
      {matches.length > 0 && <p className="px-3 pt-2 text-[10px] uppercase tracking-wide text-slate-400">Saved in Mizan</p>}
      {matches.map(r => <button type="button" key={r.id} className="w-full text-left px-3 py-1.5 hover:bg-blue-50" onClick={() => { onRecord(r); done(); }}>
        <span className="inline-block w-2 h-2 rounded-full mr-2" style={{ background: LAYER[r.kind].color }} /><span dir="auto">{r.title}</span>
        <span className="text-xs text-slate-500"> · {LAYER[r.kind].short}{r.coordinates ? "" : " · location missing"}</span></button>)}
      {!coords && term.length > 2 && <div className="border-t border-slate-100 px-3 py-2">
        {geocodingAvailable ? <button type="button" className="text-blue-700 text-xs underline disabled:opacity-50" disabled={busy} onClick={runGeocode}>{busy ? "Searching…" : `Search address “${q.trim()}” (Google Geocoding)`}</button>
          : <p className="text-xs text-slate-500">{geocodingNote}</p>}
        {plotLike && <p className="text-xs text-slate-500 mt-1">Plot / plan-number lookup needs an authorised cadastral source; none is connected.</p>}
        {error && <p className="text-xs text-red-700 mt-1">{error}</p>}
        {geo && !geo.length && <p className="text-xs text-slate-500 mt-1">No address results in Saudi Arabia.</p>}
        {geo?.map((g, i) => <button type="button" key={i} className="w-full text-left py-1.5 hover:bg-blue-50" onClick={() => { onGeocoded(g); done(); }}>
          {g.label}<span className="block text-[11px] text-slate-500">{PRECISION[g.precision]} · geocoded, confirm on imagery</span></button>)}
      </div>}
    </div>}
  </div>;
}
