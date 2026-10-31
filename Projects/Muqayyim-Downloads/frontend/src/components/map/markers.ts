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
  el.className = `mizan-marker${single ? "" : " mizan-marker--cluster"}${value ? " mizan-marker--value" : ""}${selected ? " is-selected" : ""}${grouped ? " is-grouped" : ""}`;
  if (single) {
    const layer = LAYER[single.kind];
    const unit = single.price_per_sqm != null ? ` · ${new Intl.NumberFormat("en-SA", { maximumFractionDigits: 0 }).format(single.price_per_sqm)} ${single.currency}/m²` : "";
    el.style.background = layer.color;
    if (value) el.textContent = value;
    el.setAttribute("aria-label", `${layer.short}: ${single.title}${unit}${single.location_precision === "source_reported" ? " (location as reported by source)" : ""}`);
    el.title = `${single.title} · ${layer.short}${unit}`;
  } else {
    const kinds = new Set(cluster.records.map(r => r.kind));
    el.style.background = kinds.size === 1 ? LAYER[cluster.records[0].kind].color : "#1c1c1e";
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
  // The tip of the pin marks the exact coordinate.
  el.innerHTML = '<svg viewBox="0 0 34 44" width="34" height="44" aria-hidden="true"><path d="M17 1C8.2 1 1 8.1 1 16.9 1 28.6 17 43 17 43s16-14.4 16-26.1C33 8.1 25.8 1 17 1z" fill="#FF3B30" stroke="#fff" stroke-width="2"/><circle cx="17" cy="16.5" r="5.5" fill="#fff"/></svg>';
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
