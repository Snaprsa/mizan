import type { AnalysisResult } from "@/lib/api";

type Sensitivity = AnalysisResult["outputs"]["sensitivity"];
const sar = new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 });
function axis(value: number, unit: string) {
  return unit === "ratio" ? `${(value * 100).toFixed(2)}%` : sar.format(value);
}
export default function SensitivityTable({ sensitivity: s }: { sensitivity: Sensitivity }) {
  if (!s) return null;
  return <details className="mt-3 text-xs" open>
    <summary className="font-medium cursor-pointer">Sensitivity to key assumptions</summary>
    <p className="text-[11px] text-slate-500 my-2">{s.notice}</p>
    <div className="overflow-x-auto"><table className="w-full border-collapse text-[10px]">
      <caption className="text-left text-slate-500 pb-2">Rows: {s.y.label} · Columns: {s.x.label} · Values in SAR</caption>
      <thead><tr><th scope="col" className="border p-1">{s.y.label}</th>{s.x.values.map((v,i) => <th key={i} scope="col" className="border p-1">{axis(v,s.x.unit)}</th>)}</tr></thead>
      <tbody>{s.cells.map((row,i) => <tr key={i}><th scope="row" className="border p-1">{axis(s.y.values[i],s.y.unit)}</th>{row.map((cell,j) => <td key={j} className={`border p-1 text-right ${i===1 && j===1 ? "bg-blue-50 font-semibold" : ""}`} title={cell.reason || (i===1 && j===1 ? "Saved base case" : "Assumption stress")}>{cell.value == null ? "Outside bounds" : sar.format(cell.value)}</td>)}</tr>)}</tbody>
    </table></div>
  </details>;
}
