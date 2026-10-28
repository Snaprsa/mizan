"""
BaseProvider — Interface for comparable discovery providers (Stage 4).

Providers search external data sources for comparable properties.
Designed as a plugin system — each provider implements this interface.

COMPLIANCE RULES:
- Do NOT scrape sites that prohibit it in their ToS
- Prefer official APIs where available
- Support user-assisted ingestion as fallback
- Internal data sources are always acceptable
"""

from abc import ABC, abstractmethod

from schemas._future import CandidateComparable, ProviderSearchCriteria


class BaseProvider(ABC):
    """
    All providers implement this interface.

    Planned providers:
    - AqarProvider: sa.aqar.fm (check API/ToS)
    - PasteahProvider: pasteah.com (check API/ToS)
    - AqarsasProvider: aqarsas.com (check API/ToS)
    - ManualProvider: User-entered comps
    - InternalProvider: Historical data from past valuations
    """

    name: str = "base"
    version: str = "0.0.0"
    requires_api_key: bool = False

    @abstractmethod
    async def search(self, criteria: ProviderSearchCriteria) -> list[CandidateComparable]:
        """Search for comparable properties matching criteria."""
        ...

    @abstractmethod
    async def fetch_details(self, external_id: str) -> dict:
        """Fetch full details for a specific listing/transaction."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and reachable."""
        ...


# === Provider Stubs ===

class AqarProvider(BaseProvider):
    """Aqar.fm provider — TODO: Implement in Stage 4."""
    name = "aqar"
    version = "0.0.0"

    async def search(self, criteria: ProviderSearchCriteria) -> list[CandidateComparable]:
        raise NotImplementedError("AqarProvider not yet implemented (Stage 4)")

    async def fetch_details(self, external_id: str) -> dict:
        raise NotImplementedError("AqarProvider not yet implemented (Stage 4)")

    def is_available(self) -> bool:
        return False


class PasteahProvider(BaseProvider):
    """Pasteah provider — TODO: Implement in Stage 4."""
    name = "pasteah"
    version = "0.0.0"

    async def search(self, criteria: ProviderSearchCriteria) -> list[CandidateComparable]:
        raise NotImplementedError("PasteahProvider not yet implemented (Stage 4)")

    async def fetch_details(self, external_id: str) -> dict:
        raise NotImplementedError("PasteahProvider not yet implemented (Stage 4)")

    def is_available(self) -> bool:
        return False


class AqarsasProvider(BaseProvider):
    """Aqarsas provider — TODO: Implement in Stage 4."""
    name = "aqarsas"
    version = "0.0.0"

    async def search(self, criteria: ProviderSearchCriteria) -> list[CandidateComparable]:
        raise NotImplementedError("AqarsasProvider not yet implemented (Stage 4)")

    async def fetch_details(self, external_id: str) -> dict:
        raise NotImplementedError("AqarsasProvider not yet implemented (Stage 4)")

    def is_available(self) -> bool:
        return False


class ManualProvider(BaseProvider):
    """User-entered comparables — always available."""
    name = "manual"
    version = "1.0.0"

    async def search(self, criteria: ProviderSearchCriteria) -> list[CandidateComparable]:
        return []  # Manual entry doesn't search

    async def fetch_details(self, external_id: str) -> dict:
        return {}  # User provides all data

    def is_available(self) -> bool:
        return True  # Always available
