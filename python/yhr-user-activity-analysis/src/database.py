import oracledb
from sqlalchemy import create_engine
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass

class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""
    pass

class DatabaseClient:
    def __init__(self, engine):
        """Initialize database client with engine."""
        self.engine = engine

    @classmethod
    def from_credentials(cls, username: str, password: str, dsn: str):
        """Create a DatabaseClient instance from credentials."""
        logger.debug(f"Creating database client with DSN: {dsn}")
        try:
            host, port_service = dsn.split(":")
            port, service = port_service.split("/")
            logger.debug(f"Host: {host}, Port: {port}, Service: {service}")
        except Exception as e:
            logger.error(f"Caught exception: {type(e).__name__}: {e}")
            raise DatabaseConnectionError(f"Invalid DSN format: {dsn}") from e
        try:
            engine = create_engine(f"oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service}")
        except Exception as e:
            logger.error(f"Caught exception: {type(e).__name__}: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e
        return cls(engine)

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame."""
        if not self.engine:
            raise DatabaseConnectionError("No active database connection")
        try:
            with self.engine.connect() as connection:
                df = pd.read_sql(query, connection)
                df.columns = [col.lower() for col in df.columns]
                return df
        except Exception as e:
            raise QueryExecutionError(f"Query execution failed: {e}") from e
