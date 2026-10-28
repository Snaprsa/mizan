/**
 * Shared TypeScript types for Qaim frontend
 */

export interface Case {
    id: string;
    title: string;
    description?: string;
    city?: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    source_count: number;
    comp_count: number;
}

export interface Source {
    id: string;
    case_id: string;
    source_type: 'url' | 'pdf' | 'manual';
    url?: string;
    filename?: string;
    fetch_status: string;
    fetched_at?: string;
    created_at: string;
}

export interface ExtractionJob {
    id: string;
    case_id: string;
    source_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'partial';
    extractor_name?: string;
    extractor_version: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    fields_extracted: number;
    created_at: string;
}

export interface Citation {
    source_id: string;
    source_type: string;
    source_name?: string;
    retrieval_timestamp: string;
    locator: {
        css_selector?: string;
        xpath?: string;
        text_block?: string;
        page_number?: number;
        line_range_start?: number;
        line_range_end?: number;
        bounding_hint?: string;
    };
    snippet?: string;
    extractor_name: string;
    extractor_version: string;
    parse_confidence: number;
    llm_confidence?: number;
    crosscheck_confidence?: number;
    normalization_notes?: string;
}

export interface ExtractedField {
    id: string;
    comparable_id: string;
    field_name: string;
    raw_value?: string;
    normalized_value?: string;
    confidence: number;
    citation?: Citation;
    extraction_version: string;
    fact_type: string;
}

export interface FieldOverride {
    id: string;
    comparable_id: string;
    field_name: string;
    old_value?: string;
    new_value?: string;
    reason: string;
    overridden_by: string;
    overridden_at: string;
}

export interface AreaMeasurement {
    raw_value?: number;
    raw_unit?: string;
    normalized_value?: number;
    normalized_unit: string;
    area_type: string;
}

export interface Comparable {
    id: string;
    case_id: string;
    source_id: string;
    source_url?: string;
    source_type: string;
    property_title?: string;
    city?: string;
    district?: string;
    subdistrict?: string;
    latitude?: number;
    longitude?: number;
    property_category?: string;
    property_subtype?: string;
    evidence_type: string;
    asking_price?: number;
    transacted_price?: number;
    currency: string;
    areas: AreaMeasurement[];
    price_per_sqm?: number;
    listing_date?: string;
    transaction_date?: string;
    tenure: string;
    remaining_lease_term?: string;
    notes?: string;
    reliability_score: number;
    is_invalid: boolean;
    is_outlier: boolean;
    extracted_fields: ExtractedField[];
    overrides: FieldOverride[];
    created_at: string;
    updated_at: string;
}
