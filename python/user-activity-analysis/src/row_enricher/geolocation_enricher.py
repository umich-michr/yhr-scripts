import logging
from .ipenricher import IpEnricher

logger = logging.getLogger(__name__)

GEO_FIELDS = [
    "INTEREST_CITY", "INTEREST_REGION", "INTEREST_COUNTRY", "INTEREST_POSTAL", "INTEREST_ORG",
    "ACTIVATION_CITY", "ACTIVATION_REGION", "ACTIVATION_COUNTRY", "ACTIVATION_POSTAL", "ACTIVATION_ORG"
]

class GeolocationEnricher(IpEnricher):
    def __init__(self, geo_client):
        self.geo_client = geo_client

    @property
    def header_fields(self):
        return GEO_FIELDS

    def enrich(self, row):
        interest_ip = row.get("INTEREST_SOURCE_ADDRESS")
        activation_ip = row.get("ACTIVATION_SOURCE_ADDRESS")
        logger.debug(f"Enriching IPs: {interest_ip}, {activation_ip}")

        interest_geo = self.geo_client.get_geolocation(interest_ip)
        row["INTEREST_CITY"] = interest_geo.get("city", "Unknown")
        row["INTEREST_REGION"] = interest_geo.get("region", "Unknown")
        row["INTEREST_COUNTRY"] = interest_geo.get("country", "Unknown")
        row["INTEREST_POSTAL"] = interest_geo.get("postal", "Unknown")
        row["INTEREST_ORG"] = interest_geo.get("org", "Unknown")

        if activation_ip and activation_ip != interest_ip:
            activation_geo = self.geo_client.get_geolocation(activation_ip)
        else:
            activation_geo = interest_geo

        row["ACTIVATION_CITY"] = activation_geo.get("city", "Unknown")
        row["ACTIVATION_REGION"] = activation_geo.get("region", "Unknown")
        row["ACTIVATION_COUNTRY"] = activation_geo.get("country", "Unknown")
        row["ACTIVATION_POSTAL"] = activation_geo.get("postal", "Unknown")
        row["ACTIVATION_ORG"] = activation_geo.get("org", "Unknown")
        return row