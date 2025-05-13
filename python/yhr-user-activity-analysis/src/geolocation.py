import requests
import time
from typing import Dict

class GeolocationClient:
    def __init__(self, base_url: str = "https://ipapi.co", rate_limit_delay: float = 0.1) -> None:
        """Initialize geolocation client."""
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay

    def get_geolocation(self, ip: str) -> Dict[str, str]:
        """Fetch geolocation data for a single IP address."""
        try:
            response = requests.get(f"{self.base_url}/{ip}/json/")
            response.raise_for_status()
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country_name', 'Unknown'),
                'postal': data.get('postal', 'Unknown'),
                'org': data.get('org', 'Unknown')
            }
        except requests.RequestException:
            return {
                'city': 'Unknown',
                'region': 'Unknown',
                'country': 'Unknown',
                'postal': 'Unknown',
                'org': 'Unknown'
            }
        finally:
            time.sleep(self.rate_limit_delay)

    def get_geolocations(self, ip_addresses: list[str]) -> Dict[str, Dict[str, str]]:
        """Fetch geolocation data for multiple IP addresses."""
        return {ip: self.get_geolocation(ip) for ip in ip_addresses}
