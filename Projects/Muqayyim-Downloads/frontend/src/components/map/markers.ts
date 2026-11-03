import type { MapRecord } from "@/lib/api";
import type { Cluster } from "@/lib/map-clustering";
import { LAYER } from "@/lib/map-evidence";
import type { Subject } from "@/lib/map-workspace-state";

/** One accessible button per record or cluster. Counts are saved records, not market activity. */
export function evidenceMarker(cluster: Cluster<MapRecord>, selectedId: string | null, groupIds: string[], showValues = false): HTMLButtonElement {
  const el = document.createElement("button");
  el.type = "button";
  const single = cluster.records.length === 1 ? cluster.records[0] : null;
  const selected = cluster.records.some(r => r.id === selectedId);
  const grouped = !single && groupIds.length > 0 && cluster.records.every(r => groupIds.includes(r.id));
  const value = single && showValues && single.price_per_sqm != null ? new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(single.price_per_sqm) : null;
  el.className = `mizan-marker${single ? ` mizan-marker--${single.kind}` : " mizan-marker--cluster"}${value ? " mizan-marker--value" : ""}${selected ? " is-selected" : ""}${grouped ? " is-grouped" : ""}`;
  if (single) {
    const layer = LAYER[single.kind];
    const unit = single.price_per_sqm != null ? ` · ${new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(single.price_per_sqm)} ${single.currency}/m²` : "";
    if (value) { const key = document.createElement("span"); key.className = `mizan-key mizan-key--${single.kind}`; el.append(key, value); }
    el.setAttribute("aria-label", `${layer.short}: ${single.title}${unit}${single.location_precision === "source_reported" ? " (location as reported by source)" : ""}`);
    el.title = `${single.title} · ${layer.short}${unit}`;
  } else {
    el.textContent = String(cluster.records.length);
    const sales = cluster.records.filter(r => r.kind === "transaction").length;
    el.setAttribute("aria-label", `${cluster.records.length} saved records, ${sales} achieved sales. Activate to list and zoom.`);
    el.title = `${cluster.records.length} saved records · ${sales} achieved sales`;
  }
  return el;
}

export function subjectMarker(subject: Subject, draggable: boolean): HTMLButtonElement {
  const el = document.createElement("button");
  el.type = "button";
  el.className = `mizan-subject${subject.confirmed ? " is-confirmed" : ""}${draggable ? " is-draggable" : ""}`;
  // The centre of the dot is the exact coordinate.
  el.setAttribute("aria-label", `Subject location ${subject.coordinates.map(n => n.toFixed(6)).join(", ")}${draggable ? ". Drag or use arrow keys to adjust." : ""}`);
  el.title = draggable ? "Subject · drag or use arrow keys to adjust" : "Subject location";
  return el;
}

export function vertexDot(index: number, label: string): HTMLSpanElement {
  const el = document.createElement("span");
  el.className = "mizan-vertex";
  el.setAttribute("aria-hidden", "true");
  el.title = `${label} ${index + 1}`;
  return el;
}

/** Arrow-key nudges in screen pixels; Shift moves further. */
export function arrowDelta(e: KeyboardEvent): [number, number] | null {
  const step = e.shiftKey ? 20 : 4;
  return e.key === "ArrowUp" ? [0, -step] : e.key === "ArrowDown" ? [0, step] : e.key === "ArrowLeft" ? [-step, 0] : e.key === "ArrowRight" ? [step, 0] : null;
}
