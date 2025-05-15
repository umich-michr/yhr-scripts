import logging

logger = logging.getLogger(__name__)

OUTPUT_FILE = "enriched_output.csv"


def process_and_write_rows(df, geo_client):
    """Process each row and write the enriched data to the output file."""
    if df.empty:
        logger.info("No rows returned from the query.")
        return

    if "SOURCE_ADDRESS" not in df.columns:
        logger.error("The 'SOURCE_ADDRESS' column does not exist in the DataFrame.")
        logger.error(f"Available columns: {df.columns}")
        return

    with open(OUTPUT_FILE, "w") as output_file:
        write_headers(df.columns, output_file)

        for _, row in df.iterrows():
            process_row(row, geo_client, output_file)


def write_headers(columns, output_file):
    output_file.write(",".join(columns) + "\n")


def process_row(row, geo_client, output_file):
    """Process a single row and write the enriched data to the output file."""
    source_address = row["SOURCE_ADDRESS"]
    geolocation_data = geo_client.get_geolocation(source_address)
    enriched_row = enrich_row(row, geolocation_data)
    save_row(enriched_row, output_file)


def enrich_row(row, geolocation_data):
    row["CITY"] = geolocation_data.get("city", "Unknown")
    row["REGION"] = geolocation_data.get("region", "Unknown")
    row["COUNTRY"] = geolocation_data.get("country", "Unknown")
    row["POSTAL"] = geolocation_data.get("postal", "Unknown")
    row["ORG"] = geolocation_data.get("org", "Unknown")
    return row


def save_row(row, output_file):
    # Convert the row to a dictionary if it's a pandas Series
    if not isinstance(row, dict):
        row = row.to_dict()

    output_file.write(",".join(map(str, row.values())) + "\n")
