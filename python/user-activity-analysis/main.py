import sys
import csv
import argparse
from src.config import load_config, get_dsn
from src.database import DatabaseClient, QueryExecutionError, DatabaseConnectionError
from src.query_builder import build_database_query
import logging
from logger import configure_logging
from src.ip_lookup.geolocation import GeolocationClient
from src.row_enricher.geolocation_enricher import GeolocationEnricher

configure_logging()
logger = logging.getLogger(__name__)

def get_enrichers(config):
    geo_client = GeolocationClient.from_config(config)
    enrichers = [GeolocationEnricher(geo_client)]
    # enrichers.append(BlacklistEnricher(...))  # add more as needed
    return enrichers

def enrich_row(row, enrichers):
    # First convert all input keys to uppercase to ensure consistent case
    row = {k.upper(): v for k, v in row.items()}
    
    # Apply enrichers
    for enricher in enrichers:
        row = enricher.enrich(row)
    
    # Convert all keys to uppercase again after enrichment to ensure consistency
    return {k.upper(): v for k, v in row.items()}

def get_output_fieldnames(first_row, enrichers):
    # Collect all enrichment fields from enrichers
    enrichment_fields = []
    for enricher in enrichers:
        enrichment_fields.extend(enricher.header_fields)
    
    # Create a set of uppercase enrichment fields for case-insensitive comparison
    enrichment_fields_upper = [f.upper() for f in enrichment_fields]
    
    # Only include fields that are not already in the enrichment fields (case-insensitive comparison)
    original_fields = [f for f in first_row.keys() if f.upper() not in enrichment_fields_upper]
    
    # Convert original fields to uppercase
    original_fields_upper = [f.upper() for f in original_fields]
    
    # Append enrichment fields at the end
    return original_fields_upper + enrichment_fields

# This function is now incorporated into enrich_row
# Keeping it here commented out for reference
# def convert_keys_to_uppercase(row):
#    """Convert all dictionary keys to uppercase for CSV output."""
#    return {k.upper(): v for k, v in row.items()}

def main():
    parser = argparse.ArgumentParser(description="Stream user activity analysis to CSV.")
    parser.add_argument("study_id", type=int, nargs="?", help="Study ID to filter the query (optional, runs for all studies if omitted)")
    args = parser.parse_args()

    try:
        # Load config from .env and environment
        config = load_config()
        enrichers = get_enrichers(config)
        geo_client = GeolocationClient.from_config(config)

        dsn = get_dsn(config)
        user = config["db_username"]
        password = config["db_password"]

        queries_dir = "src/queries"  
        backup_schema = config["backup_schema_name"]  
        query = build_database_query(backup_schema, queries_dir)

        # If study_id is provided, use it; else, remove the study_id filter from the query
        if args.study_id is not None:
            params = {"study_id": args.study_id}
        else:
            # Remove the study_id filter from the query
            query = query.replace("AND v.study_id = :study_id", "")
            params = {}

        logger.debug("Executing SQL query:\n%s", query)
        logger.debug("With parameters: %s", params)

        # Create database client and stream rows
        db = DatabaseClient.from_credentials(user, password, dsn)
        rows = db.stream_rows(query, params)
        first_row = next(rows, None)
        if first_row is None:
            return
        
        # Enrich the first row (with consistent uppercase keys)
        enriched_first_row = enrich_row(first_row, enrichers)
        
        # Get the fieldnames from the enriched row (already uppercase)
        fieldnames = get_output_fieldnames(enriched_first_row, enrichers)
        
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        sys.stdout.flush()

        # Write the first row (keys are already uppercase from enrich_row)
        writer.writerow(enriched_first_row)
        sys.stdout.flush()

        for row in rows:
            # Enrich row (will convert keys to uppercase)
            enriched_row = enrich_row(row, enrichers)
            # Write row (keys are already uppercase from enrich_row)
            writer.writerow(enriched_row)
            sys.stdout.flush()
    except (DatabaseConnectionError, QueryExecutionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()