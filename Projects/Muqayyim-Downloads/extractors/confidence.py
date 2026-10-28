"""
Confidence scoring for extracted fields.

Combines:
- Deterministic parse confidence (from regex/selector match quality)
- LLM confidence (from model's self-assessment, if used)
- Cross-check confidence (from validating against other fields/sources)
- Source reliability weight (1-5 scale mapped to multiplier)
"""

from typing import Optional

# Source reliability → confidence multiplier
RELIABILITY_MULTIPLIER = {
    5: 1.0,   # Authenticated transaction
    4: 0.95,  # Official filing
    3: 0.85,  # Broker material
    2: 0.75,  # Marketplace listing
    1: 0.50,  # User entered / unverified
}


def score_confidence(
    parse_confidence: float,
    source_reliability: int = 2,
    llm_confidence: Optional[float] = None,
    crosscheck_confidence: Optional[float] = None,
) -> float:
    """
    Compute a combined confidence score (0.0–1.0).

    Strategy:
    - Start with parse confidence
    - If LLM was used, blend with LLM confidence (weighted lower)
    - If cross-check available, boost or penalize
    - Apply source reliability multiplier
    """
    base = parse_confidence

    # Blend with LLM if used (LLM gets 40% weight when present)
    if llm_confidence is not None:
        base = (base * 0.6) + (llm_confidence * 0.4)

    # Cross-check adjustment (±20%)
    if crosscheck_confidence is not None:
        adjustment = (crosscheck_confidence - 0.5) * 0.4  # -0.2 to +0.2
        base = base + adjustment

    # Apply source reliability
    multiplier = RELIABILITY_MULTIPLIER.get(source_reliability, 0.75)
    result = base * multiplier

    # Clamp to 0.0–1.0
    return max(0.0, min(1.0, round(result, 3)))


def classify_confidence(score: float) -> str:
    """Return human-readable confidence level."""
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"
