import os
from typing import Dict, List, Optional

from dotenv import load_dotenv


def load_config(
    required_vars: Optional[List[str]] = None, optional_vars: Optional[List[str]] = None
) -> Dict[str, str]:
    """Load and validate environment variables."""
    load_dotenv()
    if required_vars is None:
        required_vars = [
            "DB_USERNAME",
            "DB_PASSWORD",
            "DB_HOST",
            "DB_PORT",
            "DB_SERVICE_NAME",
        ]

    if optional_vars is None:
        optional_vars = ["IP_LOOKUP_API_KEY"]

    _validate_environment_variables(required_vars)

    config = _load_environment_variables(required_vars)
    config.update(_load_environment_variables(optional_vars))

    return config


def _validate_environment_variables(required_vars: List[str]) -> None:
    """Validate that required environment variables are set."""
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(
            f"Missing environment variables: {
                ', '.join(missing_vars)}"
        )


def _load_environment_variables(vars: List[str]) -> Dict[str, str]:
    """Load environment variables into a dictionary."""
    return {var.lower(): os.environ[var] for var in vars if var in os.environ}


def get_dsn(config: Dict[str, str]) -> str:
    """Construct the DSN from configuration."""
    return f"{config['db_host']}:{config['db_port']}/{config['db_service_name']}"
