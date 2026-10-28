"""
Valuation Approaches Package.

Contains the three main valuation approaches used in professional
real estate appraisal.
"""

from .base import ApproachResult
from .sales_comparison import SalesComparisonApproach
from .income import IncomeApproach
from .cost import CostApproach

__all__ = [
    "ApproachResult",
    "SalesComparisonApproach",
    "IncomeApproach",
    "CostApproach",
]
