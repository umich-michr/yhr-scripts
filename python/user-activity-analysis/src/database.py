import logging
from typing import Any, Dict, Iterator

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""


class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""


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
            engine = create_engine(
                f"oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service}"
            )
        except Exception as e:
            logger.error(f"Caught exception: {type(e).__name__}: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e
        return cls(engine)

    def stream_rows(self, query: str, params: dict) -> Iterator[Dict[str, Any]]:
        """Stream rows from the database as dictionaries."""
        try:
            with self.engine.connect() as conn:
                result = conn.execution_options(stream_results=True).execute(
                    text(query), params
                )
                columns = result.keys()
                for row in result:
                    yield dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Query execution failed: {e}") from e
