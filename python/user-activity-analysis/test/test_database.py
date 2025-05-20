from unittest.mock import MagicMock, patch

import pytest

from src.database import (DatabaseClient, DatabaseConnectionError,
                          QueryExecutionError)


@pytest.fixture
def mock_engine():
    """Fixture for mock engine."""
    return MagicMock()


def test_from_credentials_success():
    """Test creating DatabaseClient instance from credentials."""
    with patch("sqlalchemy.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        db_client = DatabaseClient.from_credentials(
            "username", "password", "localhost:1521/service"
        )
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
    with patch("src.database.create_engine") as mock_create_engine:
        mock_create_engine.side_effect = Exception("Connection failed")
        try:
            DatabaseClient.from_credentials(
                "username", "password", "localhost:1521/service"
            )
            pytest.fail("DatabaseConnectionError not raised")
        except DatabaseConnectionError as e:
            assert "Database connection failed" in str(e)
            assert "Connection failed" in str(e.__cause__)
        mock_create_engine.assert_called_once()


def test_stream_rows_yields_dicts(mock_engine):
    # Mock result set
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "study_id", "value"]
    mock_result.__iter__.return_value = [
        (1, 1234, "foo"),
        (2, 1234, "bar"),
    ]

    mock_conn = MagicMock()
    mock_conn.execution_options.return_value.execute.return_value = mock_result
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    db_client = DatabaseClient(mock_engine)
    rows = list(db_client.stream_rows("SELECT ...", {"study_id": 1234}))
    assert rows == [
        {"id": 1, "study_id": 1234, "value": "foo"},
        {"id": 2, "study_id": 1234, "value": "bar"},
    ]


def test_stream_rows_query_execution_error(mock_engine):
    mock_conn = MagicMock()
    mock_conn.execution_options.return_value.execute.side_effect = Exception(
        "Query failed"
    )
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    db_client = DatabaseClient(mock_engine)
    with pytest.raises(QueryExecutionError) as exc_info:
        list(db_client.stream_rows("SELECT ...", {"study_id": 1234}))
    assert "Query execution failed" in str(exc_info.value)
