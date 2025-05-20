from unittest.mock import MagicMock, patch

from src.query_runner import stream_rows


def test_stream_rows_yields_dicts():
    # Mock result set
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "study_id", "value"]
    mock_result.__iter__.return_value = [
        (1, 1234, "foo"),
        (2, 1234, "bar"),
    ]

    mock_conn = MagicMock()
    mock_conn.execution_options.return_value.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    with patch("src.query_runner.create_engine", return_value=mock_engine):
        rows = list(stream_rows("user", "pw", "db_dsn", "SELECT ...", 1234))
        assert rows == [
            {"id": 1, "study_id": 1234, "value": "foo"},
            {"id": 2, "study_id": 1234, "value": "bar"},
        ]
