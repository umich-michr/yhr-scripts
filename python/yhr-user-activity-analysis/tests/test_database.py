
import pytest
import pandas as pd
from src.database import DatabaseClient, DatabaseConnectionError, QueryExecutionError
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_engine():
    """Fixture for mock engine."""
    return MagicMock()

def test_execute_query_success(mock_engine):
    """Test successful query execution."""
    with patch('pandas.read_sql') as mock_read_sql:
        mock_df = pd.DataFrame({'study_id': [1]})
        mock_read_sql.return_value = mock_df
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()
        db_client = DatabaseClient(mock_engine)
        result = db_client.execute_query("SELECT * FROM table")
        pd.testing.assert_frame_equal(result, mock_df)
        mock_read_sql.assert_called_once()

def test_execute_query_no_connection():
    """Test query execution fails without connection."""
    db_client = DatabaseClient(None)
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db_client.execute_query("SELECT * FROM table")
    assert "No active database connection" in str(exc_info.value)

def test_execute_query_failure(mock_engine):
    """Test query execution failure raises QueryExecutionError."""
    with patch('pandas.read_sql') as mock_read_sql:
        mock_read_sql.side_effect = Exception("Query failed")
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()
        db_client = DatabaseClient(mock_engine)
        with pytest.raises(QueryExecutionError) as exc_info:
            db_client.execute_query("SELECT * FROM table")
        assert "Query execution failed" in str(exc_info.value)

def test_from_credentials_success():
    """Test creating DatabaseClient instance from credentials."""
    with patch('sqlalchemy.create_engine') as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        db_client = DatabaseClient.from_credentials("username", "password", "localhost:1521/service")
        url = str(db_client.engine.url)
        assert "oracle+oracledb://" in url
        assert "@localhost:1521/?service_name=service" in url

def test_from_credentials_failure_invalid_dsn():
    """Test creating DatabaseClient instance from invalid DSN."""
    with pytest.raises(DatabaseConnectionError) as exc_info:
        DatabaseClient.from_credentials("username", "password", "invalid_dsn")
    assert "Invalid DSN format" in str(exc_info.value)

def test_from_credentials_failure_connection_error():
    """Test creating DatabaseClient instance from valid DSN but connection error."""
    with patch('src.database.create_engine') as mock_create_engine:
        mock_create_engine.side_effect = Exception("Connection failed")
        try:
            DatabaseClient.from_credentials("username", "password", "localhost:1521/service")
            pytest.fail("DatabaseConnectionError not raised")
        except DatabaseConnectionError as e:
            assert "Database connection failed" in str(e)
            assert "Connection failed" in str(e.__cause__)
        mock_create_engine.assert_called_once()
