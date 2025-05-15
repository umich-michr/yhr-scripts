from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from src.processor import (
    enrich_row,
    process_and_write_rows,
    process_row,
    save_row,
    write_headers,
)


@pytest.fixture
def sample_dataframe():
    """Return a sample DataFrame for testing."""
    return pd.DataFrame(
        {"SOURCE_ADDRESS": ["192.168.1.1", "8.8.8.8"], "DATA": ["data1", "data2"]}
    )


@pytest.fixture
def geo_client_mock():
    """Return a mock geolocation client."""
    mock_client = MagicMock()
    mock_client.get_geolocation.side_effect = lambda ip: {
        "city": "City-" + ip,
        "region": "Region-" + ip,
        "country": "Country-" + ip,
        "postal": "Postal-" + ip,
        "org": "Org-" + ip,
    }
    return mock_client


def test_write_headers():
    """Test that headers are written correctly."""
    columns = ["COLUMN1", "COLUMN2"]
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        with open("mock_output.csv", "w") as f:
            write_headers(columns, f)

    mock_file().write.assert_called_once_with("COLUMN1,COLUMN2\n")


def test_enrich_row():
    """Test that a row is enriched with geolocation data."""
    row = {"SOURCE_ADDRESS": "192.168.1.1", "DATA": "data1"}
    geolocation_data = {
        "city": "Test City",
        "region": "Test Region",
        "country": "Test Country",
        "postal": "12345",
        "org": "Test Org",
    }
    enriched_row = enrich_row(row, geolocation_data)

    assert enriched_row["CITY"] == "Test City"
    assert enriched_row["REGION"] == "Test Region"
    assert enriched_row["COUNTRY"] == "Test Country"
    assert enriched_row["POSTAL"] == "12345"
    assert enriched_row["ORG"] == "Test Org"


def test_save_row():
    """Test that a row is saved correctly to the file."""
    row = {"COLUMN1": "value1", "COLUMN2": "value2"}
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        with open("mock_output.csv", "w") as f:
            save_row(row, f)

    # Validate that the correct content was written to the file
    mock_file().write.assert_called_once_with("value1,value2\n")


def test_process_row(geo_client_mock):
    """Test that a single row is processed and saved correctly."""
    row = {"SOURCE_ADDRESS": "192.168.1.1", "DATA": "data1"}
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        with open("mock_output.csv", "w") as f:
            process_row(row, geo_client_mock, f)

    geo_client_mock.get_geolocation.assert_called_once_with("192.168.1.1")
    # Validate that the enriched row was written to the file
    mock_file().write.assert_called_once_with(
        "192.168.1.1,data1,City-192.168.1.1,Region-192.168.1.1,Country-192.168.1.1,Postal-192.168.1.1,Org-192.168.1.1\n"
    )


def test_process_and_write_rows(sample_dataframe, geo_client_mock):
    """Test that all rows in a DataFrame are processed and written to a file."""
    mock_file = mock_open()
    with patch("builtins.open", mock_file):
        process_and_write_rows(sample_dataframe, geo_client_mock)

    # Verify headers are written once
    mock_file().write.assert_any_call("SOURCE_ADDRESS,DATA\n")

    # Verify rows are processed
    assert geo_client_mock.get_geolocation.call_count == 2
    assert mock_file().write.call_count == 3  # 1 header + 2 rows
