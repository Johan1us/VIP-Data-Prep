import pytest


@pytest.fixture
def mock_config():
    return {
        'LUXS_ACCEPT_CLIENT_ID': 'test_client_id',
        'LUXS_ACCEPT_CLIENT_SECRET': 'test_client_secret',
        'LUXS_ACCEPT_API_URL': 'https://api.test.com',
        'LUXS_ACCEPT_AUTH_URL': 'https://auth.test.com'
    }

@pytest.fixture
def api_client(mock_config, monkeypatch):
    # Mock environment variables
    for key, value in mock_config.items():
        monkeypatch.setenv(key, value)
    
    from src.api_client import LuxsAcceptClient
    return LuxsAcceptClient() 