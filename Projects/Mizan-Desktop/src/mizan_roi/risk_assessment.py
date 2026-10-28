"""
Risk Assessment module for real estate investments.

Evaluates market risk, liquidity risk, location risk, and 
regulatory risk to provide an overall risk score.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classifications."""
    VERY_LOW = "Very Low"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class RiskScore:
    """Comprehensive risk assessment for a property investment."""
    
    # Individual risk scores (1-10, where 10 is highest risk)
    market_risk: int = 5
    liquidity_risk: int = 5
    location_risk: int = 5
    regulatory_risk: int = 3
    concentration_risk: int = 5
    
    # Overall risk
    overall_risk: int = 5
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # Risk factors details
    risk_factors: list = None
    mitigating_factors: list = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.mitigating_factors is None:
            self.mitigating_factors = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "market_risk": self.market_risk,
            "liquidity_risk": self.liquidity_risk,
            "location_risk": self.location_risk,
            "regulatory_risk": self.regulatory_risk,
            "concentration_risk": self.concentration_risk,
            "overall_risk": self.overall_risk,
            "risk_level": self.risk_level.value,
            "risk_factors": self.risk_factors,
            "mitigating_factors": self.mitigating_factors,
        }


# District liquidity data (average days to sell)
DISTRICT_LIQUIDITY = {
    "Riyadh": {
        "Al Olaya": 25,
        "Hittin": 30,
        "Al Nakheel": 35,
        "Al Malqa": 40,
        "Al Yasmin": 45,
        "Al Muruj": 40,
        "Al Sahafa": 50,
        "Al Sulaimaniyah": 35,
        "Al Woroud": 40,
        "Al Mohammadiyah": 55,
        "Al Narjis": 60,
        "Al Qirawan": 65,
        "Al Rabwah": 55,
        "Al Rawdah": 50,
        "Al Shifa": 70,
    },
    "Jeddah": {
        "Al Hamra": 30,
        "Obhur": 25,
        "Al Shati": 30,
        "Al Zahra": 40,
        "Al Rawdah": 50,
        "Al Khalidiyah": 35,
        "Al Salama": 55,
        "Al Safa": 45,
        "Al Marwah": 55,
        "Al Naeem": 65,
        "Al Andalus": 60,
    },
    "Dammam": {
        "Al Shati": 35,
        "Al Murjan": 40,
        "Al Faisaliyah": 45,
        "Al Khalij": 40,
        "Al Rawdah": 55,
        "Al Anoud": 50,
        "Al Qadisiyah": 55,
        "Al Nada": 65,
        "Al Mazruiyah": 70,
        "Ash Shulah": 60,
    },
}

# Market volatility by city (historical price variation %)
MARKET_VOLATILITY = {
    "Riyadh": 8.0,   # Moderate volatility
    "Jeddah": 10.0,  # Higher volatility
    "Dammam": 7.0,   # Lower volatility
}

# Oversupply risk by property type and area
OVERSUPPLY_RISK = {
    "apartment": {
        "high": ["Al Qirawan", "Al Narjis", "Al Shifa"],  # New developments, high supply
        "moderate": ["Al Yasmin", "Al Sahafa", "Al Mohammadiyah"],
        "low": ["Al Olaya", "Hittin", "Al Nakheel"],
    },
    "villa": {
        "high": ["Al Narjis", "Al Qirawan"],
        "moderate": ["Al Yasmin", "Al Malqa"],
        "low": ["Hittin", "Al Nakheel", "Al Muruj"],
    },
    "land": {
        "high": ["Al Qirawan", "Al Shifa"],
        "moderate": ["Al Narjis", "Al Rabwah"],
        "low": ["Al Olaya", "Hittin", "Al Malqa"],
    },
}


