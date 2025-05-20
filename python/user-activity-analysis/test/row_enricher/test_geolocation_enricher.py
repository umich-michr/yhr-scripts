import pytest
from unittest.mock import MagicMock
from src.row_enricher.geolocation_enricher import GeolocationEnricher, GEO_FIELDS

@pytest.fixture
def mock_geo_client():
    client = MagicMock()
    client.get_geolocation.side_effect = lambda ip: {
        "city": f"city_{ip}" if ip else "Unknown",
        "region": f"region_{ip}" if ip else "Unknown",
        "country": f"country_{ip}" if ip else "Unknown",
        "postal": f"postal_{ip}" if ip else "Unknown",
        "org": f"org_{ip}" if ip else "Unknown",
    }
    return client

def test_enrich_both_ips_different(mock_geo_client):
    enricher = GeolocationEnricher(mock_geo_client)
    row = {
        "INTEREST_SOURCE_ADDRESS": "1.1.1.1",
        "ACTIVATION_SOURCE_ADDRESS": "2.2.2.2"
    }
    enriched = enricher.enrich(row.copy())
    assert enriched["INTEREST_CITY"] == "city_1.1.1.1"
    assert enriched["ACTIVATION_CITY"] == "city_2.2.2.2"
    assert enriched["INTEREST_ORG"] == "org_1.1.1.1"
    assert enriched["ACTIVATION_ORG"] == "org_2.2.2.2"

def test_enrich_ips_same(mock_geo_client):
    enricher = GeolocationEnricher(mock_geo_client)
    row = {
        "INTEREST_SOURCE_ADDRESS": "3.3.3.3",
        "ACTIVATION_SOURCE_ADDRESS": "3.3.3.3"
    }
    enriched = enricher.enrich(row.copy())
    assert enriched["INTEREST_CITY"] == "city_3.3.3.3"
    assert enriched["ACTIVATION_CITY"] == "city_3.3.3.3"

def test_enrich_interest_ip_only(mock_geo_client):
    enricher = GeolocationEnricher(mock_geo_client)
    row = {
        "INTEREST_SOURCE_ADDRESS": "4.4.4.4",
        "ACTIVATION_SOURCE_ADDRESS": ""
    }
    enriched = enricher.enrich(row.copy())
    assert enriched["INTEREST_CITY"] == "city_4.4.4.4"
    assert enriched["ACTIVATION_CITY"] == "city_4.4.4.4"

def test_enrich_missing_ips(mock_geo_client):
    enricher = GeolocationEnricher(mock_geo_client)
    row = {}
    enriched = enricher.enrich(row.copy())
    assert enriched["INTEREST_CITY"] == "Unknown"
    assert enriched["ACTIVATION_CITY"] == "Unknown"

def test_header_fields_property(mock_geo_client):
    enricher = GeolocationEnricher(mock_geo_client)
    assert isinstance(enricher.header_fields, list)
    for field in GEO_FIELDS:
        assert field in enricher.header_fields