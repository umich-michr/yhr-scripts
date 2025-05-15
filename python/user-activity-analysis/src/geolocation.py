import time
from typing import Dict

import requests


class GeolocationClient:
    def __init__(
        self, base_url: str, api_key: str, rate_limit_delay: float = 0.1
    ) -> None:
        """Initialize geolocation client."""
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay

    @classmethod
    def from_config(cls, config: Dict[str, str]) -> "GeolocationClient":
        """Create a GeolocationClient instance from configuration."""
        return cls(
            base_url="https://ipapi.co",
            api_key=config["ip_lookup_api_key"],
            rate_limit_delay=0.1,
        )

    def get_geolocation(self, ip: str) -> Dict[str, str]:
        """Fetch geolocation data for a single IP address."""
        try:
            response = requests.get(f"{self.base_url}/{ip}/json/?key={self.api_key}")
            response.raise_for_status()
            data = response.json()
            return {
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "postal": data.get("postal", "Unknown"),
                "org": data.get("org", "Unknown"),
            }
        except requests.RequestException:
            return {
                "city": "Unknown",
                "region": "Unknown",
                "country": "Unknown",
                "postal": "Unknown",
                "org": "Unknown",
            }
        finally:
            time.sleep(self.rate_limit_delay)

    def get_geolocations(self, ip_addresses: list[str]) -> Dict[str, Dict[str, str]]:
        """Fetch geolocation data for multiple IP addresses."""
        return {ip: self.get_geolocation(ip) for ip in ip_addresses}
