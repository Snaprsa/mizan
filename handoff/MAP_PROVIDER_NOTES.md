# Map-provider notes — checked 28 October 2026

These are implementation inputs for the requested upgrade, not features already enabled in Mizan. Recheck current official documentation before writing SDK-specific code.

## Primary candidate: Google Maps JavaScript API

Google documents roadmap, satellite, hybrid and terrain basemaps. Production setup requires an appropriate API key and billing-enabled project. Restrict browser keys to intended websites/APIs and keep server keys separate. Do not assume Places/geocoding/3D use is enabled by a map key alone or quote a fixed price without checking current product/SKU terms.

- [Map types](https://developers.google.com/maps/documentation/javascript/maptypes)
- [API key and project setup](https://developers.google.com/maps/documentation/javascript/get-api-key)
- [Usage and billing](https://developers.google.com/maps/documentation/javascript/usage-and-billing)

The older Drawing Library and automatic raster 45-degree imagery were retired in May 2026. Use current supported interaction/drawing tooling; do not copy old DrawingManager examples. Modern vector-camera controls and photorealistic 3D maps are separate capabilities that need their own verification.

- [Deprecations](https://developers.google.com/maps/deprecations)
- [3D coverage](https://developers.google.com/maps/documentation/javascript/3d/coverage)

3D terrain and photorealistic surface/building coverage are different. Check the provider's coverage for the actual Saudi location. Historical imagery, exact capture timestamps and every possible 3D feature are not blanket promises of a satellite map.

## Alternative renderer: MapLibre GL JS

MapLibre documents raster satellite sources. It is a renderer, not a guarantee of free imagery or any particular data coverage. An imagery/terrain source still needs suitable access, attribution and licensing. If selected, implement a licensed provider with known terms and an intentional design decision.

- [Satellite raster example](https://maplibre.org/maplibre-gl-js/docs/examples/display-a-satellite-map/)
- [Source specification](https://maplibre.org/maplibre-style-spec/sources/)

## Proposed configuration boundary

Use a typed provider configuration and document exact required names when implemented. Suggested placeholders are supplied in `handoff/templates/frontend-imagery.env.example`. Those names are proposed for the upgrade; they are not currently consumed by the existing Leaflet screen.

A provider/key failure should leave evidence lists, saved work and settings accessible. A road-map fallback must be labelled as such and cannot be reported as completed satellite imagery. Automated tests may stub tiles; at least one real authorized imagery view must be verified separately before declaring the provider integration working.
