# Prompt for synthetic demo comparables

Paste this into ChatGPT. Paste the JSON it returns into Mizan under **Explore → Data → Demo comparables → Import**.
Every imported record is labelled DEMO and valuations using them say so. **Remove all demo data** deletes them.

---

Create made-up real-estate comparables for testing software. They are fictional and must not copy real transactions, buildings or people.

Return ONLY a valid JSON array of 60 objects, with no explanation. Every object must follow this format exactly:

{
  "title": "Short fictional description",
  "property_type": "apartment",
  "evidence_type": "transaction_achieved",
  "price_sar": 1250000,
  "area_sqm": 160,
  "date": "2026-08-14",
  "latitude": 24.7136,
  "longitude": 46.6753,
  "district": "Al Olaya",
  "attributes": { "floor": 4, "position": "front" }
}

Rules:
- Mix: 20 "apartment", 20 "office", 15 "land", 5 "villa".
- In each type, about 80% "evidence_type": "transaction_achieved" (achieved sale) and 20% "listing_asking" (asking price).
- "price_sar" is the TOTAL price in Saudi riyals, a plain number. "area_sqm" is the area in square metres.
- Plausible total price ÷ area: apartment 5,000–11,000 SAR/m², office 7,000–16,000, land 4,000–15,000, villa 4,000–9,000. Vary them, and make better floors, grades and wider streets tend to cost more so that adjustments are visible.
- "date" is YYYY-MM-DD, between 2025-11-15 and 2026-10-25.
- Location: central Riyadh, Saudi Arabia, within 3 km of latitude 24.7136, longitude 46.6753. "latitude" is about 24.69–24.74 and "longitude" is about 46.65–46.70. Never swap them. Spread them out, avoid repeating a coordinate, and use real district names such as Al Olaya, Al Sulimaniyah, Al Wurud, Al Murooj, Al Malaz or King Fahd.
- "attributes" depends on the type. Use only these keys and values:
  - apartment: "floor" (whole number 0–25), "position" ("rear", "side", "front" or "corner")
  - office: "grade" ("A+", "A", "B" or "C"), "floor" (whole number 0–40)
  - land: "street_width_m" (number 10–60), "corner" (true or false)
  - villa: {}
- Leave "floor", "position" or "grade" out of about 5 records so that missing data can be tested.
- Each title must be unique. Do not start titles with "DEMO" and do not add any other keys.
