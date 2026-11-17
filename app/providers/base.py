from abc import ABC, abstractmethod

class ProviderError(RuntimeError):
    pass

class SportsProvider(ABC):
    name: str

    @abstractmethod
    async def fetch_games(self) -> list[dict]:
        """Return canonical game dictionaries; provider-specific raw payload is retained."""
        raise NotImplementedError
