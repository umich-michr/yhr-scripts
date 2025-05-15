from unittest.mock import patch

import pytest

from src.config import get_dsn, load_config


def test_load_config_success():
    """Test loading config with all required environment variables."""
    mock_env = {
        "DB_USERNAME": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "1521",
        "DB_SERVICE_NAME": "orclpdb1",
        "IP_LOOKUP_API_KEY": "test_api_key",
    }
    with patch("src.config.load_dotenv") as mock_dotenv:
        mock_dotenv.return_value = None  # Mock load_dotenv to do nothing
        with patch.dict("os.environ", mock_env, clear=True):
            config = load_config()
            assert config == {
                "db_username": "test_user",
                "db_password": "test_pass",
                "db_host": "localhost",
                "db_port": "1521",
                "db_service_name": "orclpdb1",
                "ip_lookup_api_key": "test_api_key",
            }


def test_load_config_missing_vars():
    """Test load_config raises ValueError when variables are missing."""
    mock_env = {"DB_USERNAME": "test_user"}  # Missing other vars
    with patch("src.config.load_dotenv") as mock_dotenv:
        mock_dotenv.return_value = None  # Mock load_dotenv to do nothing
        with patch.dict("os.environ", mock_env, clear=True):
            with pytest.raises(ValueError) as exc_info:
                load_config()
            assert (
                "Missing environment variables: DB_PASSWORD, DB_HOST, DB_PORT, DB_SERVICE_NAME"
                in str(exc_info.value)
            )


def test_load_config_optional_vars():
    """Test load_config with optional variables missing."""
    mock_env = {
        "DB_USERNAME": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "1521",
        "DB_SERVICE_NAME": "orclpdb1",
    }
    with patch("src.config.load_dotenv") as mock_dotenv:
        mock_dotenv.return_value = None  # Mock load_dotenv to do nothing
        with patch.dict("os.environ", mock_env, clear=True):
            config = load_config()
            assert "ip_lookup_api_key" not in config


def test_get_dsn():
    """Test DSN construction from config."""
    config = {"db_host": "localhost", "db_port": "1521", "db_service_name": "orclpdb1"}
    dsn = get_dsn(config)
    assert dsn == "localhost:1521/orclpdb1"
