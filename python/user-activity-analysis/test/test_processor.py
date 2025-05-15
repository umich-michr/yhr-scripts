import pandas as pd

from src.processor import enrich_dataframe, save_dataframe


def test_enrich_dataframe():
    # Create a sample DataFrame
    df = pd.DataFrame({"SOURCE_ADDRESS": ["192.168.1.1", "8.8.8.8"]})

    # Create sample geolocation data
    geolocation_data = {
        "192.168.1.1": {
            "city": "New York",
            "region": "NY",
            "country": "US",
            "postal": "10001",
            "org": "Example Org",
        },
        "8.8.8.8": {
            "city": "Mountain View",
            "region": "CA",
            "country": "US",
            "postal": "94043",
            "org": "Google",
        },
    }

    # Enrich the DataFrame
    enriched_df = enrich_dataframe(df, geolocation_data)

    # Verify the enriched DataFrame
    assert enriched_df.shape == (2, 6)
    assert enriched_df["city"].tolist() == ["New York", "Mountain View"]
    assert enriched_df["region"].tolist() == ["NY", "CA"]
    assert enriched_df["country"].tolist() == ["US", "US"]
    assert enriched_df["postal"].tolist() == ["10001", "94043"]
    assert enriched_df["org"].tolist() == ["Example Org", "Google"]


def test_enrich_dataframe_missing_ip():
    # Create a sample DataFrame
    df = pd.DataFrame({"SOURCE_ADDRESS": ["192.168.1.1", "8.8.8.8"]})

    # Create sample geolocation data (missing one IP)
    geolocation_data = {
        "192.168.1.1": {
            "city": "New York",
            "region": "NY",
            "country": "US",
            "postal": "10001",
            "org": "Example Org",
        }
    }

    # Enrich the DataFrame
    enriched_df = enrich_dataframe(df, geolocation_data)

    # Verify the enriched DataFrame
    expected_values = {
        "192.168.1.1": {
            "city": "New York",
            "region": "NY",
            "country": "US",
            "postal": "10001",
            "org": "Example Org",
        },
        "8.8.8.8": {
            "city": "unknown",
            "region": "unknown",
            "country": "unknown",
            "postal": "unknown",
            "org": "unknown",
        },
    }

    for field in ["city", "region", "country", "postal", "org"]:
        assert enriched_df[field].tolist() == [
            expected_values[ip][field] for ip in df["SOURCE_ADDRESS"]
        ]


def test_save_dataframe(tmp_path):
    # Create a sample DataFrame
    df = pd.DataFrame({"SOURCE_ADDRESS": ["192.168.1.1", "8.8.8.8"]})

    # Save the DataFrame to a CSV file
    output_path = tmp_path / "output.csv"
    save_dataframe(df, output_path)

    # Verify the CSV file exists
    assert output_path.exists()

    # Verify the CSV file contents
    saved_df = pd.read_csv(output_path)
    assert saved_df.equals(df)


def test_save_dataframe_overwrite(tmp_path):
    # Create a sample DataFrame
    df = pd.DataFrame({"SOURCE_ADDRESS": ["192.168.1.1", "8.8.8.8"]})

    # Save the DataFrame to a CSV file
    output_path = tmp_path / "output.csv"
    save_dataframe(df, output_path)

    # Save the DataFrame again (should overwrite)
    save_dataframe(df, output_path)

    # Verify the CSV file exists
    assert output_path.exists()

    # Verify the CSV file contents
    saved_df = pd.read_csv(output_path)
    assert saved_df.equals(df)