class RiskAssessor:
    """
    Assesses investment risk for real estate properties.
    
    Evaluates multiple risk dimensions including market,
    liquidity, location, and regulatory risks.
    """
    
    def __init__(self):
        """Initialize the risk assessor."""
        pass
    
    def assess(
        self,
        city: str,
        district: str,
        property_type: str,
        property_value_sar: float,
        area_sqm: float,
        year_built: Optional[int] = None,
    ) -> RiskScore:
        """
        Assess investment risk for a property.
        
        Args:
            city: City name
            district: District name
            property_type: apartment, villa, or land
            property_value_sar: Property value in SAR
            area_sqm: Property area in square meters
            year_built: Year of construction (optional)
            
        Returns:
            RiskScore with comprehensive risk assessment
        """
        # Calculate individual risk scores
        market_risk = self._assess_market_risk(city, property_type)
        liquidity_risk = self._assess_liquidity_risk(city, district, property_type, area_sqm)
        location_risk = self._assess_location_risk(city, district, property_type)
        regulatory_risk = self._assess_regulatory_risk(property_type, city)
        concentration_risk = self._assess_concentration_risk(property_value_sar)
        
        # Calculate overall risk (weighted average)
        weights = {
            "market": 0.25,
            "liquidity": 0.25,
            "location": 0.25,
            "regulatory": 0.15,
            "concentration": 0.10,
        }
        
        overall = int(round(
            market_risk * weights["market"] +
            liquidity_risk * weights["liquidity"] +
            location_risk * weights["location"] +
            regulatory_risk * weights["regulatory"] +
            concentration_risk * weights["concentration"]
        ))
        
        # Determine risk level
        if overall <= 2:
            risk_level = RiskLevel.VERY_LOW
        elif overall <= 4:
            risk_level = RiskLevel.LOW
        elif overall <= 6:
            risk_level = RiskLevel.MODERATE
        elif overall <= 8:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        # Build risk factors and mitigating factors
        risk_factors, mitigating_factors = self._build_factor_lists(
            city, district, property_type, market_risk, liquidity_risk, 
            location_risk, property_value_sar
        )
        
        return RiskScore(
            market_risk=market_risk,
            liquidity_risk=liquidity_risk,
            location_risk=location_risk,
            regulatory_risk=regulatory_risk,
            concentration_risk=concentration_risk,
            overall_risk=overall,
            risk_level=risk_level,
            risk_factors=risk_factors,
            mitigating_factors=mitigating_factors,
        )
    
    def _assess_market_risk(self, city: str, property_type: str) -> int:
        """Assess market volatility risk."""
        volatility = MARKET_VOLATILITY.get(city, 8.0)
        
        # Convert volatility to risk score (1-10)
        base_risk = min(10, max(1, int(volatility)))
        
        # Land has higher market risk
        if property_type == "land":
            base_risk = min(10, base_risk + 2)
        
        return base_risk
    
    def _assess_liquidity_risk(
        self, 
        city: str, 
        district: str, 
        property_type: str,
        area_sqm: float,
    ) -> int:
        """Assess how quickly the property can be sold."""
        city_liquidity = DISTRICT_LIQUIDITY.get(city, {})
        days_to_sell = city_liquidity.get(district, 50)
        
        # Convert days to risk score
        if days_to_sell <= 30:
            base_risk = 2
        elif days_to_sell <= 40:
            base_risk = 3
        elif days_to_sell <= 50:
            base_risk = 5
        elif days_to_sell <= 60:
            base_risk = 7
        else:
            base_risk = 8
        
        # Larger properties are harder to sell
        if area_sqm > 400:
            base_risk = min(10, base_risk + 1)
        
        # Land is generally less liquid
        if property_type == "land":
            base_risk = min(10, base_risk + 1)
        
        return base_risk
    
    def _assess_location_risk(
        self, 
        city: str, 
        district: str, 
        property_type: str,
    ) -> int:
        """Assess location-specific risks."""
        # Check oversupply risk
        type_risks = OVERSUPPLY_RISK.get(property_type, {})
        
        if district in type_risks.get("high", []):
            base_risk = 7
        elif district in type_risks.get("moderate", []):
            base_risk = 5
        elif district in type_risks.get("low", []):
            base_risk = 3
        else:
            base_risk = 5  # Unknown district, moderate risk
        
        return base_risk
    
    def _assess_regulatory_risk(self, property_type: str, city: str) -> int:
        """Assess regulatory and policy risks."""
        # Saudi Arabia has relatively stable property regulations
        base_risk = 3
        
        # Foreign ownership restrictions vary
        if city == "Riyadh":
            base_risk = 2  # Most permissive
        elif city == "Jeddah":
            base_risk = 3
        else:
            base_risk = 4
        
        # Land has more zoning considerations
        if property_type == "land":
            base_risk = min(10, base_risk + 2)
        
        return base_risk
    
    def _assess_concentration_risk(self, property_value_sar: float) -> int:
        """Assess risk from investment concentration (large single investment)."""
        # Higher value = higher concentration risk for typical investors
        if property_value_sar > 10_000_000:
            return 8
        elif property_value_sar > 5_000_000:
            return 6
        elif property_value_sar > 3_000_000:
            return 4
        elif property_value_sar > 1_500_000:
            return 3
        else:
            return 2
    
    def _build_factor_lists(
        self,
        city: str,
        district: str,
        property_type: str,
        market_risk: int,
        liquidity_risk: int,
        location_risk: int,
        property_value_sar: float,
    ) -> tuple[list, list]:
        """Build lists of risk factors and mitigating factors."""
        risk_factors = []
        mitigating_factors = []
        
        # Market risk factors
        if market_risk >= 7:
            risk_factors.append("High market volatility")
        elif market_risk <= 3:
            mitigating_factors.append("Stable market conditions")
        
        # Liquidity factors
        if liquidity_risk >= 7:
            risk_factors.append("Low market liquidity - longer selling time expected")
        elif liquidity_risk <= 3:
            mitigating_factors.append("High liquidity - quick sale potential")
        
        # Location factors
        if location_risk >= 7:
            risk_factors.append("Oversupply in area may affect appreciation")
        elif location_risk <= 3:
            mitigating_factors.append("Strong location with limited supply")
        
        # Value-based factors
        if property_value_sar > 5_000_000:
            risk_factors.append("Premium pricing - smaller buyer pool")
        elif property_value_sar < 2_000_000:
            mitigating_factors.append("Accessible price point - larger buyer pool")
        
        # Property type factors
        if property_type == "land":
            risk_factors.append("Land investment - no rental income")
            mitigating_factors.append("Land scarcity - strong long-term appreciation potential")
        elif property_type == "villa":
            mitigating_factors.append("Villa - strong family demand in Saudi market")
        else:
            mitigating_factors.append("Apartment - rental income potential")
        
        # City factors
        if city == "Riyadh":
            mitigating_factors.append("Capital city - government support and development")
        
        return risk_factors, mitigating_factors
