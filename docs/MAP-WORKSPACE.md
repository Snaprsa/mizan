# Property intelligence map — 25 October 2026

Open http://127.0.0.1:3100/map or use **Map & Comparables** in the sidebar. Case and property workspaces link to the map; a case link scopes it to that case and linked properties.

## Delivered behavior

- Leaflet/OpenStreetMap basemap beside a synchronized evidence list. Selecting a list record focuses its location; selecting a pin opens its evidence details. Grouped markers show saved record counts and expand into the adjacent list.
- Layers: properties, recorded transactions, asking-price listings, other comparables. Subject properties are not counted as comparable sales.
- City, property-type, text and evidence-date filters. Last 30/90/365 days use the current Saudi date. Dates come from transaction/listing/collection evidence; import time is never used as a substitute for missing dates.
- Current-view record and transaction counts, plus expandable district activity groups. Bounds and counts follow pan/zoom. Optional 'Only records in current map view' filters the adjacent list.
- Google Maps links open exact coordinates where available; unlocated records can search their city/district as an explicitly approximate area search. No Google Maps key is required for these links.
- Unlocated or invalid coordinates are not placed at invented district centroids. Such records remain in the list. Invalid/outlier evidence is excluded by default; drafts remain clearly labelled.
- Evidence details show recorded price, currency, area, price/m², date, source, source reliability and links to the original case/property. Recorded-transaction classification requires an explicit achieved/official/auction evidence type, transacted price and valid transaction date. Listings and unclassified comparables do not inflate completed-transaction counts.
- Map API owner-scopes both properties and case comparables and honors extracted field overrides, including reviewed coordinates.

## Scope and limits

The map shows saved evidence, not all Saudi transactions or a live market feed. Counts are source records rather than deduplicated transactions or properties. At initial implementation only one of the 18 legacy comparables had coordinates. Property and comparable coordinates must be supplied/reviewed before missing records can appear as pins. Data quality issues in old extraction outputs are exposed rather than corrected by guessing.

The endpoint returns up to 5,000 filtered records and explicitly marks truncation. Larger deployments should move filtering/aggregation into spatial queries and server-side clustering. District summaries group recorded district names in the viewport; they are not authoritative municipality boundaries. Heatmaps, parcel polygons, automatic geocoding and Google embedded basemaps are not implemented.

Map tiles are requested directly by the browser and depend on network availability. Tile failures show a notice while retaining evidence and Google links. `NEXT_PUBLIC_MAP_TILE_URL` and `NEXT_PUBLIC_MAP_ATTRIBUTION` can configure a different tile provider at build time; set both according to that provider's licensing. There is no tile prefetch or offline download. A shared/high-volume deployment should configure an appropriate commercial/self-hosted tile service.

Google's full embedded Maps JavaScript API requires a configured Google project/API key (and production billing setup). This release uses documented Google Maps URLs instead, without scraping or unofficial Google tile endpoints.

## Verification

- 5 new map API tests pass; the complete API suite passed with 63 tests before the final source/case consistency guard, and the map tests passed again afterward.
- Tests cover ownership, actual versus asking evidence, unknown/invalid coordinates, source dates versus import dates, date bounds, case/city/type/search filters, explicit truncation and reviewed coordinate overrides.
- Production frontend build and TypeScript/ESLint checks pass.
- Read-only browser checks confirm live saved records, marker selection, Google links, visible-area/date filters, layer toggles and successful basemap loading.
- `docs/verify_map_ui.py` verifies marker groups, list synchronization and missing locations with browser-only fixtures. It intercepts both evidence and tiles; it does not add fake records to the database or download OSM tiles during repeated map interactions.
- Removed a pre-existing direct Linux-only SWC dev dependency that prevented npm installs on this Mac. Next's own platform-specific dependency handling remains in place.

## References

- Google Maps URLs: https://developers.google.com/maps/documentation/urls/get-started
- Google Maps JavaScript setup: https://developers.google.com/maps/documentation/javascript/get-api-key
- Leaflet: https://leafletjs.com/examples/quick-start/
- OSM tile policy: https://operations.osmfoundation.org/policies/tiles/
