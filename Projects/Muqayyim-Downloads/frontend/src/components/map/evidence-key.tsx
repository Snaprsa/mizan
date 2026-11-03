// The list and legend counterpart of a map marker: same shape, so colour never carries the meaning alone.
import type { MapRecord } from "@/lib/api";

export default function EvidenceKey({ kind }: { kind: MapRecord["kind"] }) {
  return <span aria-hidden className={`mizan-key mizan-key--${kind}`} />;
}
