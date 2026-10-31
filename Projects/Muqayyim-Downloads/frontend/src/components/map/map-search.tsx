"use client";
// Search: coordinates (exact as typed), saved Mizan records, and Esri address search (free tier).
// Address results only move the map; the user drops and confirms the pin.
import { useEffect, useRef, useState } from "react";
import { MapPin, Search, X } from "lucide-react";
import type { MapRecord } from "@/lib/api";
import { parseCoordinates, type LatLng } from "@/lib/geo";
import { LAYER } from "@/lib/map-evidence";
import { esriGeocode, readProviderConfig, type PlaceResult } from "@/lib/map-provider";

type Props = { records: MapRecord[]; geocodingAvailable: boolean; hasKey: boolean;
  onCoordinates: (p: LatLng) => void; onRecord: (r: MapRecord) => void; onPlace: (p: LatLng) => void };

export default function MapSearch({ records, geocodingAvailable, hasKey, onCoordinates, onRecord, onPlace }: Props) {
  const [q, setQ] = useState(""); const [open, setOpen] = useState(false);
  const [places, setPlaces] = useState<PlaceResult[] | null>(null); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const root = useRef<HTMLDivElement>(null);
  const coords = q.trim() ? parseCoordinates(q) : null;
  const term = q.trim().toLocaleLowerCase();
  const matches = term.length >= 2 && !coords ? records.filter(r => [r.title, r.district, r.city].some(v => v?.toLocaleLowerCase().includes(term))).slice(0, 5) : [];
  const plotLike = /\b(plot|parcel|plan|block|قطعة|مخطط)\b/i.test(q);

  useEffect(() => { const close = (e: MouseEvent) => { if (!root.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close); return () => document.removeEventListener("mousedown", close); }, []);
  // Debounced address search while typing (only when Esri geocoding is available).
  useEffect(() => {
    setPlaces(null); setError("");
    if (!geocodingAvailable || coords || term.length < 3) return;
    const key = readProviderConfig().esriKey; if (!key) return;
    const controller = new AbortController();
    const t = setTimeout(() => { setBusy(true);
      esriGeocode(q.trim(), key, controller.signal).then(setPlaces).catch(e => { if ((e as Error).name !== "AbortError") setError((e as Error).message); })
        .finally(() => setBusy(false)); }, 400);
    return () => { clearTimeout(t); controller.abort(); };
  }, [q, term.length, geocodingAvailable]); // eslint-disable-line react-hooks/exhaustive-deps

  const done = () => { setOpen(false); setQ(""); };
  const empty = !coords && !matches.length && !places?.length;
  return <div ref={root} className="relative" onKeyDown={e => { if (e.key === "Escape") setOpen(false); }}>
    <label className="sr-only" htmlFor="map-search">Search coordinates, address or saved records</label>
    <div className="flex h-9 items-center rounded-[10px] bg-black/[0.06] focus-within:bg-black/[0.08]">
      <Search size={16} className="ml-2.5 mr-1.5 shrink-0 text-black/40" aria-hidden />
      <input id="map-search" value={q} onChange={e => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)}
        onKeyDown={e => { if (e.key === "Enter" && coords?.ok) { onCoordinates(coords.value); done(); } }}
        placeholder={geocodingAvailable ? "Search address or coordinates" : "Search coordinates or saved places"} autoComplete="off"
        role="combobox" aria-autocomplete="list" aria-expanded={open && !!q.trim()} aria-controls="map-search-results"
        className="min-w-0 flex-1 bg-transparent text-[15px] text-black/85 outline-none placeholder:text-black/35" />
      {q && <button type="button" aria-label="Clear search" onClick={() => setQ("")} className="mr-2 grid h-4 w-4 place-items-center rounded-full bg-black/25 text-white"><X size={11} strokeWidth={3} /></button>}
    </div>
    {open && q.trim() && <div id="map-search-results" className="absolute z-[1200] mt-2 w-full overflow-hidden rounded-2xl bg-white/95 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.3)] ring-1 ring-black/[0.06] backdrop-blur-xl">
      {coords?.ok && <Result onClick={() => { onCoordinates(coords.value); done(); }} title={coords.value.map(n => n.toFixed(6)).join(", ")} detail={`Drop pin here · latitude, longitude${coords.warning ? ` · ${coords.warning}` : ""}`} />}
      {coords && !coords.ok && <div className="px-4 py-3 text-[13px] text-[#c4271d]">{coords.error}
        {coords.swapped && <button type="button" className="mt-1 block text-[#007AFF]" onClick={() => { onCoordinates(coords.swapped!); done(); }}>Use {coords.swapped.map(n => n.toFixed(6)).join(", ")} instead</button>}</div>}
      {matches.map(r => <Result key={r.id} onClick={() => { onRecord(r); done(); }} dot={LAYER[r.kind].color} title={r.title} detail={`${LAYER[r.kind].short}${r.coordinates ? "" : " · no location"}`} />)}
      {places?.map((p, i) => <Result key={i} onClick={() => { onPlace(p.coordinates); done(); }} title={p.label} detail={`${p.precision.replace(/([a-z])([A-Z])/g, "$1 $2")} · moves the map — then tap to drop the pin`} />)}
      {busy && <p className="px-4 py-3 text-[13px] text-black/45">Searching…</p>}
      {error && <p className="px-4 py-3 text-[13px] text-[#c4271d]">{error}</p>}
      {!busy && empty && !error && <p className="px-4 py-3 text-[13px] text-black/45">{coords ? "" : !hasKey ? "Turn on satellite to search addresses. For now, type coordinates like 24.7136, 46.6753." : term.length < 3 ? "Keep typing…" : "No matches."}</p>}
      {plotLike && <p className="border-t border-black/[0.06] px-4 py-2.5 text-[12px] text-black/45">Plot and plan numbers can’t be looked up yet — no authorised cadastral source is connected.</p>}
    </div>}
  </div>;
}

function Result({ title, detail, onClick, dot }: { title: string; detail: string; onClick: () => void; dot?: string }) {
  return <button type="button" onClick={onClick} className="flex w-full items-start gap-3 border-b border-black/[0.05] px-4 py-2.5 text-left last:border-0 hover:bg-black/[0.03]">
    {dot ? <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: dot }} /> : <MapPin size={16} className="mt-0.5 shrink-0 text-[#FF3B30]" />}
    <span className="min-w-0"><span className="block truncate text-[15px] text-black/85" dir="auto">{title}</span><span className="block text-[12.5px] text-black/45">{detail}</span></span>
  </button>;
}
