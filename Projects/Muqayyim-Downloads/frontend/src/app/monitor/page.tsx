"use client";
// Monitor's front door: your portfolios, or the two ways to start.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ChevronRight, Plus } from "lucide-react";
import { createDemoPortfolio, createPortfolio, errorText, listPortfolios, pct, removeDemoPortfolio, sar } from "@/lib/monitor";
import { Button, Field, Movement, OriginBadge, inputClass } from "@/components/monitor/ui";

type Row = Awaited<ReturnType<typeof listPortfolios>>[number];

export default function MonitorHome() {
  const router = useRouter();
  const [rows, setRows] = useState<Row[] | null>(null); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const [adding, setAdding] = useState(false);
  const load = useCallback(() => listPortfolios().then(setRows).catch(e => setError(errorText(e))), []);
  useEffect(() => { load(); }, [load]);
  const demo = rows?.find(r => r.is_demo);
  const addDemo = async () => { setBusy(true); setError(""); try { const p = await createDemoPortfolio(); router.push(`/monitor/${p.id}`); } catch (e) { setError(errorText(e)); setBusy(false); } };
  const dropDemo = async () => { if (!window.confirm("Remove the demo fund and all its demo properties, sales and valuations? Your real records are not touched.")) return;
    setBusy(true); setError(""); try { await removeDemoPortfolio(); await load(); } catch (e) { setError(errorText(e)); } setBusy(false); };
  const create = async (e: FormEvent<HTMLFormElement>) => { e.preventDefault(); const f = new FormData(e.currentTarget); setBusy(true); setError("");
    try { const p = await createPortfolio({ name: String(f.get("name")), owner_entity: String(f.get("owner") || "") || undefined, fund: String(f.get("fund") || "") || undefined, asset_manager: String(f.get("manager") || "") || undefined }); router.push(`/monitor/${p.id}`); }
    catch (err) { setError(errorText(err)); setBusy(false); } };
  return <div>
    <div className="mb-6 flex items-start justify-between gap-4">
      <div><h1 className="text-[28px] font-semibold tracking-tight">Monitor</h1>
        <p className="mt-0.5 max-w-xl text-[14px] text-black/50">What your portfolio is worth now, what changed since the last valuation, why, and what needs your attention.</p></div>
      <Button tone="primary" onClick={() => setAdding(a => !a)}><Plus size={15} />New portfolio</Button>
    </div>
    {error && <p className="mb-4 rounded-xl bg-[#FF3B30]/10 px-4 py-2.5 text-[13px] text-[#c4271d]">{error}</p>}
    {adding && <form onSubmit={create} className="mb-5 grid gap-3 rounded-2xl bg-white p-4 ring-1 ring-black/[0.05] sm:grid-cols-2">
      <Field label="Portfolio name"><input name="name" required maxLength={255} className={inputClass} autoFocus /></Field>
      <Field label="Owner or entity (optional)"><input name="owner" className={inputClass} /></Field>
      <Field label="Fund (optional)"><input name="fund" className={inputClass} /></Field>
      <Field label="Asset manager (optional)"><input name="manager" className={inputClass} /></Field>
      <div className="sm:col-span-2"><Button type="submit" tone="primary" disabled={busy}>Create</Button></div>
    </form>}
    {rows === null ? <p className="py-12 text-center text-[14px] text-black/40">Loading…</p> : <>
      {rows.length > 0 && <div className="mb-5 divide-y divide-black/[0.06] overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.05]">
        {rows.map(r => <Link key={r.id} href={`/monitor/${r.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-black/[0.02]">
          <div className="min-w-0 flex-1"><div className="flex items-center gap-2"><span className="truncate text-[15px] font-medium text-black/85" dir="auto">{r.name}</span>{r.is_demo && <OriginBadge origin="demo" />}</div>
            <div className="text-[12.5px] text-black/45">{r.asset_count} {r.asset_count === 1 ? "asset" : "assets"}</div></div>
          <div className="text-right"><div className="text-[15px] font-semibold tabular-nums text-black/85">{r.asset_count ? sar(r.value) : "—"}</div><div className="text-[12.5px] tabular-nums"><Movement value={r.change_pct}>{r.change_pct != null ? `${pct(r.change_pct)} vs official` : ""}</Movement></div></div>
          <ChevronRight size={16} className="text-black/25" />
        </Link>)}
      </div>}
      {rows.length === 0 && !adding && <div className="rounded-2xl bg-white px-6 py-10 text-center ring-1 ring-black/[0.05]">
        <h2 className="text-[17px] font-semibold text-black/85">No portfolios yet</h2>
        <p className="mx-auto mt-1 max-w-md text-[14px] text-black/50">Create one from the properties you have already valued, or explore a made-up fund to see how Monitor works.</p></div>}
      <div className="mt-4 flex flex-wrap items-center gap-3 px-1 text-[13px] text-black/50">
        {demo ? <Button tone="danger" disabled={busy} onClick={dropDemo}>Remove demo fund</Button> : <><Button disabled={busy} onClick={addDemo}>{busy ? "Building the demo fund…" : "Explore a demo fund"}</Button><span>72 made-up assets, clearly labelled and removable in one click.</span></>}
      </div>
    </>}
  </div>;
}
