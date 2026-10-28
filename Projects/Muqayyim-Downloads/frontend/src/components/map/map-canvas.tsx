"use client";
// Chooses the imagery provider. A Google failure falls back to the labelled road map without
// remounting the workspace, so selections, geometry and unsaved valuation inputs are kept.
import { useCallback, useMemo, useState, type MutableRefObject } from "react";
import { readProviderConfig } from "@/lib/map-provider";
import GoogleRenderer from "./google-renderer";
import LeafletRenderer from "./leaflet-renderer";
import type { MapStatus, RendererHandle, RendererProps } from "./types";

export type CanvasProps = Omit<RendererProps, "onStatus"> & {
  handle: MutableRefObject<RendererHandle | null>;
  onStatus: (status: MapStatus & { fallbackReason: string | null }) => void;
};

export default function MapCanvas({ handle, onStatus, ...props }: CanvasProps) {
  const config = useMemo(readProviderConfig, []);
  const [googleError, setGoogleError] = useState<string | null>(null);
  const useGoogle = !!config.googleKey && config.requested === "google" && !googleError;
  const fallbackReason = useGoogle ? null : googleError ? `Google Maps failed: ${googleError}` : config.googleBlocker;
  const report = useCallback((s: MapStatus) => {
    if (s.provider === "google" && s.state === "error") { setGoogleError(s.message || "unknown error"); return; }
    onStatus({ ...s, fallbackReason });
  }, [onStatus, fallbackReason]);
  return useGoogle
    ? <GoogleRenderer key="google" ref={handle} {...props} apiKey={config.googleKey!} mapId={config.googleMapId} onStatus={report} />
    : <LeafletRenderer key="leaflet" ref={handle} {...props} tileUrl={config.fallbackTileUrl} attribution={config.fallbackAttribution} onStatus={report} />;
}
