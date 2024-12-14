import time
import pytest
import requests_mock
# from app.utils.api_client import APIClient
from VIP_DataMakelaar.app.utils.api_client import APIClient


@pytest.fixture
def client():
    # Gebruik dummy client_id en client_secret
    return APIClient(client_id="dummy_id", client_secret="dummy_secret")


@pytest.fixture
def token_url():
    return "https://auth.accept.luxsinsights.com/oauth2/token"


@pytest.fixture
def base_url():
    return "https://api.accept.luxsinsights.com"


def test_get_token(client, token_url, requests_mock):
    # Mock de token response
    requests_mock.post(token_url, json={"access_token": "test_token", "expires_in": 3600})

    # Forceer ophalen token
    client._get_token()
    assert client.token == "test_token"
    assert client.token_expires_at > time.time()


def test_get_metadata(client, token_url, base_url, requests_mock):
    # Mock de token response
    requests_mock.post(token_url, json={"access_token": "test_token", "expires_in": 3600})
    # Mock de metadata response
    metadata_url = f"{base_url}/v1/metadata"
    mock_response = {
        "objectTypes": [
            {
                "name": "Building",
                "attributes": [
                    {
                        "name": "Attribute1",
                        "type": "STRING",
                        "source": None,
                        "definition": "Test attribute",
                        "attributeCategory": "",
                        "dateFormat": None,
                        "attributeValueOptions": [],
                        "contactPerson": None,
                        "contactEmail": None,
                        "contactTelephone": None
                    }
                ],
                "childObjectTypes": []
            }
        ]
    }
    requests_mock.get(metadata_url, json=mock_response)

    result = client.get_metadata()
    assert "objectTypes" in result
    assert len(result["objectTypes"]) == 1
    assert result["objectTypes"][0]["name"] == "Building"


def test_get_objects(client, token_url, base_url, requests_mock):
    # Mock de token response
    requests_mock.post(token_url, json={"access_token": "test_token", "expires_in": 3600})
    objects_url = f"{base_url}/v1/objects/filterByObjectType"

    mock_objects = [
        {
            "objectType": "Unit",
            "identifier": "OGE-1234",
            "attributes": {"Name": "Test Unit"}
        }
    ]
    requests_mock.get(objects_url, json=mock_objects)

    result = client.get_objects(object_type="Unit")
    assert len(result) == 1
    assert result[0]["identifier"] == "OGE-1234"


def test_upsert_objects(client, token_url, base_url, requests_mock):
    # Mock de token response
    requests_mock.post(token_url, json={"access_token": "test_token", "expires_in": 3600})
    upsert_url = f"{base_url}/v1/objects"
    mock_response = [
        {
            "objectType": "Unit",
            "identifier": "OGE-1234",
            "success": True,
            "isCreation": True,
            "message": "Created successfully"
        }
    ]
    requests_mock.post(upsert_url, json=mock_response)

    objects_data = [{
        "objectType": "Unit",
        "identifier": "OGE-1234",
        "attributes": {"Name": "New Unit"}
    }]
    result = client.upsert_objects(objects_data)
    assert len(result) == 1
    assert result[0]["success"] is True


def test_update_objects(client, token_url, base_url, requests_mock):
    # Mock de token response
    requests_mock.post(token_url, json={"access_token": "test_token", "expires_in": 3600})
    update_url = f"{base_url}/v1/objects"
    mock_response = [
        {
            "objectType": "Unit",
            "identifier": "OGE-1234",
            "success": True,
            "message": "Updated successfully"
        }
    ]
    requests_mock.put(update_url, json=mock_response)

    objects_data = [{
        "objectType": "Unit",
        "identifier": "OGE-1234",
        "attributes": {"Name": "Updated Unit"}
    }]
    result = client.update_objects(objects_data)
    assert len(result) == 1
    assert result[0]["success"] is True
    assert "Updated successfully" in result[0]["message"]
