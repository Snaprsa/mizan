# Prompt for Claude Design (version 2, November 2026)

Attach 5–7 screenshots of the app as it is now before sending: the map with its card, Value a property, the Area on the map section with a traced plot, the comparable adjustments screen (with one sale opened), a valuation result, and the Monitor overview.

```text
This is the second design pass for Mizan (ميزان), a Saudi real-estate valuation and portfolio-monitoring platform. I've attached screenshots of the app as it is now, already built from your first pass. Keep what works (the full-screen map, one card, calm type, shape-coded evidence pins) and take it further on three things:

1. The comparable adjustment screen. This is the core of a valuer's work, and it still feels like a form. Make it feel like a professional sales comparison grid that is still simple.
2. Smoothness. Every change on screen should feel continuous and quiet, like Apple Maps or Stocks: nothing jumps, flashes or reflows.
3. The whole product, updated to what it now does (listed below).

Make it calmer, clearer and more premium, never busier. Think Apple Maps, Stocks and Wallet, not an enterprise dashboard.

WHO USES IT
Valuers, asset managers and fund managers in Saudi Arabia. They want the answer first ("what is it worth, why, what needs my attention") and the detail only when they ask.

RULES THAT DO NOT CHANGE
1. Simplicity first. One thing at a time. Progressive disclosure: answer, then why, then evidence, then audit trail.
2. The map is the home screen: full-screen, with ONE card on top (a sidebar card on desktop, a draggable bottom sheet on phones). No second panel, no nav clutter on the map.
3. Few controls, generous spacing, large clear numbers, quiet secondary text. No gradients, no glassy "AI" look, no decorative charts, no icon soup.
4. Honest data is part of the design. Each important number shows its origin with a small label (REAL DATA, DEMO DATA, USER PROVIDED, MEASURED ON MAP, DERIVED, ESTIMATED). Missing values show "—", never 0. Confidence is High / Medium / Low with reasons one tap away, never a percentage. The "middle half" range is not called a confidence interval. Mizan never suggests adjustment rates: the valuer sets them, with a basis.
5. Money in SAR, compact (SAR 5.63bn, SAR 53.2m, SAR 840k); unit values as SAR/m². Signs explicit (+3.0%, −11.2%), and colour never carries meaning alone.
6. English and Arabic (RTL), light and dark, down to a 375px phone.

WHAT THE APP DOES NOW (design all of it)
A. Map, Explore. Satellite map. Pins are shape-coded: circle = achieved sale, diamond = listing, blue square = my property, rounded square = market data, dashed ring = other. Clusters; value labels appear when zoomed in. The card has an Explore | Monitor switch, search, counts per evidence type that filter the map, and one primary action: "Value a property".
B. Value a property, as a short guided flow in the same card with step progress: drop the pin (or type coordinates) → property type → method → type-specific details (apartment: floor and position; office: grade and floor; land: street width and corner) → area → required inputs, each with source and date → Calculate.
C. Area from the map. For buildings, Mizan looks up the building outline from OpenStreetMap and shows it dashed, with its area and floors, as a suggestion to accept. For land, there is no free plot source, so the valuer traces the plot by tapping corners. The area fills the valuation automatically and updates when the outline changes. The valuer can drag corners ("Adjust corners"), trace again, or type their own figure ("entered by you, replacing the measured 10,654 m²", with "Use measured" to go back). Design this as one small, elegant section: the outline on the map, the number, the origin label, three quiet actions. Also design the loading state (outline lookup can take up to 30 seconds), "no building mapped here" and "service busy, trace it yourself".
D. Comparable adjustments (the main focus, see the detailed brief below).
E. Valuation result: value and range in large type, the concluded SAR/m², the sales that support it, the method, and saved history with revisions.
F. Monitor: portfolio overview (value against official valuation, "7 assets need attention", rising / stable / falling, value-over-time chart with 1M 3M 6M 1Y 3Y All, NAV, debt, LTV, NOI, cap rate, occupancy, sector and city breakdowns), one asset (value against official, range, confidence grade with reasons, alerts with Accept / Investigate, "why it changed" as signed bars per driver, history with the official line, comparable sales marked NEW, assumptions adjustable only with a reason, collapsed audit trail), the assets table and bubble chart, and the "Revalue first" list with reasons. Demo funds are clearly labelled DEMO.

D. COMPARABLE ADJUSTMENTS: DETAILED BRIEF
What it is today (see screenshot): a summary card ("Concluded unit value", SAR/m², property value, middle half, "median of 12 sales · 1 excluded", a folded statistics table before/after: median, mean, weighted median, middle half, spread); a "Compare to this property" card with one % rate per factor (location, street width, corner, floor, position, grade, area, age), each showing the subject's value and an optional basis; a "Sales" list where each row shows the title, date, distance, area, its details, the adjusted SAR/m² and the unadjusted value with the % change, and opens to edit the sale's details, see applied steps, add an adjustment for that sale only (factor, unit % / SAR per m² / SAR total, amount, reason required, source, Apply switch), set a manual weight, or exclude it with a reason; a folded "Time and weighting" section (market change per year with required basis and date; weighting equal / less-adjusted-count-more / manual with rationale; conclude on median / mean / weighted median / weighted mean); a sticky Save bar that appears only with unsaved changes (Discard, Save).

What I want:
1. A real comparison grid, without the clutter. On desktop, show sales as columns next to the subject (Subject | Sale 1 | Sale 2 | ...), with rows for price per m², each factor (the detail, then the adjustment), net and gross adjustment, and the adjusted SAR/m². It must read at a glance. Show a calm list on phones, with the grid one swipe or tap away. Decide what can stay hidden and show me.
2. Show the adjustment as it happens. When I type a rate, every sale's adjusted value and the conclusion update in place with a soft number transition, and a small marker shows what moved. I should see "before → after" without opening anything.
3. Visualise the spread simply: one horizontal strip of dots showing each sale's SAR/m² before (hollow) and after (filled) adjustment, with the concluded value as a line and the middle half shaded. Tapping a dot highlights the sale in the list and on the map.
4. Make heavily adjusted sales obvious: gross adjustment shown per sale, with a quiet caution when a sale needs a lot of adjustment (for example over 25% gross), as text and an icon, not just colour.
5. Excluding and including again should feel light: swipe or a menu, a reason sheet, and the row folds into an "Excluded (2)" group with its reason visible.
6. Editing a sale's missing details (for example "street width not set") should be inline, right where the gap shows, not in a separate form.
7. Per-sale adjustments that replace a factor's rate should be visibly marked on that cell ("override: +5%, reason").
8. Keep the honest rules: rates come from the valuer with a basis; Mizan explains its conventions in a folded "How adjustments are applied"; saving creates a revision, so show "Saved as revision 4" afterwards.
9. Design the states: no sales yet, sales missing details, subject area missing ("measure it on the map" links to section C), validation errors written as sentences next to the field, saving, saved, and a stale-result warning when the evidence changed.

SMOOTHNESS (motion spec I want you to define)
- Card and bottom sheet: spring-like but subtle movement between steps; content cross-fades, height animates instead of jumping. The sheet keeps three snap heights on phones.
- Numbers: values that change count or cross-fade over about 200 ms; never flash.
- Lists: rows expand and collapse with height animation; excluded rows slide into their group.
- Map: fly-to when selecting a pin or sale; the selected pin grows slightly; the outline draws in.
- Loading: skeletons shaped like the final content, no spinners in the middle of cards; long lookups show a quiet line of progress text.
- Everything 150–300 ms with standard easing, and all of it switched off with "reduce motion".
Give exact durations, easing curves and which properties animate (transform and opacity only where possible), so it can be built in CSS.

ALSO DESIGN
- Empty, loading, error and missing-data states for every screen.
- Alert severity (info, watch, warning, critical) with icon and word.
- An updated design system page: colour tokens light and dark (current: accent #0071E3, accent text #0062C4, text #1D1D1F, secondary #5F5F64, positive #17722F, negative #C0271B, caution #8A5200), type scale with tabular numbers, spacing, radius, elevation, the motion tokens, and the components (card, list row, comparison grid cell, segmented control, switch, compact input, button, badge, origin label, stat, dot strip, chart styles, bottom sheet, sticky save bar).

BUILD CONSTRAINTS
Next.js, React, Tailwind and Lucide icons; Leaflet with Esri satellite imagery. System fonts (SF Pro / Inter-like, plus IBM Plex Sans Arabic). No paid services, no 3D maps, no animation libraries beyond CSS transitions. Must stay fast with 100+ sales on the map and 30 in the grid.

EXAMPLE CONTENT
Use clearly fictional names and numbers in Riyadh, Jeddah, Khobar and Dammam (for example "DEMO · Land plot, Al Narjis, 1,250 m², SAR 4,800/m², 2.1 km"), so nothing looks like real market data.

DELIVERABLE
High-fidelity desktop and phone screens for A–F, with D in the most depth (grid, list, dot strip, editing, excluding, states), the motion spec, the design-system page, and short notes on what you removed or simplified and why.
```
