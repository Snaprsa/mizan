"""
Confidence scoring for valuation predictions.

Computes transparent confidence metrics based on data completeness,
segment support, and model uncertainty.
"""

from mizan_data.schemas import SubjectProperty, FIELD_WEIGHTS


# Minimum sample size for full segment support score
N_MIN = 30

# Weight for combining scores
WEIGHT_COMPLETENESS = 0.3
WEIGHT_SEGMENT_SUPPORT = 0.4
WEIGHT_MODEL_RESIDUAL = 0.3


def compute_completeness_score(subject: SubjectProperty) -> int:
    """
    Compute data completeness score based on field presence.

    Score formula:
        sum(field_weight * field_present) / sum(field_weight) * 100

    Args:
        subject: SubjectProperty to evaluate

    Returns:
        Completeness score 0-100
    """
    present_fields = subject.get_present_fields()

    weighted_present = 0.0
    total_weight = 0.0

    for field, weight in FIELD_WEIGHTS.items():
        total_weight += weight
        # Handle age: either year_built or age_years counts
        if field in ("year_built", "age_years"):
            if "year_built" in present_fields or "age_years" in present_fields:
                weighted_present += weight
        elif field in present_fields:
            weighted_present += weight

    if total_weight == 0:
        return 0

    score = (weighted_present / total_weight) * 100
    return int(min(100, max(0, score)))


def compute_segment_support_score(segment_count: int) -> int:
    """
    Compute segment support score based on sample size.

    Score formula:
        min(segment_count / N_MIN, 1.0) * 100

    Args:
        segment_count: Number of comparables in segment

    Returns:
        Segment support score 0-100
    """
    ratio = min(segment_count / N_MIN, 1.0)
    return int(ratio * 100)


def compute_model_residual_score(model_uncertainty: float) -> int:
    """
    Compute model residual score based on prediction uncertainty.

    Score formula:
        max(0, 100 - normalized_uncertainty * 50)

    Lower uncertainty = higher score.

    Args:
        model_uncertainty: Standard deviation or half-width of prediction interval
                          in log space

    Returns:
        Model residual score 0-100
    """
    # Typical model uncertainty in log(price_per_sqm) is 0.1-0.5
    # Normalize: 0.1 = excellent (95), 0.3 = good (70), 0.5 = fair (50), >0.6 = poor
    normalized = model_uncertainty / 0.5  # 0.5 as baseline
    score = max(0, 100 - normalized * 50)
    return int(min(100, score))


def compute_confidence_score(
    completeness_score: int,
    segment_support_score: int,
    model_uncertainty: float,
) -> int:
    """
    Compute overall confidence score.

    Combines three components:
    - Completeness (30%): How much input data was provided
    - Segment support (40%): How many comparables in segment
    - Model residual (30%): How certain the model prediction is

    Args:
        completeness_score: Score from compute_completeness_score
        segment_support_score: Score from compute_segment_support_score
        model_uncertainty: Raw model uncertainty value

    Returns:
        Overall confidence score 0-100
    """
    model_score = compute_model_residual_score(model_uncertainty)

    combined = (
        WEIGHT_COMPLETENESS * completeness_score
        + WEIGHT_SEGMENT_SUPPORT * segment_support_score
        + WEIGHT_MODEL_RESIDUAL * model_score
    )

    return int(min(100, max(0, combined)))


def get_confidence_interpretation(score: int) -> str:
    """
    Get human-readable interpretation of confidence score.

    Args:
        score: Confidence score 0-100

    Returns:
        Interpretation string
    """
    if score >= 80:
        return "High confidence - strong data support and reliable prediction"
    elif score >= 60:
        return "Moderate confidence - reasonable data support, some uncertainty"
    elif score >= 40:
        return "Low confidence - limited data, wider value range recommended"
    else:
        return "Very low confidence - insufficient data, use with caution"


# Fallback level penalties (percentage reduction in confidence)
FALLBACK_PENALTIES = {
    "segment": 0,       # Exact segment match - no penalty
    "city": 10,         # City-level fallback - minor penalty
    "property_type": 20, # National property-type fallback - moderate penalty
    "global": 30,       # Global fallback - significant penalty
}


def compute_fallback_penalty(fallback_level: str) -> int:
    """
    Compute confidence penalty based on fallback level.

    Cities without local data use national benchmarks, which should
    reduce confidence since local market conditions may differ.

    Args:
        fallback_level: One of 'segment', 'city', 'property_type', 'global'

    Returns:
        Penalty percentage (0-30)
    """
    return FALLBACK_PENALTIES.get(fallback_level, 0)


def compute_confidence_score_with_fallback(
    completeness_score: int,
    segment_support_score: int,
    model_uncertainty: float,
    fallback_level: str = "segment",
) -> int:
    """
    Compute overall confidence score with fallback penalty.

    Args:
        completeness_score: Score from compute_completeness_score
        segment_support_score: Score from compute_segment_support_score
        model_uncertainty: Raw model uncertainty value
        fallback_level: Level of geographic fallback used

    Returns:
        Overall confidence score 0-100 with fallback penalty applied
    """
    base_score = compute_confidence_score(
        completeness_score, segment_support_score, model_uncertainty
    )
    penalty = compute_fallback_penalty(fallback_level)
    
    # Apply penalty
    adjusted_score = base_score - penalty
    
    return int(min(100, max(0, adjusted_score)))
