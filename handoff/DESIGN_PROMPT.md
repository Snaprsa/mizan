# Prompt for Claude Design

Attach 4–6 screenshots of the current app (map, Value a property, a valuation result, Monitor overview, an asset page) before sending.

```text
Redesign the interface of Mizan (ميزان), a Saudi real-estate valuation and portfolio-monitoring platform. I've attached screenshots of what exists today. Make it look dramatically better, calmer and more premium, while keeping it as simple as it is now, or simpler. Think of how Apple would design professional software: Apple Maps, Stocks and Wallet, not a crowded enterprise dashboard.

WHO USES IT
Valuers, asset managers and fund managers in Saudi Arabia. They want an answer first ("what is it worth, what changed, what needs my attention") and the detail only when they ask for it.

WHAT MUST NOT CHANGE (my rules)
1. Simplicity first. One thing at a time. Progressive disclosure: answer, then why, then evidence, then audit trail. Never show everything at once.
2. The map is the home screen. It is full-screen, with ONE floating card on top: a sidebar-style card on desktop, a draggable bottom sheet on phones. No second panel, no permanent left-nav clutter on the map.
3. Few controls, generous spacing, large clear numbers, quiet secondary text. No gradients, no glassy "AI" sparkle, no decorative charts, no icon soup.
4. Honest data is part of the design. Every important number shows where it came from with a small label: REAL DATA, DEMO DATA, USER PROVIDED, DERIVED or ESTIMATED. Missing values show "—", never 0. Confidence is High / Medium / Low with the reasons one tap away, never a fake percentage. Ranges are not called confidence intervals. Demo data is always clearly marked.
5. Money is in SAR, compact: SAR 5.63bn, SAR 53.2m, SAR 840k. Signs are explicit (+3.1%, −11.2%), and colour never carries meaning on its own.
6. It must work in English and Arabic (RTL), in light and dark mode, and down to a 375px phone.

SCREENS TO DESIGN (high fidelity, desktop and phone)
A. Map: Explore. A satellite map with evidence pins (achieved sales, listings, my properties) and clusters. The card shows search, a simple list of nearby evidence with counts, and one clear primary action: "Value a property".
B. Value a property, as a short guided flow inside the same card: drop the pin → property type → method → the details that matter for that type (apartment: floor and position in the building; office: assumed grade and floor; land: street width and corner) → required inputs, each showing its source and date → Calculate.
C. Valuation result: the value and range in large type, then "Compare to this property" (one adjustment rate per factor), the comparable sales with their adjustments, and the saved history. Dense information must stay calm and readable.
D. Monitor: portfolio overview. Hero: portfolio value, change against the official valuation, and a single "7 assets need attention" button. Below it: rising / stable / falling counts, a value-over-time chart with period buttons (1M 3M 6M 1Y 3Y All), and fund figures (NAV, debt, LTV, NOI, cap rate, occupancy). Small sector and geography breakdowns.
E. Monitor: one asset. Current value against official, range, confidence. Alerts with Accept / Investigate. "Why it changed" as signed bars per driver (comparable sales, occupancy, cap rate, rent...). Value history with the official line. Methods and the reconciled value. Comparable sales marked NEW. Assumptions with an "Adjust" action that requires a reason. An audit trail that stays collapsed by default.
F. Monitor: the assets list as a table, and as a bubble chart (value against change since official). Plus the "Revalue first" list, where each asset shows the reasons it is there.

ALSO DESIGN
- Empty, loading, error and "missing data" states for each screen. These matter as much as the full states.
- Alert severity styling (info, watch, warning, critical) with icon and word, not colour alone.
- A small design system: colour tokens for light and dark, type scale, spacing, radius, elevation, and the components (card, list row, segmented control, button, badge, data label, stat, chart styles, bottom sheet).

CONSTRAINTS SO IT CAN BE BUILT
It will be built in Next.js, React, Tailwind and Lucide icons, with a Leaflet map using Esri satellite imagery. Use system fonts (SF Pro / Inter-like, plus an Arabic face such as IBM Plex Sans Arabic). No paid services, no 3D maps, no heavy animation: subtle transitions only. Keep the current accent close to Apple blue (#007AFF) unless you have a clearly better reason.

EXAMPLE CONTENT
Use clearly fictional names and numbers set in Riyadh, Jeddah, Khobar and Dammam (for example "DEMO · Asset 016, Jeddah logistics, SAR 27.0m, −20.1% against official"), so nothing looks like real market data.

DELIVERABLE
High-fidelity screens for A–F on desktop and phone, the states above, the design-system page, and short notes on what you simplified and why. If anything in the current screenshots adds clutter without helping the user decide, remove it and tell me.
```
