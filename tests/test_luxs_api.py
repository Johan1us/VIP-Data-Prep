from datetime import datetime
from unittest.mock import Mock

import pytest

from src.api.luxs_api import LuxsAPI


@pytest.fixture
def mock_client() -> Mock:
    client = Mock()
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    client.make_request.return_value = mock_response
    return client


@pytest.fixture
def api(mock_client: Mock) -> LuxsAPI:
    return LuxsAPI(mock_client)


def test_get_objects(api: LuxsAPI, mock_client: Mock) -> None:
    # Test with minimal parameters
    api.get_objects()
    mock_client.make_request.assert_called_with(
        "v1/objects",
        method="GET",
        params={"onlyActive": False, "page": 0, "pageSize": 100},
        data=None,
    )

    # Test with all parameters
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)
    api.get_objects(
        last_change_date_start=start_date,
        last_change_date_end=end_date,
        only_active=True,
        page=1,
        page_size=50,
    )
    mock_client.make_request.assert_called_with(
        "v1/objects",
        method="GET",
        params={
            "lastChangeDateStart": "2024-01-01T00:00:00",
            "lastChangeDateEnd": "2024-02-01T00:00:00",
            "onlyActive": True,
            "page": 1,
            "pageSize": 50,
        },
        data=None,
    )


def test_get_objects_by_type(api: LuxsAPI, mock_client: Mock) -> None:
    # Test with minimal parameters
    api.get_objects_by_type("Building")
    mock_client.make_request.assert_called_with(
        "v1/objects/filterByObjectType",
        method="GET",
        params={
            "objectType": "Building",
            "onlyActive": False,
            "page": 0,
            "pageSize": 100,
        },
        data=None,
    )

    # Test with all parameters
    api.get_objects_by_type(
        object_type="Building",
        identifier="123",
        attributes=["attr1", "attr2"],
        attributes_filter={"key": "value"},
        only_active=True,
        page=2,
        page_size=25,
    )
    mock_client.make_request.assert_called_with(
        "v1/objects/filterByObjectType",
        method="GET",
        params={
            "objectType": "Building",
            "identifier": "123",
            "attributes": ["attr1", "attr2"],
            "attributesFilter": {"key": "value"},
            "onlyActive": True,
            "page": 2,
            "pageSize": 25,
        },
        data=None,
    )


def test_get_children(api: LuxsAPI, mock_client: Mock) -> None:
    api.get_children("Building", "123", ["Unit", "Space"])
    mock_client.make_request.assert_called_with(
        "v1/objects/children",
        method="GET",
        params={
            "parentObjectType": "Building",
            "parentIdentifier": "123",
            "childObjectTypes": ["Unit", "Space"],
            "onlyActive": False,
            "page": 0,
            "pageSize": 100,
        },
        data=None,
    )


def test_get_metadata(api: LuxsAPI, mock_client: Mock) -> None:
    # Test without object type
    api.get_metadata()
    mock_client.make_request.assert_called_with(
        "v1/metadata", method="GET", params={}, data=None
    )

    # Test with object type
    api.get_metadata("Building")
    mock_client.make_request.assert_called_with(
        "v1/metadata", method="GET", params={"objectType": "Building"}, data=None
    )


def test_get_history(api: LuxsAPI, mock_client: Mock) -> None:
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)
    api.get_history(
        object_type="Building",
        identifier="123",
        attributes=["attr1"],
        change_date_start=start_date,
        change_date_end=end_date,
        page=1,
        page_size=50,
    )
    mock_client.make_request.assert_called_with(
        "v1/history",
        method="GET",
        params={
            "objectType": "Building",
            "identifier": "123",
            "attributes": ["attr1"],
            "changeDateStart": "2024-01-01T00:00:00",
            "changeDateEnd": "2024-02-01T00:00:00",
            "page": 1,
            "pageSize": 50,
        },
        data=None,
    )
