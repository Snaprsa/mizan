"""
Market Factors Engine for real estate valuation adjustments.

Analyzes location premiums, infrastructure impacts, market momentum,
and other variables affecting property values.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketFactors:
    """Market factors affecting property value."""
    
    # Location factors (percentage adjustments)
    location_premium_pct: float = 0.0
    cbd_proximity_pct: float = 0.0
    
    # Infrastructure factors
    infrastructure_impact_pct: float = 0.0
    metro_proximity_pct: float = 0.0
    mega_project_proximity_pct: float = 0.0
    
    # Market dynamics
    market_momentum_pct: float = 0.0
    supply_demand_adjustment_pct: float = 0.0
    
    # Development potential (for land)
    development_potential_pct: float = 0.0
    
    # Combined adjustment
    combined_adjustment_pct: float = 0.0
    
    # Descriptive factors
    key_drivers: list = None
    
    def __post_init__(self):
        if self.key_drivers is None:
            self.key_drivers = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "location_premium_pct": round(self.location_premium_pct, 1),
            "cbd_proximity_pct": round(self.cbd_proximity_pct, 1),
            "infrastructure_impact_pct": round(self.infrastructure_impact_pct, 1),
            "metro_proximity_pct": round(self.metro_proximity_pct, 1),
            "mega_project_proximity_pct": round(self.mega_project_proximity_pct, 1),
            "market_momentum_pct": round(self.market_momentum_pct, 1),
            "supply_demand_adjustment_pct": round(self.supply_demand_adjustment_pct, 1),
            "development_potential_pct": round(self.development_potential_pct, 1),
            "combined_adjustment_pct": round(self.combined_adjustment_pct, 1),
            "key_drivers": self.key_drivers,
        }


# District characteristics database
DISTRICT_CHARACTERISTICS = {
    "Riyadh": {
        "Al Olaya": {
            "location_premium": 20.0,
            "cbd_proximity": 15.0,
            "metro_access": True,
            "market_momentum": 8.0,
            "supply_pressure": -3.0,  # High supply = negative pressure
            "description": "Prime business district with excellent connectivity",
        },
        "Hittin": {
            "location_premium": 18.0,
            "cbd_proximity": 10.0,
            "metro_access": True,
            "market_momentum": 10.0,
            "supply_pressure": -2.0,
            "description": "Upscale residential with high demand",
        },
        "Al Nakheel": {
            "location_premium": 15.0,
            "cbd_proximity": 8.0,
            "metro_access": True,
            "market_momentum": 7.0,
            "supply_pressure": 0.0,
            "description": "Established premium residential area",
        },
        "Al Malqa": {
            "location_premium": 10.0,
            "cbd_proximity": 5.0,
            "metro_access": False,
            "market_momentum": 6.0,
            "supply_pressure": 2.0,
            "description": "Growing residential district with good amenities",
        },
        "Al Yasmin": {
            "location_premium": 8.0,
            "cbd_proximity": 3.0,
            "metro_access": False,
            "market_momentum": 5.0,
            "supply_pressure": 3.0,
            "description": "Popular family-oriented neighborhood",
        },
        "Al Muruj": {
            "location_premium": 12.0,
            "cbd_proximity": 6.0,
            "metro_access": True,
            "market_momentum": 7.0,
            "supply_pressure": 0.0,
            "description": "Well-connected residential area",
        },
        "Al Sahafa": {
            "location_premium": 7.0,
            "cbd_proximity": 4.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 2.0,
            "description": "Affordable residential with growing infrastructure",
        },
        "Al Sulaimaniyah": {
            "location_premium": 15.0,
            "cbd_proximity": 12.0,
            "metro_access": True,
            "market_momentum": 6.0,
            "supply_pressure": -1.0,
            "description": "Central location with commercial activity",
        },
        "Al Woroud": {
            "location_premium": 10.0,
            "cbd_proximity": 8.0,
            "metro_access": True,
            "market_momentum": 5.0,
            "supply_pressure": 0.0,
            "description": "Established mixed-use neighborhood",
        },
        "Al Mohammadiyah": {
            "location_premium": 6.0,
            "cbd_proximity": 3.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 3.0,
            "description": "Traditional residential area",
        },
        "Al Narjis": {
            "location_premium": 3.0,
            "cbd_proximity": 0.0,
            "metro_access": False,
            "market_momentum": 5.0,
            "supply_pressure": 5.0,
            "description": "Developing peripheral area with new construction",
        },
        "Al Qirawan": {
            "location_premium": 2.0,
            "cbd_proximity": 0.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 6.0,
            "description": "Emerging residential zone",
        },
        "Al Rabwah": {
            "location_premium": 4.0,
            "cbd_proximity": 2.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 4.0,
            "description": "Established older residential area",
        },
        "Al Rawdah": {
            "location_premium": 5.0,
            "cbd_proximity": 3.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 3.0,
            "description": "Mid-range residential neighborhood",
        },
        "Al Shifa": {
            "location_premium": 2.0,
            "cbd_proximity": 0.0,
            "metro_access": False,
            "market_momentum": 2.0,
            "supply_pressure": 5.0,
            "description": "Budget-friendly residential area",
        },
    },
    "Jeddah": {
        "Al Hamra": {
            "location_premium": 18.0,
            "cbd_proximity": 12.0,
            "metro_access": False,
            "market_momentum": 7.0,
            "supply_pressure": -2.0,
            "description": "Premium waterfront district",
        },
        "Obhur": {
            "location_premium": 20.0,
            "cbd_proximity": 5.0,
            "metro_access": False,
            "market_momentum": 10.0,
            "supply_pressure": -3.0,
            "description": "Exclusive coastal area with luxury developments",
        },
        "Al Shati": {
            "location_premium": 16.0,
            "cbd_proximity": 8.0,
            "metro_access": False,
            "market_momentum": 8.0,
            "supply_pressure": -1.0,
            "description": "Popular beachfront neighborhood",
        },
        "Al Zahra": {
            "location_premium": 12.0,
            "cbd_proximity": 6.0,
            "metro_access": False,
            "market_momentum": 6.0,
            "supply_pressure": 0.0,
            "description": "Central residential area",
        },
        "Al Rawdah": {
            "location_premium": 8.0,
            "cbd_proximity": 4.0,
            "metro_access": False,
            "market_momentum": 5.0,
            "supply_pressure": 2.0,
            "description": "Growing residential district",
        },
        "Al Khalidiyah": {
            "location_premium": 14.0,
            "cbd_proximity": 10.0,
            "metro_access": False,
            "market_momentum": 6.0,
            "supply_pressure": 0.0,
            "description": "Well-established commercial area",
        },
        "Al Salama": {
            "location_premium": 6.0,
            "cbd_proximity": 3.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 3.0,
            "description": "Popular residential zone",
        },
        "Al Safa": {
            "location_premium": 10.0,
            "cbd_proximity": 5.0,
            "metro_access": False,
            "market_momentum": 5.0,
            "supply_pressure": 1.0,
            "description": "Established residential neighborhood",
        },
        "Al Marwah": {
            "location_premium": 5.0,
            "cbd_proximity": 2.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 3.0,
            "description": "Mid-range residential area",
        },
        "Al Naeem": {
            "location_premium": 3.0,
            "cbd_proximity": 0.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 4.0,
            "description": "Budget residential zone",
        },
        "Al Andalus": {
            "location_premium": 4.0,
            "cbd_proximity": 2.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 4.0,
            "description": "Affordable residential neighborhood",
        },
    },
    "Dammam": {
        "Al Shati": {
            "location_premium": 15.0,
            "cbd_proximity": 8.0,
            "metro_access": False,
            "market_momentum": 8.0,
            "supply_pressure": -2.0,
            "description": "Premium waterfront zone",
        },
        "Al Murjan": {
            "location_premium": 12.0,
            "cbd_proximity": 6.0,
            "metro_access": False,
            "market_momentum": 7.0,
            "supply_pressure": -1.0,
            "description": "Upscale residential area",
        },
        "Al Faisaliyah": {
            "location_premium": 8.0,
            "cbd_proximity": 5.0,
            "metro_access": False,
            "market_momentum": 5.0,
            "supply_pressure": 1.0,
            "description": "Central district with good amenities",
        },
        "Al Khalij": {
            "location_premium": 10.0,
            "cbd_proximity": 4.0,
            "metro_access": False,
            "market_momentum": 6.0,
            "supply_pressure": 0.0,
            "description": "Growing coastal neighborhood",
        },
        "Al Rawdah": {
            "location_premium": 5.0,
            "cbd_proximity": 2.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 3.0,
            "description": "Established residential area",
        },
        "Al Anoud": {
            "location_premium": 6.0,
            "cbd_proximity": 3.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 2.0,
            "description": "Popular residential zone",
        },
        "Al Qadisiyah": {
            "location_premium": 5.0,
            "cbd_proximity": 2.0,
            "metro_access": False,
            "market_momentum": 4.0,
            "supply_pressure": 3.0,
            "description": "Mid-range residential neighborhood",
        },
        "Al Nada": {
            "location_premium": 3.0,
            "cbd_proximity": 0.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 4.0,
            "description": "Budget residential area",
        },
        "Al Mazruiyah": {
            "location_premium": 3.0,
            "cbd_proximity": 0.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 5.0,
            "description": "Developing peripheral zone",
        },
        "Ash Shulah": {
            "location_premium": 4.0,
            "cbd_proximity": 1.0,
            "metro_access": False,
            "market_momentum": 3.0,
            "supply_pressure": 4.0,
            "description": "Affordable residential area",
        },
    },
}

# Mega project proximity bonuses
MEGA_PROJECTS = {
    "Riyadh": {
        "King Abdullah Financial District": {
            "nearby_districts": ["Al Olaya", "Al Woroud", "Al Sulaimaniyah"],
            "bonus": 8.0,
        },
        "Diriyah Gate": {
            "nearby_districts": ["Al Yasmin", "Al Malqa"],
            "bonus": 6.0,
        },
        "Riyadh Metro Network": {
            "nearby_districts": ["Al Olaya", "Hittin", "Al Muruj", "Al Nakheel", "Al Sulaimaniyah", "Al Woroud"],
            "bonus": 5.0,
        },
    },
    "Jeddah": {
        "Jeddah Tower": {
            "nearby_districts": ["Obhur", "Al Shati"],
            "bonus": 10.0,
        },
        "Red Sea Project Access": {
            "nearby_districts": ["Al Hamra", "Obhur"],
            "bonus": 7.0,
        },
    },
    "Dammam": {
        "King Fahd Causeway Expansion": {
            "nearby_districts": ["Al Shati", "Al Khalij"],
            "bonus": 5.0,
        },
    },
}


class MarketFactorsEngine:
    """
    Engine for calculating market factor adjustments.
    
    Analyzes location, infrastructure, market dynamics, and 
    development potential to provide value adjustment factors.
    """
    
    def __init__(self):
        """Initialize the market factors engine."""
        pass
    
    def analyze(
        self,
        city: str,
        district: str,
        property_type: str,
        area_sqm: float,
    ) -> MarketFactors:
        """
        Analyze market factors for a property.
        
        Args:
            city: City name
            district: District name
            property_type: apartment, villa, or land
            area_sqm: Property area
            
        Returns:
            MarketFactors with all adjustments
        """
        # Get district characteristics
        city_data = DISTRICT_CHARACTERISTICS.get(city, DISTRICT_CHARACTERISTICS.get("Riyadh", {}))
        district_data = city_data.get(district, {})
        
        # Base location factors
        location_premium = district_data.get("location_premium", 5.0)
        cbd_proximity = district_data.get("cbd_proximity", 3.0)
        
        # Metro access bonus
        metro_bonus = 5.0 if district_data.get("metro_access", False) else 0.0
        
        # Market dynamics
        market_momentum = district_data.get("market_momentum", 4.0)
        supply_pressure = district_data.get("supply_pressure", 0.0)
        
        # Mega project proximity
        mega_bonus = self._get_mega_project_bonus(city, district)
        
        # Development potential (mainly for land)
        dev_potential = 0.0
        if property_type == "land":
            # Larger plots have more development potential
            if area_sqm >= 1000:
                dev_potential = 15.0
            elif area_sqm >= 500:
                dev_potential = 10.0
            elif area_sqm >= 300:
                dev_potential = 5.0
        
        # Combined infrastructure impact
        infrastructure_impact = metro_bonus + mega_bonus
        
        # Calculate combined adjustment
        combined = (
            location_premium 
            + infrastructure_impact 
            + market_momentum 
            + supply_pressure 
            + dev_potential
        ) / 100 * 100  # Convert to percentage
        
        # Build key drivers list
        key_drivers = []
        if location_premium >= 10:
            key_drivers.append(f"Premium location (+{location_premium:.0f}%)")
        if metro_bonus > 0:
            key_drivers.append(f"Metro access (+{metro_bonus:.0f}%)")
        if mega_bonus > 0:
            key_drivers.append(f"Near mega-project (+{mega_bonus:.0f}%)")
        if market_momentum >= 7:
            key_drivers.append(f"Strong market momentum (+{market_momentum:.0f}%)")
        if supply_pressure < 0:
            key_drivers.append(f"Limited supply (+{abs(supply_pressure):.0f}%)")
        if dev_potential > 0:
            key_drivers.append(f"Development potential (+{dev_potential:.0f}%)")
        
        if not key_drivers:
            key_drivers.append("Standard market conditions")
        
        return MarketFactors(
            location_premium_pct=location_premium,
            cbd_proximity_pct=cbd_proximity,
            infrastructure_impact_pct=infrastructure_impact,
            metro_proximity_pct=metro_bonus,
            mega_project_proximity_pct=mega_bonus,
            market_momentum_pct=market_momentum,
            supply_demand_adjustment_pct=supply_pressure,
            development_potential_pct=dev_potential,
            combined_adjustment_pct=combined,
            key_drivers=key_drivers,
        )
    
    def _get_mega_project_bonus(self, city: str, district: str) -> float:
        """Calculate bonus from proximity to mega projects."""
        city_projects = MEGA_PROJECTS.get(city, {})
        total_bonus = 0.0
        
        for project, data in city_projects.items():
            if district in data.get("nearby_districts", []):
                total_bonus = max(total_bonus, data.get("bonus", 0.0))
        
        return total_bonus
    
    def get_district_description(self, city: str, district: str) -> str:
        """Get description for a district."""
        city_data = DISTRICT_CHARACTERISTICS.get(city, {})
        district_data = city_data.get(district, {})
        return district_data.get("description", "Standard residential area")
