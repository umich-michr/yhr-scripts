from dotenv import load_dotenv
import os
from typing import Optional, List, Dict

def load_config(required_vars: Optional[List[str]] = None) -> Dict[str, str]:
    """Load and validate environment variables."""
    load_dotenv()
    if required_vars is None:
        required_vars = ['DB_USERNAME', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_SERVICE_NAME']

    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

    return {
        'db_username': os.environ['DB_USERNAME'],
        'db_password': os.environ['DB_PASSWORD'],
        'db_host': os.environ['DB_HOST'],
        'db_port': os.environ['DB_PORT'],
        'db_service_name': os.environ['DB_SERVICE_NAME']
    }

def get_dsn(config: Dict[str, str]) -> str:
    """Construct the DSN from configuration."""
    return f"{config['db_host']}:{config['db_port']}/{config['db_service_name']}"
