import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.api.luxs_api import LuxsAPI

@pytest.fixture
def mock_client():
    client = Mock()
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    client.make_request.return_value = mock_response
    return client

@pytest.fixture
def api(mock_client):
    return LuxsAPI(mock_client)

def test_get_objects(api, mock_client):
    # Test with minimal parameters
    api.get_objects()
    mock_client.make_request.assert_called_with(
        'GET', 
        'v1/objects', 
        params={'onlyActive': False, 'page': 0, 'pageSize': 100}
    )
    
    # Test with all parameters
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)
    api.get_objects(
        last_change_date_start=start_date,
        last_change_date_end=end_date,
        only_active=True,
        page=1,
        page_size=50
    )
    mock_client.make_request.assert_called_with(
        'GET',
        'v1/objects',
        params={
            'lastChangeDateStart': '2024-01-01T00:00:00',
            'lastChangeDateEnd': '2024-02-01T00:00:00',
            'onlyActive': True,
            'page': 1,
            'pageSize': 50
        }
    )

def test_get_objects_by_type(api, mock_client):
    # Test with minimal parameters
    api.get_objects_by_type('Building')
    mock_client.make_request.assert_called_with(
        'GET',
        'v1/objects/filterByObjectType',
        params={'objectType': 'Building', 'onlyActive': False, 'page': 0, 'pageSize': 100}
    )
    
    # Test with all parameters
    api.get_objects_by_type(
        object_type='Building',
        identifier='123',
        attributes=['attr1', 'attr2'],
        attributes_filter={'key': 'value'},
        only_active=True,
        page=2,
        page_size=25
    )
    mock_client.make_request.assert_called_with(
        'GET',
        'v1/objects/filterByObjectType',
        params={
            'objectType': 'Building',
            'identifier': '123',
            'attributes': ['attr1', 'attr2'],
            'attributesFilter': {'key': 'value'},
            'onlyActive': True,
            'page': 2,
            'pageSize': 25
        }
    )

def test_get_children(api, mock_client):
    api.get_children('Building', '123', ['Unit', 'Space'])
    mock_client.make_request.assert_called_with(
        'GET',
        'v1/objects/children',
        params={
            'parentObjectType': 'Building',
            'parentIdentifier': '123',
            'childObjectTypes': ['Unit', 'Space'],
            'onlyActive': False,
            'page': 0,
            'pageSize': 100
        }
    )

def test_get_metadata(api, mock_client):
    # Test without object type
    api.get_metadata()
    mock_client.make_request.assert_called_with('GET', 'v1/metadata', params={})
    
    # Test with object type
    api.get_metadata('Building')
    mock_client.make_request.assert_called_with(
        'GET',
        'v1/metadata',
        params={'objectType': 'Building'}
    )

def test_get_history(api, mock_client):
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 2, 1)
    api.get_history(
        object_type='Building',
        identifier='123',
        attributes=['attr1'],
        change_date_start=start_date,
        change_date_end=end_date,
        page=1,
        page_size=50
    )
    mock_client.make_request.assert_called_with(
        'GET',
        'v1/history',
        params={
            'objectType': 'Building',
            'identifier': '123',
            'attributes': ['attr1'],
            'changeDateStart': '2024-01-01T00:00:00',
            'changeDateEnd': '2024-02-01T00:00:00',
            'page': 1,
            'pageSize': 50
        }
    ) 
