"use client";
// Map style picker. With no key it offers one clear path: get a free Esri key and paste it here.
import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { esriAvailableStyles, esriTileUrl, ESRI_STYLES, readProviderConfig, storeEsriKey } from "@/lib/map-provider";
import { BASEMAPS, type Basemap } from "@/lib/map-workspace-state";
import type { MapStatus } from "./types";

// One fixed tile over central Riyadh (z13), used only as a thumbnail.
const THUMB = { z: "13", x: "5158", y: "3515" };
const fill = (url: string) => url.replace("{z}", THUMB.z).replace("{x}", THUMB.x).replace("{y}", THUMB.y);

function Thumb({ basemap, esriKey, osmUrl }: { basemap: Basemap; esriKey: string | null; osmUrl: string }) {
  const style = ESRI_STYLES[basemap];
  const layers = esriKey ? [style.base, ...(style.overlay ? [style.overlay] : [])].map(s => fill(esriTileUrl(s, esriKey))) : [fill(osmUrl)];
  // eslint-disable-next-line @next/next/no-img-element
  return <span className="relative block h-14 overflow-hidden rounded-lg bg-black/[0.05]">{layers.map(src => <img key={src} src={src} alt="" className="absolute inset-0 h-full w-full object-cover" loading="lazy" />)}</span>;
}

type Props = { basemap: Basemap; status: MapStatus | null; onChoose: (b: Basemap) => void; onKeyChange: (key: string | null) => void };

export default function MapStylePanel({ basemap, status, onChoose, onKeyChange }: Props) {
  const config = readProviderConfig();
  const [value, setValue] = useState(""); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const caps = status?.capabilities;

  async function turnOn() {
    const key = value.trim(); if (!key) return;
    setBusy(true); setError("");
    try { await esriAvailableStyles(key); storeEsriKey(key); setValue(""); onKeyChange(key); }
    catch (e) { setError((e as Error).name === "TypeError" ? "Couldn’t reach Esri. Check your connection and try again." : (e as Error).message); }
    finally { setBusy(false); }
  }
  function remove() { storeEsriKey(null); onKeyChange(null); }

  if (!config.esriKey) return <div className="space-y-3">
    <div className="flex items-center gap-3"><div className="w-16 shrink-0"><Thumb basemap="roadmap" esriKey={null} osmUrl={config.osmUrl} /></div>
      <div><p className="text-[15px] font-semibold text-black/85">See real satellite imagery</p><p className="text-[13px] leading-snug text-black/50">Free with an Esri account. You’re on the standard map for now.</p></div></div>
    <ol className="space-y-2 text-[13.5px] leading-snug text-black/70">
      <li className="flex gap-2"><Step n={1} /><span><a href="https://location.arcgis.com/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[#007AFF]">Open Esri and sign up <ExternalLink size={12} /></a><span className="block text-[12px] text-black/45">Leave pay-as-you-go off, so nothing can be charged.</span></span></li>
      <li className="flex gap-2"><Step n={2} /><span>Create an API key with the <b className="font-medium">Basemaps</b> and <b className="font-medium">Geocoding</b> permissions.</span></li>
      <li className="flex gap-2"><Step n={3} /><span>Paste it here:</span></li>
    </ol>
    <form onSubmit={e => { e.preventDefault(); turnOn(); }} className="space-y-2">
      <input type="password" aria-label="Esri API key" autoComplete="off" spellCheck={false} placeholder="Your Esri API key" value={value} onChange={e => { setValue(e.target.value); setError(""); }} className="mizan-field" />
      {error && <p role="alert" className="text-[12.5px] leading-snug text-[#c4271d]">{error}</p>}
      <button type="submit" disabled={!value.trim() || busy} className="w-full rounded-xl bg-[#007AFF] px-4 py-2.5 text-[15px] font-semibold text-white active:opacity-80 disabled:bg-black/10 disabled:text-black/35">{busy ? "Checking…" : "Turn on satellite"}</button>
      <p className="text-[11.5px] leading-snug text-black/40">Saved only in this browser. If you restrict the key, allow <code>http://127.0.0.1:3100/*</code>.</p>
    </form>
    {status?.message && status.message !== "No free Esri key configured" && <p role="alert" className="text-[12.5px] leading-snug text-[#c4271d]">{status.message}</p>}
  </div>;

  return <div>
    <div className="grid grid-cols-2 gap-2">{BASEMAPS.map(b => { const ok = status?.provider === "esri" && !!caps?.[b.key];
      return <button key={b.key} type="button" disabled={!ok} aria-pressed={basemap === b.key && ok} onClick={() => onChoose(b.key)}
        className={`rounded-xl p-1.5 text-left ring-1 ${basemap === b.key && ok ? "bg-[#007AFF]/5 ring-2 ring-[#007AFF]" : "bg-white ring-black/10"} disabled:opacity-40`}>
        <Thumb basemap={b.key} esriKey={config.esriKey} osmUrl={config.osmUrl} />
        <span className="mt-1 block px-1 pb-0.5 text-[13px] font-medium text-black/80">{b.key === "roadmap" ? "Standard" : b.label}</span></button>; })}</div>
    {status?.message && status.provider === "osm" && <p role="alert" className="mt-2 text-[12.5px] leading-snug text-[#c4271d]">{status.message}</p>}
    <p className="mt-2 text-[11.5px] leading-snug text-black/45">{status?.imageryNote || "Connecting to Esri…"}</p>
    {config.keySource === "browser" && <button type="button" onClick={remove} className="mt-2 text-[13px] text-[#FF3B30]">Remove key from this browser</button>}
  </div>;
}

function Step({ n }: { n: number }) {
  return <span className="mt-px grid h-5 w-5 shrink-0 place-items-center rounded-full bg-black/[0.06] text-[11.5px] font-semibold text-black/60">{n}</span>;
}
