from typing import Dict, Any

#To be used like an interface
class IpEnricher:
    def enrich(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich the row with additional attributes."""
        raise NotImplementedError

    @property
    def header_fields(self) -> list:
        """Return the list of new header fields this enricher adds."""
        raise NotImplementedError