/** Compare saved inputs and actual evidence, not just the property's revision. */
import type { AnalysisInput, AnalysisResult, Candidate, PreparedAnalysis, ValuationField } from "./api";

type SignatureInput = { method: string; asOf: string; radius: number; lookback: number;
  inputs: Record<string, AnalysisInput>; evidence: Candidate[] };

export function inputsFromFields(fields: ValuationField[]): Record<string, AnalysisInput> {
  return Object.fromEntries(fields.filter(f => f.value != null).map(f => [f.key, {
    value: f.value!, source: f.source || "", as_of: f.as_of || "", status: f.assumption_status || "user_input",
  }]));
}

export function valuationSignature({ method, asOf, radius, lookback, inputs, evidence }: SignatureInput) {
  const normalizedInputs = Object.fromEntries(Object.keys(inputs).sort().map(key => [key, {
    value: inputs[key].value, source: inputs[key].source.trim(), as_of: inputs[key].as_of,
    status: inputs[key].status || "user_input",
  }]));
  const normalizedEvidence = method === "sales_comparison" ? evidence.map(r => ({
    id: r.id, price: r.price, area: r.area_sqm, rate: r.price_per_sqm, coordinates: r.coordinates,
    date: r.date, currency: r.currency, property_type: r.property_type, source: r.source,
    status: r.status, evidence_type: r.evidence_type,
  })).sort((a, b) => a.id.localeCompare(b.id)) : [];
  return JSON.stringify({ method, asOf, radius, lookback, inputs: normalizedInputs, evidence: normalizedEvidence });
}

export function preparedSignature(p: PreparedAnalysis) {
  return valuationSignature({ method: p.method, asOf: p.as_of, radius: p.radius_km,
    lookback: p.lookback_days, inputs: inputsFromFields(p.fields), evidence: p.eligible_comparables });
}

export function savedRunMatchesPrepared(p: PreparedAnalysis, run: AnalysisResult) {
  if (run.property_revision !== p.revision || run.method !== p.method || !run.inputs || !run.property?.analysis ||
      !p.calculation_version || run.outputs.calculation_version !== p.calculation_version) return false;
  const setup = run.property.analysis;
  return preparedSignature(p) === valuationSignature({ method: run.method, asOf: run.data_date,
    radius: setup.radius_km, lookback: setup.lookback_days, inputs: inputsFromFields(run.inputs),
    evidence: run.comparables || [] });
}
