import logging
from logger import configure_logging
from src.config import load_config, get_dsn
from src.database import DatabaseClient
from src.geolocation import GeolocationClient
from src.processor import enrich_dataframe, save_dataframe
from src.queries import STUDY_INTEREST_QUERY

logger = logging.getLogger(__name__)

def main():
    """Main function to orchestrate the program."""
    try:
        # Load configuration
        config = load_config()
        dsn = get_dsn(config)

        # Initialize clients
        db_client = DatabaseClient.from_credentials(
            username=config['db_username'],
            password=config['db_password'],
            dsn=dsn
        )
        geo_client = GeolocationClient.from_config(config)

        df = db_client.execute_query(STUDY_INTEREST_QUERY)
        df.columns = [col.upper() for col in df.columns]

        # Check if the DataFrame is empty
        if df.empty:
            logger.info("No rows returned from the query.")
            return

        # Check if the 'SOURCE_ADDRESS' column exists
        if 'SOURCE_ADDRESS' not in df.columns:
            logger.error("The 'SOURCE_ADDRESS' column does not exist in the DataFrame.")
            logger.error("Available columns:", df.columns)
            return

        # Process data
        unique_ips = df['SOURCE_ADDRESS'].unique()
        logger.info("Checking locations for IP addresses...")
        geolocation_data = geo_client.get_geolocations(unique_ips)
        logger.info("Finished collecting locations for IP addresses")
        enriched_df = enrich_dataframe(df, geolocation_data)
        logger.debug("Enriched db data with locations for IP addresses")
        save_dataframe(enriched_df, 'enriched_output.csv')
        #save_dataframe(df, 'enriched_output.csv')

        print("Processing complete. Output saved to enriched_output.csv")
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
