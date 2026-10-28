// Screen-space grid clustering shared by every map renderer. Counts always refer to saved records.
import type { LatLng } from "./geo.ts";

export type Projected<T> = { record: T; coordinates: LatLng; x: number; y: number };
export type Cluster<T> = { key: string; records: T[]; center: LatLng; x: number; y: number };

export function clusterProjected<T>(items: Projected<T>[], cellPx = 56): Cluster<T>[] {
  const cells = new Map<string, Projected<T>[]>();
  for (const item of items) {
    if (!Number.isFinite(item.x) || !Number.isFinite(item.y)) continue;
    const key = `${Math.floor(item.x / cellPx)},${Math.floor(item.y / cellPx)}`;
    const cell = cells.get(key); if (cell) cell.push(item); else cells.set(key, [item]);
  }
  return Array.from(cells, ([key, group]) => ({ key, records: group.map(g => g.record),
    center: [group.reduce((s, g) => s + g.coordinates[0], 0) / group.length, group.reduce((s, g) => s + g.coordinates[1], 0) / group.length] as LatLng,
    x: group.reduce((s, g) => s + g.x, 0) / group.length, y: group.reduce((s, g) => s + g.y, 0) / group.length }));
}
