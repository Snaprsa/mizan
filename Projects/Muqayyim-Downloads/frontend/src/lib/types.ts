/**
 * TypeScript types mirroring backend Pydantic schemas.
 * Keep in sync with api/app/schemas/ and schemas/
 */

// ──────────────────────────────────────────────
// Enums
// ──────────────────────────────────────────────

export type PropertyType =
  | "raw_land" | "serviced_land"
  | "villa" | "apartment" | "compound" | "branded_residence" | "townhouse" | "duplex"
  | "office" | "retail" | "mixed_use"
  | "hotel" | "serviced_apartment"
  | "warehouse" | "logistics" | "factory"
  | "special_purpose" | "other" | "unknown";

export type DealType = "sale" | "lease" | "rent" | "unknown";

export type EvidenceType =
  | "listing_asking" | "transaction_achieved" | "offer_accepted"
  | "auction_result" | "official_record" | "unknown";

export type AreaType = "land_area" | "plot_area" | "bua" | "gla" | "nla" | "total_area" | "other" | "unknown";

export type SourceType = "url" | "pdf" | "manual";

export type ExtractionStatus = "pending" | "running" | "completed" | "failed" | "partial";

export type ComparableStatus = "active" | "invalid" | "outlier" | "draft";

export type CaseStatus = "draft" | "in_progress" | "review" | "completed" | "archived";

export type DataClassification = "fact" | "assumption" | "judgment";

// ──────────────────────────────────────────────
// Citation
// ──────────────────────────────────────────────

export interface CitationObject {
  source_id: string;
  source_type: string;
  source_url_or_name: string;
  retrieval_timestamp: string;
  locator: string | null;
  snippet: string | null;
  extractor_name: string;
  extractor_version: string;
  parse_confidence: number;
  llm_confidence: number | null;
  crosscheck_confidence: number | null;
  normalization_notes: string | null;
}

// ──────────────────────────────────────────────
// Cases
// ──────────────────────────────────────────────

export interface Case {
  id: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  source_count: number;
  comparable_count: number;
}

export interface CaseCreate {
  title: string;
  description?: string;
}

export interface CaseListResponse {
  data: Case[];
  total: number;
}

// ──────────────────────────────────────────────
// Sources
// ──────────────────────────────────────────────

export interface Source {
  id: string;
  case_id: string;
  source_type: SourceType;
  url: string | null;
  file_name: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface SourceAddURL {
  url: string;
  notes?: string;
}

// ──────────────────────────────────────────────
// Extraction Jobs
// ──────────────────────────────────────────────

export interface ExtractionJob {
  id: string;
  source_id: string;
  status: ExtractionStatus;
  extractor_name: string | null;
  extractor_version: string | null;
  error_log: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface StartExtractionResponse {
  job_id: string;
  status: string;
  message: string;
}

// ──────────────────────────────────────────────
// Extracted Fields
// ──────────────────────────────────────────────

export interface ExtractedField {
  id: string;
  field_name: string;
  raw_value: string | null;
  normalized_value: string | null;
  display_value: string | null;
  confidence: number;
  classification: DataClassification;
  citation: CitationObject | null;
  is_overridden: boolean;
  override_value: string | null;
}

export interface FieldOverrideRequest {
  new_value: string;
  reason: string;
}

// ──────────────────────────────────────────────
// Comparables
// ──────────────────────────────────────────────

export interface Comparable {
  id: string;
  case_id: string;
  source_id: string;
  status: ComparableStatus;
  reliability_score: number;

  property_title: string | null;
  city: string | null;
  district: string | null;
  property_type: string | null;
  evidence_type: string | null;
  asking_price: number | null;
  transacted_price: number | null;
  currency: string;
  primary_area_sqm: number | null;
  price_per_sqm: number | null;
  listing_date: string | null;
  transaction_date: string | null;
  tenure: string | null;
  latitude: number | null;
  longitude: number | null;
  notes: string | null;

  created_at: string;

  extracted_fields: ExtractedField[];
  source_url: string | null;
  source_type: string | null;
}

export interface ComparableListResponse {
  data: Comparable[];
  total: number;
}

export interface ComparableStatusUpdate {
  status: "active" | "invalid" | "outlier";
  reason?: string;
}

// ──────────────────────────────────────────────
// Reliability labels
// ──────────────────────────────────────────────

export const RELIABILITY_LABELS: Record<number, string> = {
  5: "Authenticated Transaction",
  4: "Official Filing",
  3: "Broker Material",
  2: "Marketplace Listing",
  1: "User Entered / Unverified",
};

export const EVIDENCE_LABELS: Record<string, string> = {
  listing_asking: "Listing (Asking)",
  transaction_achieved: "Transaction (Achieved)",
  offer_accepted: "Offer Accepted",
  auction_result: "Auction Result",
  official_record: "Official Record",
  unknown: "Unknown",
};

// ──────────────────────────────────────────────
// Confidence helpers
// ──────────────────────────────────────────────

export function confidenceColor(confidence: number): string {
  if (confidence >= 0.8) return "text-green-700 bg-green-50";
  if (confidence >= 0.5) return "text-yellow-700 bg-yellow-50";
  return "text-red-700 bg-red-50";
}

export function confidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return "High";
  if (confidence >= 0.5) return "Medium";
  return "Low";
}
