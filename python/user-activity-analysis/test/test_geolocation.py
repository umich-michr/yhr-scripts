from unittest.mock import MagicMock, patch

import pytest
import requests

from src.geolocation import GeolocationClient


@pytest.fixture
def geo_client():
    """Fixture for GeolocationClient instance."""
    return GeolocationClient.from_config({"ip_lookup_api_key": "test_api_key"})


def test_init_default():
    """Test initialization with default parameters."""
    client = GeolocationClient.from_config({"ip_lookup_api_key": "test_api_key"})
    assert client.base_url == "https://ipapi.co"
    assert client.api_key == "test_api_key"
    assert client.rate_limit_delay == 0.1


def test_get_geolocation_success(geo_client):
    """Test successful geolocation lookup."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "city": "San Francisco",
        "region": "California",
        "country_name": "United States",
        "postal": "94105",
        "org": "ExampleOrg",
    }
    with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.return_value = mock_response
        result = geo_client.get_geolocation("1.2.3.4")
        assert result == {
            "city": "San Francisco",
            "region": "California",
            "country": "United States",
            "postal": "94105",
            "org": "ExampleOrg",
        }
        mock_get.assert_called_once_with(
            "https://ipapi.co/1.2.3.4/json/?key=test_api_key"
        )
        mock_sleep.assert_called_once_with(0.1)


def test_get_geolocation_request_error(geo_client):
    """Test geolocation failure returns default values."""
    with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.side_effect = requests.RequestException("Network error")
        result = geo_client.get_geolocation("1.2.3.4")
        assert result == {
            "city": "Unknown",
            "region": "Unknown",
            "country": "Unknown",
            "postal": "Unknown",
            "org": "Unknown",
        }
        mock_get.assert_called_once_with(
            "https://ipapi.co/1.2.3.4/json/?key=test_api_key"
        )
        mock_sleep.assert_called_once_with(0.1)


def test_get_geolocations_success(geo_client):
    """Test successful geolocation lookup for multiple IPs."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "city": "San Francisco",
        "region": "California",
        "country_name": "United States",
        "postal": "94105",
        "org": "ExampleOrg",
    }
    with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.return_value = mock_response
        result = geo_client.get_geolocations(["1.2.3.4", "5.6.7.8"])
        assert result == {
            "1.2.3.4": {
                "city": "San Francisco",
                "region": "California",
                "country": "United States",
                "postal": "94105",
                "org": "ExampleOrg",
            },
            "5.6.7.8": {
                "city": "San Francisco",
                "region": "California",
                "country": "United States",
                "postal": "94105",
                "org": "ExampleOrg",
            },
        }
        mock_get.assert_any_call("https://ipapi.co/1.2.3.4/json/?key=test_api_key")
        mock_get.assert_any_call("https://ipapi.co/5.6.7.8/json/?key=test_api_key")
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 2


def test_get_geolocations_empty(geo_client):
    """Test geolocation lookup with empty IP list."""
    with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
        result = geo_client.get_geolocations([])
        assert result == {}
        mock_get.assert_not_called()
        mock_sleep.assert_not_called()
