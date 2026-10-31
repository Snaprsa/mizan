"use client";
// Map style picker. The key is handled only by Mizan's local API: it is sent once when saved,
// stored encrypted in the Mac's Keychain and never comes back to the browser.
import { useState } from "react";
import { ExternalLink, Lock } from "lucide-react";
import { BASEMAP_LAYERS, imageryTileUrl, readOsmConfig, removeImageryKey, saveImageryKey } from "@/lib/map-provider";
import { BASEMAPS, type Basemap } from "@/lib/map-workspace-state";
import type { MapStatus } from "./types";

// One fixed tile over central Riyadh (z13), used only as a thumbnail.
const THUMB = { z: "13", x: "5158", y: "3515" };
const fill = (url: string) => url.replace("{z}", THUMB.z).replace("{x}", THUMB.x).replace("{y}", THUMB.y);

function Thumb({ layers }: { layers: string[] }) {
  // eslint-disable-next-line @next/next/no-img-element
  return <span className="relative block h-14 overflow-hidden rounded-lg bg-black/[0.05]">{layers.map(src => <img key={src} src={fill(src)} alt="" className="absolute inset-0 h-full w-full object-cover" loading="lazy" />)}</span>;
}

type Props = { basemap: Basemap; status: MapStatus | null; onChoose: (b: Basemap) => void; onKeyChange: (on: boolean) => void };

function KeyForm({ label, onSaved }: { label: string; onSaved: () => void }) {
  const [value, setValue] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  async function save() {
    const key = value.trim(); if (!key) return;
    setBusy(true); setError("");
    try { await saveImageryKey(key); setValue(""); onSaved(); }
    catch (e) { setError((e as Error).name === "TypeError" ? "Couldn’t reach Mizan’s server. Try again." : (e as Error).message); }
    finally { setBusy(false); }
  }
  return <form onSubmit={e => { e.preventDefault(); save(); }} className="space-y-2">
    <input type="password" aria-label="Esri API key" autoComplete="off" spellCheck={false} placeholder="Your Esri API key" value={value} onChange={e => { setValue(e.target.value); setError(""); }} className="mizan-field" />
    {error && <p role="alert" className="text-[12.5px] leading-snug text-[#c4271d]">{error}</p>}
    <button type="submit" disabled={!value.trim() || busy} className="w-full rounded-xl bg-[#007AFF] px-4 py-2.5 text-[15px] font-semibold text-white active:opacity-80 disabled:bg-black/10 disabled:text-black/35">{busy ? "Checking…" : label}</button>
    <p className="flex gap-1.5 text-[11.5px] leading-snug text-black/45"><Lock size={12} className="mt-0.5 shrink-0" />Stored encrypted in this Mac’s Keychain. Never kept in the browser.</p>
  </form>;
}

export default function MapStylePanel({ basemap, status, onChoose, onKeyChange }: Props) {
  const osm = readOsmConfig();
  const caps = status?.capabilities;

  if (status && !status.configured) return <div className="space-y-3">
    <div className="flex items-center gap-3"><div className="w-16 shrink-0"><Thumb layers={[osm.url]} /></div>
      <div><p className="text-[15px] font-semibold text-black/85">See real satellite imagery</p><p className="text-[13px] leading-snug text-black/50">Free with an Esri account. You’re on the standard map for now.</p></div></div>
    <ol className="space-y-2 text-[13.5px] leading-snug text-black/70">
      <li className="flex gap-2"><Step n={1} /><span><a href="https://location.arcgis.com/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[#007AFF]">Open Esri and sign up <ExternalLink size={12} /></a><span className="block text-[12px] text-black/45">Leave pay-as-you-go off.</span></span></li>
      <li className="flex gap-2"><Step n={2} /><span>Create an API key with basemap and geocoding permissions.</span></li>
      <li className="flex gap-2"><Step n={3} /><span>Paste it here:</span></li>
    </ol>
    <KeyForm label="Turn on satellite" onSaved={() => onKeyChange(true)} />
  </div>;

  const thumb = (b: Basemap) => { const l = BASEMAP_LAYERS[b];
    if (b === "roadmap" && status?.provider === "esri" && !status.esri_streets) return [osm.url];
    if (status?.provider !== "esri" || !caps?.[b]) return b === "roadmap" ? [osm.url] : [];
    return [l.base, ...(l.overlay ? [l.overlay] : [])].map(imageryTileUrl); };
  const missing = status?.provider === "esri" && (!caps?.hybrid || !caps?.terrain);
  return <div>
    <div className="grid grid-cols-2 gap-2">{BASEMAPS.map(b => { const ok = !!caps?.[b.key];
      return <button key={b.key} type="button" disabled={!ok} aria-pressed={basemap === b.key && ok} onClick={() => onChoose(b.key)}
        className={`rounded-xl p-1.5 text-left ring-1 ${basemap === b.key && ok ? "bg-[#007AFF]/5 ring-2 ring-[#007AFF]" : "bg-white ring-black/10"} disabled:opacity-40`}>
        <Thumb layers={thumb(b.key)} />
        <span className="mt-1 block px-1 pb-0.5 text-[13px] font-medium text-black/80">{b.key === "roadmap" ? "Standard" : b.label}</span></button>; })}</div>
    {missing && <p className="mt-2 text-[12px] leading-snug text-black/50">Hybrid and Terrain need the “static basemap tiles” permission on your Esri key. Add it in Esri and they’ll turn on here.</p>}
    {status?.message && <p role="alert" className="mt-2 text-[12.5px] leading-snug text-[#c4271d]">{status.message}</p>}
    {status?.imageryNote && <p className="mt-2 text-[11.5px] leading-snug text-black/45">{status.imageryNote}</p>}
    {status?.configured && <details className="mt-2"><summary className="cursor-pointer text-[13px] text-[#007AFF]">Manage key</summary>
      <div className="mt-2 space-y-2"><KeyForm label="Replace key" onSaved={() => onKeyChange(true)} />
        <button type="button" onClick={async () => { await removeImageryKey(); onKeyChange(false); }} className="text-[13px] text-[#FF3B30]">Remove key from this Mac</button></div></details>}
  </div>;
}

function Step({ n }: { n: number }) {
  return <span className="mt-px grid h-5 w-5 shrink-0 place-items-center rounded-full bg-black/[0.06] text-[11.5px] font-semibold text-black/60">{n}</span>;
}
