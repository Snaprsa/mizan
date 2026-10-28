"""
ROI Calculator for real estate investment analysis.

Computes rental yields, capital appreciation, cash-on-cash returns,
and overall investment metrics.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class InvestmentGrade(str, Enum):
    """Investment recommendation grades."""
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    CAUTION = "Caution"


@dataclass
class ROIProjection:
    """Complete ROI projection for a property investment."""
    
    # Rental yields (percentage)
    rental_yield_gross: float = 0.0
    rental_yield_net: float = 0.0
    
    # Capital appreciation projections (percentage)
    capital_appreciation_1yr: float = 0.0
    capital_appreciation_3yr: float = 0.0
    capital_appreciation_5yr: float = 0.0
    
    # Combined ROI
    total_roi_1yr: float = 0.0
    total_roi_3yr: float = 0.0
    total_roi_5yr: float = 0.0
    
    # Investment analysis
    cash_on_cash_return: float = 0.0
    payback_period_years: Optional[float] = None
    
    # Risk and recommendation
    risk_score: int = 5  # 1-10 scale
    investment_grade: InvestmentGrade = InvestmentGrade.HOLD
    
    # Breakdown details
    estimated_annual_rent_sar: float = 0.0
    estimated_operating_expenses_sar: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "rental_yield_gross": round(self.rental_yield_gross, 2),
            "rental_yield_net": round(self.rental_yield_net, 2),
            "capital_appreciation_1yr": round(self.capital_appreciation_1yr, 2),
            "capital_appreciation_3yr": round(self.capital_appreciation_3yr, 2),
            "capital_appreciation_5yr": round(self.capital_appreciation_5yr, 2),
            "total_roi_1yr": round(self.total_roi_1yr, 2),
            "total_roi_3yr": round(self.total_roi_3yr, 2),
            "total_roi_5yr": round(self.total_roi_5yr, 2),
            "cash_on_cash_return": round(self.cash_on_cash_return, 2),
            "payback_period_years": round(self.payback_period_years, 1) if self.payback_period_years else None,
            "risk_score": self.risk_score,
            "investment_grade": self.investment_grade.value,
            "estimated_annual_rent_sar": int(self.estimated_annual_rent_sar),
            "estimated_operating_expenses_sar": int(self.estimated_operating_expenses_sar),
        }


# Average rental rates by city and property type (SAR per sqm per year)
# Based on Saudi Real Estate Authority data
RENTAL_RATES = {
    "Riyadh": {
        "apartment": {
            "premium": 1200,  # Al Olaya, Hittin, Al Nakheel
            "standard": 900,   # Al Malqa, Al Yasmin, Al Muruj
            "economy": 650,    # Al Narjis, Al Qirawan, Al Rabwah
        },
        "villa": {
            "premium": 800,
            "standard": 600,
            "economy": 450,
        },
        "land": 0,  # No rental for land
    },
    "Jeddah": {
        "apartment": {
            "premium": 1100,  # Al Hamra, Obhur, Al Shati
            "standard": 850,
            "economy": 600,
        },
        "villa": {
            "premium": 750,
            "standard": 550,
            "economy": 400,
        },
        "land": 0,
    },
    "Dammam": {
        "apartment": {
            "premium": 900,  # Al Shati, Al Murjan
            "standard": 700,
            "economy": 500,
        },
        "villa": {
            "premium": 650,
            "standard": 500,
            "economy": 350,
        },
        "land": 0,
    },
}

# Premium districts by city
PREMIUM_DISTRICTS = {
    "Riyadh": ["Al Olaya", "Hittin", "Al Nakheel", "Al Sulaimaniyah"],
    "Jeddah": ["Al Hamra", "Obhur", "Al Shati", "Al Khalidiyah"],
    "Dammam": ["Al Shati", "Al Murjan", "Al Khalij"],
}

ECONOMY_DISTRICTS = {
    "Riyadh": ["Al Narjis", "Al Qirawan", "Al Rabwah", "Al Shifa"],
    "Jeddah": ["Al Naeem", "Al Andalus"],
    "Dammam": ["Al Nada", "Al Rawdah", "Al Mazruiyah"],
}

# Historical appreciation rates (annual %)
APPRECIATION_RATES = {
    "Riyadh": {
        "apartment": {"premium": 8.5, "standard": 6.5, "economy": 4.5},
        "villa": {"premium": 10.0, "standard": 7.5, "economy": 5.5},
        "land": {"premium": 12.0, "standard": 9.0, "economy": 7.0},
    },
    "Jeddah": {
        "apartment": {"premium": 7.5, "standard": 5.5, "economy": 4.0},
        "villa": {"premium": 9.0, "standard": 6.5, "economy": 5.0},
        "land": {"premium": 11.0, "standard": 8.0, "economy": 6.0},
    },
    "Dammam": {
        "apartment": {"premium": 7.0, "standard": 5.0, "economy": 3.5},
        "villa": {"premium": 8.5, "standard": 6.0, "economy": 4.5},
        "land": {"premium": 10.0, "standard": 7.5, "economy": 5.5},
    },
}

# Operating expense ratios
EXPENSE_RATIOS = {
    "apartment": 0.12,  # 12% of gross rent
    "villa": 0.10,      # 10% of gross rent
    "land": 0.02,       # 2% (minimal - just land tax if any)
}


class ROICalculator:
    """
    Calculator for real estate investment returns.
    
    Computes comprehensive ROI metrics including rental yields,
    capital appreciation, and investment recommendations.
    """
    
    def __init__(self):
        """Initialize the ROI calculator."""
        pass
    
    def calculate(
        self,
        property_value_sar: float,
        property_type: str,
        city: str,
        district: str,
        area_sqm: float,
        down_payment_pct: float = 30.0,
        mortgage_rate_pct: float = 7.0,
        loan_term_years: int = 20,
        risk_score: int = 5,
    ) -> ROIProjection:
        """
        Calculate comprehensive ROI projection.
        
        Args:
            property_value_sar: Estimated property value in SAR
            property_type: apartment, villa, or land
            city: City name
            district: District name
            area_sqm: Property area in square meters
            down_payment_pct: Down payment percentage (default 30%)
            mortgage_rate_pct: Annual mortgage rate (default 7%)
            loan_term_years: Loan term in years (default 20)
            risk_score: Pre-calculated risk score 1-10
            
        Returns:
            ROIProjection with all investment metrics
        """
        # Determine district tier
        tier = self._get_district_tier(city, district)
        
        # Get rental rate
        rental_rate = self._get_rental_rate(city, property_type, tier)
        annual_rent = rental_rate * area_sqm
        
        # Calculate expense ratio
        expense_ratio = EXPENSE_RATIOS.get(property_type, 0.12)
        annual_expenses = annual_rent * expense_ratio
        net_rent = annual_rent - annual_expenses
        
        # Calculate yields
        rental_yield_gross = (annual_rent / property_value_sar * 100) if property_value_sar > 0 else 0
        rental_yield_net = (net_rent / property_value_sar * 100) if property_value_sar > 0 else 0
        
        # Get appreciation rates
        appreciation = self._get_appreciation_rate(city, property_type, tier)
        
        # Calculate compound appreciation
        cap_1yr = appreciation
        cap_3yr = ((1 + appreciation / 100) ** 3 - 1) * 100
        cap_5yr = ((1 + appreciation / 100) ** 5 - 1) * 100
        
        # Total ROI (rental + appreciation)
        total_1yr = rental_yield_net + cap_1yr
        total_3yr = rental_yield_net * 3 + cap_3yr
        total_5yr = rental_yield_net * 5 + cap_5yr
        
        # Cash-on-cash return (for leveraged purchase)
        down_payment = property_value_sar * (down_payment_pct / 100)
        
        if down_payment > 0:
            # Monthly mortgage payment calculation (simplified)
            loan_amount = property_value_sar - down_payment
            monthly_rate = mortgage_rate_pct / 100 / 12
            n_payments = loan_term_years * 12
            
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
            else:
                monthly_payment = loan_amount / n_payments
            
            annual_mortgage = monthly_payment * 12
            annual_cashflow = net_rent - annual_mortgage
            cash_on_cash = (annual_cashflow / down_payment * 100) if down_payment > 0 else 0
        else:
            cash_on_cash = rental_yield_net
        
        # Payback period
        if net_rent > 0:
            payback_years = property_value_sar / net_rent
        else:
            payback_years = None
        
        # Investment grade
        grade = self._calculate_investment_grade(
            rental_yield_net, appreciation, risk_score, property_type
        )
        
        return ROIProjection(
            rental_yield_gross=rental_yield_gross,
            rental_yield_net=rental_yield_net,
            capital_appreciation_1yr=cap_1yr,
            capital_appreciation_3yr=cap_3yr,
            capital_appreciation_5yr=cap_5yr,
            total_roi_1yr=total_1yr,
            total_roi_3yr=total_3yr,
            total_roi_5yr=total_5yr,
            cash_on_cash_return=cash_on_cash,
            payback_period_years=payback_years,
            risk_score=risk_score,
            investment_grade=grade,
            estimated_annual_rent_sar=annual_rent,
            estimated_operating_expenses_sar=annual_expenses,
        )
    
    def _get_district_tier(self, city: str, district: str) -> str:
        """Determine district tier: premium, standard, or economy."""
        if district in PREMIUM_DISTRICTS.get(city, []):
            return "premium"
        elif district in ECONOMY_DISTRICTS.get(city, []):
            return "economy"
        return "standard"
    
    def _get_rental_rate(self, city: str, property_type: str, tier: str) -> float:
        """Get rental rate per sqm per year."""
        city_rates = RENTAL_RATES.get(city, RENTAL_RATES["Riyadh"])
        type_rates = city_rates.get(property_type, city_rates.get("apartment", {}))
        
        if isinstance(type_rates, dict):
            return type_rates.get(tier, type_rates.get("standard", 800))
        return type_rates
    
    def _get_appreciation_rate(self, city: str, property_type: str, tier: str) -> float:
        """Get annual appreciation rate percentage."""
        city_rates = APPRECIATION_RATES.get(city, APPRECIATION_RATES["Riyadh"])
        type_rates = city_rates.get(property_type, city_rates.get("apartment", {}))
        return type_rates.get(tier, type_rates.get("standard", 6.0))
    
    def _calculate_investment_grade(
        self,
        rental_yield: float,
        appreciation: float,
        risk_score: int,
        property_type: str,
    ) -> InvestmentGrade:
        """Calculate investment recommendation grade."""
        # Combined score based on returns and risk
        combined_return = rental_yield + appreciation
        risk_adjusted_return = combined_return * (11 - risk_score) / 10
        
        # Land has different thresholds (no rental, higher appreciation expected)
        if property_type == "land":
            if appreciation >= 10 and risk_score <= 4:
                return InvestmentGrade.STRONG_BUY
            elif appreciation >= 7 and risk_score <= 6:
                return InvestmentGrade.BUY
            elif appreciation >= 5 and risk_score <= 7:
                return InvestmentGrade.HOLD
            else:
                return InvestmentGrade.CAUTION
        
        # Buildings (apartments/villas)
        if risk_adjusted_return >= 12 and risk_score <= 4:
            return InvestmentGrade.STRONG_BUY
        elif risk_adjusted_return >= 9 and risk_score <= 6:
            return InvestmentGrade.BUY
        elif risk_adjusted_return >= 6 and risk_score <= 7:
            return InvestmentGrade.HOLD
        else:
            return InvestmentGrade.CAUTION
