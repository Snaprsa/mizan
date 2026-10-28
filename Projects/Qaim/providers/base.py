"""Provider interface — base class for Stage 4 comparable discovery providers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseProvider(ABC):
    """Abstract base for real estate listing/transaction data providers.
    
    Stage 4 will implement concrete providers (Aqar, Pasteah, Aqarsas, etc.)
    that fetch comparable property data from external sources.
    
    Design rules:
    - No ToS-violating scraping
    - Support user-assisted ingestion as fallback
    - All results must carry source attribution
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Source classification (marketplace, official, broker, etc.)."""
        pass
    
    @abstractmethod
    async def search(
        self,
        city: str,
        district: Optional[str] = None,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Search for comparable properties. Returns list of raw results."""
        pass
    
    @abstractmethod
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get a single listing by ID."""
        pass
    
    @abstractmethod
    def get_reliability_score(self) -> int:
        """Return the reliability score (1-5) for this provider's data."""
        pass


class AqarProvider(BaseProvider):
    """Aqar.fm provider — Stage 4 placeholder."""
    
    @property
    def name(self) -> str:
        return "Aqar"
    
    @property
    def source_type(self) -> str:
        return "marketplace"
    
    async def search(self, city: str, **kwargs) -> List[Dict[str, Any]]:
        # TODO: Stage 4 — implement Aqar API integration or user-assisted ingestion
        raise NotImplementedError("Aqar provider not yet implemented (Stage 4)")
    
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Aqar provider not yet implemented (Stage 4)")
    
    def get_reliability_score(self) -> int:
        return 2  # Marketplace listing


class PasteahProvider(BaseProvider):
    """Pasteah provider — Stage 4 placeholder."""
    
    @property
    def name(self) -> str:
        return "Pasteah"
    
    @property
    def source_type(self) -> str:
        return "marketplace"
    
    async def search(self, city: str, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError("Pasteah provider not yet implemented (Stage 4)")
    
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Pasteah provider not yet implemented (Stage 4)")
    
    def get_reliability_score(self) -> int:
        return 2


class AqarsasProvider(BaseProvider):
    """Aqarsas provider — Stage 4 placeholder."""
    
    @property
    def name(self) -> str:
        return "Aqarsas"
    
    @property
    def source_type(self) -> str:
        return "official"
    
    async def search(self, city: str, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError("Aqarsas provider not yet implemented (Stage 4)")
    
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Aqarsas provider not yet implemented (Stage 4)")
    
    def get_reliability_score(self) -> int:
        return 4  # Official filing data


class ManualIngestProvider(BaseProvider):
    """User-assisted ingestion — allows manual data entry as a provider."""
    
    @property
    def name(self) -> str:
        return "ManualIngest"
    
    @property
    def source_type(self) -> str:
        return "manual"
    
    async def search(self, city: str, **kwargs) -> List[Dict[str, Any]]:
        return []  # Manual provider doesn't search
    
    async def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        return None
    
    def get_reliability_score(self) -> int:
        return 1  # User-entered
