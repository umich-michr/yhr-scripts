import oracledb
from sqlalchemy import create_engine
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, username: str, password: str, dsn: str) -> None:
        """Initialize database client with credentials."""
        self.username = username
        self.password = password
        self.dsn = dsn
        logger.debug(f"dsn: {dsn}")
        self.engine: Optional[object] = None

    def connect(self) -> 'DatabaseClient':
        """Establish database connection."""
        try:
            host, port_service = self.dsn.split(":")
            port, service = port_service.split("/")
            self.engine = create_engine(f"oracle+oracledb://{self.username}:{self.password}@{host}:{port}/?service_name={service}")
            return self
        except Exception as e:
            logger.error(f"Exception occurred: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e

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

    def close(self) -> None:
        """Close database connection."""
        # No need to close the engine explicitly
        pass

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass

class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""
    pass
