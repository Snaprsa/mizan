"use client";
import { PropertyInput } from "@/lib/api";

type Section = "location" | "land" | "planning" | "building" | "financial" | "provenance";
type FieldType = "text" | "number" | "ratio" | "boolean" | "list" | "date" | "url";
const fields: Record<Section, [string, string, FieldType][]> = {
  location: [["address", "Address", "text"], ["city", "City", "text"], ["district", "District", "text"], ["municipality", "Municipality", "text"], ["latitude", "Latitude", "number"], ["longitude", "Longitude", "number"], ["plot_number", "Plot number", "text"], ["block_number", "Block number", "text"], ["plan_number", "Plan number", "text"]],
  land: [["area_sqm", "Land area (m²)", "number"], ["width_m", "Width (m)", "number"], ["depth_m", "Depth (m)", "number"], ["frontage_m", "Frontage (m)", "number"], ["street_width_m", "Street width (m)", "number"], ["street_frontages", "Street frontages", "number"], ["corner", "Corner plot", "boolean"], ["shape", "Shape", "text"], ["topography", "Topography", "text"], ["orientation", "Orientation", "text"], ["utilities", "Utilities (comma separated)", "list"]],
  planning: [["land_use", "Land use", "text"], ["permitted_use", "Permitted uses (comma separated)", "list"], ["far", "FAR", "number"], ["coverage_ratio", "Coverage (0–1)", "ratio"], ["height_limit_m", "Height limit (m)", "number"], ["parking_requirements", "Parking requirements", "text"], ["restrictions", "Restrictions (comma separated)", "list"]],
  building: [["built_up_area_sqm", "Built-up area (m²)", "number"], ["gfa_sqm", "GFA (m²)", "number"], ["gla_sqm", "GLA (m²)", "number"], ["nla_sqm", "NLA (m²)", "number"], ["floors", "Floors", "number"], ["units", "Units", "number"], ["year_built", "Year built", "number"], ["age_years", "Age (years)", "number"], ["condition", "Condition", "text"], ["occupancy_ratio", "Occupancy (0–1)", "ratio"], ["current_use", "Current use", "text"]],
  financial: [["asking_price_sar", "Asking price (SAR)", "number"], ["purchase_price_sar", "Purchase price (SAR)", "number"], ["annual_rent_sar", "Annual rent (SAR)", "number"], ["rent_sar_sqm_year", "Rent (SAR/m²/year)", "number"], ["operating_expenses_sar_year", "Operating expenses (SAR/year)", "number"], ["noi_sar_year", "NOI (SAR/year)", "number"]],
  provenance: [["source", "Source", "text"], ["source_url", "Property / source URL", "url"], ["collected_on", "Date collected", "date"], ["confidence", "Data confidence (0–100)", "number"], ["notes", "Notes", "text"]],
};
export function PropertyEditor({ value, onChange }: { value: PropertyInput; onChange: (p: PropertyInput) => void }) {
  function change(section: Section, key: string, type: FieldType, raw: string) {
    const v = type === "list" ? raw.split(",").map(s => s.trim()).filter(Boolean)
      : raw === "" ? null : type === "boolean" ? raw === "true" : type === "number" || type === "ratio" ? Number(raw) : raw;
    onChange({ ...value, [section]: { ...value[section], [key]: v } });
  }
  return <div className="space-y-4">
    <div className="grid md:grid-cols-3 gap-4">
      <label className="mizan-label">Property name<input className="mizan-input" value={value.name} required maxLength={255} onChange={e => onChange({ ...value, name: e.target.value })} /></label>
      <label className="mizan-label">Property type<input className="mizan-input" value={value.property_type || ""} onChange={e => onChange({ ...value, property_type: e.target.value || null })} placeholder="Land, apartment, office…" /></label>
      <label className="mizan-label">Preferred locale<select aria-label="Preferred locale" className="mizan-input" value={value.locale} onChange={e => onChange({ ...value, locale: e.target.value as PropertyInput["locale"] })}><option value="en-SA">English (Saudi Arabia)</option><option value="ar-SA">Arabic (Saudi Arabia)</option></select></label>
    </div>
    {(Object.keys(fields) as Section[]).map(section => <details key={section} open={section === "location"} className="border-t border-slate-200 pt-3">
      <summary className="capitalize font-medium text-sm cursor-pointer">{section}</summary>
      <div className="grid md:grid-cols-3 gap-4 mt-3">{fields[section].map(([key, label, type]) => {
        const current = value[section][key]; const display = Array.isArray(current) ? current.join(", ") : current == null ? "" : String(current);
        return <label key={key} className="mizan-label">{label}{type === "boolean" ?
          <select aria-label={label} className="mizan-input" value={display} onChange={e => change(section, key, type, e.target.value)}><option value="">Unknown</option><option value="true">Yes</option><option value="false">No</option></select> :
          <input className="mizan-input" type={type === "ratio" ? "number" : ["number", "date", "url"].includes(type) ? type : "text"} step="any" min={type === "ratio" ? 0 : undefined} max={type === "ratio" ? 1 : undefined} value={display} onChange={e => change(section, key, type, e.target.value)} />}</label>;
      })}</div>
      {section === "planning" && <div className="grid md:grid-cols-4 gap-3 mt-3">{["front", "rear", "left", "right"].map(side => <label key={side} className="mizan-label">{side} setback (m)<input className="mizan-input" type="number" min="0" step="any" value={String((value.planning.setbacks_m as Record<string, number> | undefined)?.[side] ?? "")} onChange={e => {
        const setbacks = { ...(value.planning.setbacks_m as Record<string, number> || {}) };
        if (e.target.value === "") delete setbacks[side]; else setbacks[side] = Number(e.target.value);
        onChange({ ...value, planning: { ...value.planning, setbacks_m: setbacks } });
      }} /></label>)}</div>}
    </details>)}
  </div>;
}
