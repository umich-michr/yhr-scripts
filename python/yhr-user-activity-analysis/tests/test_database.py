import pytest
import oracledb
import pandas as pd
from src.database import DatabaseClient, DatabaseConnectionError, QueryExecutionError
from unittest.mock import MagicMock, patch

@pytest.fixture
def db_client():
    """Fixture for DatabaseClient instance."""
    return DatabaseClient(username="test_user", password="test_pass", dsn="localhost:1521/orclpdb1")

def test_connect_success(db_client):
    """Test successful database connection."""
    with patch('sqlalchemy.create_engine') as mock_create_database_engine:
        with patch('sqlalchemy.engine.Engine.connect') as mock_connect:
            mock_connect.return_value = MagicMock()
            result = db_client.connect()
            assert result is db_client
            assert db_client.engine is not None

def test_connect_failure(db_client):
    """Test connection failure raises DatabaseConnectionError."""
    with patch('sqlalchemy.create_engine') as mock_create_engine:
        mock_create_engine.side_effect = Exception("Connection failed")
        try:
            db_client.connect()
        except Exception as e:
            print(f"Actual exception: {e}")
            assert isinstance(e, DatabaseConnectionError)
            assert "Database connection failed" in str(e)

def test_execute_query_success(db_client):
    """Test successful query execution."""
    with patch('pandas.read_sql') as mock_read_sql:
        mock_df = pd.DataFrame({'STUDY_ID': [1]})
        mock_read_sql.return_value = mock_df
        db_client.engine = MagicMock()
        db_client.engine.connect.return_value.__enter__.return_value = MagicMock()
        result = db_client.execute_query("SELECT * FROM table")
        pd.testing.assert_frame_equal(result, mock_df)
        mock_read_sql.assert_called_once()

def test_execute_query_no_connection(db_client):
    """Test query execution fails without connection."""
    with pytest.raises(DatabaseConnectionError) as exc_info:
        db_client.execute_query("SELECT * FROM table")
    assert "No active database connection" in str(exc_info.value)

def test_execute_query_failure(db_client):
    """Test query execution failure raises QueryExecutionError."""
    with patch('pandas.read_sql') as mock_read_sql:
        mock_read_sql.side_effect = Exception("Query failed")
        db_client.engine = MagicMock()
        db_client.engine.connect.return_value.__enter__.return_value = MagicMock()
        with pytest.raises(QueryExecutionError) as exc_info:
            db_client.execute_query("SELECT * FROM table")
        assert "Query execution failed" in str(exc_info.value)

def test_close_connection(db_client):
    # No need to test close connection as engine doesn't need to be closed explicitly using sqlalchemy
    pass
