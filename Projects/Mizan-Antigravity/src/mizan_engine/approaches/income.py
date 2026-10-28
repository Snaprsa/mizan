"""
Income Approach.

Estimates property value based on income-producing potential using
Direct Capitalization and Discounted Cash Flow (DCF) methods.
"""

import logging
from typing import Optional


from .base import ApproachResult, ApproachType


logger = logging.getLogger(__name__)


class IncomeApproach:
    """
    Income Approach for property valuation.
    
    Supports two methods:
    - Direct Capitalization: NOI / Cap Rate
    - DCF: Present value of projected cash flows + terminal value
    """
    
    def __init__(self, default_cap_rate: float = 0.08):
        """
        Initialize income approach.
        
        Args:
            default_cap_rate: Default capitalization rate (8%)
        """
        self.default_cap_rate = default_cap_rate
    
    def value_direct_cap(
        self,
        noi: float,
        cap_rate: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> ApproachResult:
        """
        Estimate value using Direct Capitalization.
        
        Value = NOI / Cap Rate
        
        Args:
            noi: Net Operating Income (annual)
            cap_rate: Capitalization rate (default 8%)
            notes: Optional notes about the valuation
            
        Returns:
            ApproachResult with value indication
        """
        cap_rate = cap_rate or self.default_cap_rate
        
        if cap_rate <= 0:
            raise ValueError("Cap rate must be positive")
        
        value = noi / cap_rate
        
        # Value range based on cap rate uncertainty (±50bps)
        value_high = noi / (cap_rate - 0.005) if cap_rate > 0.005 else value * 1.1
        value_low = noi / (cap_rate + 0.005)
        
        return ApproachResult(
            approach_type=ApproachType.INCOME,
            value_low=value_low,
            value_mid=value,
            value_high=value_high,
            reliability_score=80 if cap_rate else 60,
            data_quality_score=85 if noi > 0 else 50,
            evidence={
                "method": "direct_capitalization",
                "noi": noi,
                "cap_rate": cap_rate,
                "cap_rate_range": [cap_rate - 0.005, cap_rate + 0.005],
                "implied_yield": cap_rate * 100,
            },
            notes=notes or f"Direct cap: NOI {noi:,.0f} / {cap_rate*100:.1f}% = {value:,.0f}",
        )
    
    def value_dcf(
        self,
        cash_flows: list[float],
        terminal_value: float,
        discount_rate: float,
        notes: Optional[str] = None,
    ) -> ApproachResult:
        """
        Estimate value using Discounted Cash Flow (DCF).
        
        Value = Σ(CF_t / (1+r)^t) + TV / (1+r)^n
        
        Args:
            cash_flows: List of projected annual cash flows
            terminal_value: Terminal value at end of projection
            discount_rate: Discount rate / required return
            notes: Optional notes
            
        Returns:
            ApproachResult with DCF value
        """
        if discount_rate <= 0:
            raise ValueError("Discount rate must be positive")
        
        n_years = len(cash_flows)
        
        # PV of cash flows
        pv_cash_flows = sum(
            cf / ((1 + discount_rate) ** (t + 1))
            for t, cf in enumerate(cash_flows)
        )
        
        # PV of terminal value
        pv_terminal = terminal_value / ((1 + discount_rate) ** n_years)
        
        value = pv_cash_flows + pv_terminal
        
        # Sensitivity: ±100bps on discount rate
        dr_high = discount_rate + 0.01
        dr_low = discount_rate - 0.01
        
        pv_low = sum(cf / ((1 + dr_high) ** (t + 1)) for t, cf in enumerate(cash_flows))
        pv_low += terminal_value / ((1 + dr_high) ** n_years)
        
        pv_high = sum(cf / ((1 + dr_low) ** (t + 1)) for t, cf in enumerate(cash_flows))
        pv_high += terminal_value / ((1 + dr_low) ** n_years)
        
        return ApproachResult(
            approach_type=ApproachType.INCOME,
            value_low=pv_low,
            value_mid=value,
            value_high=pv_high,
            reliability_score=75,
            data_quality_score=80,
            evidence={
                "method": "dcf",
                "projection_years": n_years,
                "total_cash_flows": sum(cash_flows),
                "terminal_value": terminal_value,
                "discount_rate": discount_rate,
                "pv_cash_flows": pv_cash_flows,
                "pv_terminal": pv_terminal,
                "terminal_value_pct": (pv_terminal / value) * 100 if value else 0,
            },
            notes=notes or f"DCF {n_years}-year projection at {discount_rate*100:.1f}% discount rate",
        )
    
    def value_yield(
        self,
        gross_income: float,
        opex_ratio: float = 0.35,
        cap_rate: Optional[float] = None,
    ) -> ApproachResult:
        """
        Quick yield-based valuation from gross income.
        
        Args:
            gross_income: Gross potential income
            opex_ratio: Operating expense ratio (default 35%)
            cap_rate: Cap rate (default from init)
            
        Returns:
            ApproachResult
        """
        noi = gross_income * (1 - opex_ratio)
        return self.value_direct_cap(
            noi=noi,
            cap_rate=cap_rate,
            notes=f"From gross income {gross_income:,.0f} with {opex_ratio*100:.0f}% opex ratio",
        )
