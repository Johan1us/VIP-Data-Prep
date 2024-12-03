import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LuxsAPI:
    """Client for interacting with LUXS Accept API based on OpenAPI spec"""

    def __init__(self, client: Any) -> None:
        self.client = client
        self.page_size: int = 100
        self.page: int = 0

    def get_objects(
        self,
        last_change_date_start: Optional[datetime] = None,
        last_change_date_end: Optional[datetime] = None,
        only_active: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Optional[List[Dict]]:
        """Get objects by supplied filters"""
        params = {"onlyActive": only_active, "page": page, "pageSize": page_size}

        if last_change_date_start:
            params["lastChangeDateStart"] = last_change_date_start.isoformat()
        if last_change_date_end:
            params["lastChangeDateEnd"] = last_change_date_end.isoformat()

        return self._make_request("GET", "v1/objects", params=params)

    def get_objects_by_type(
        self,
        object_type: str,
        identifier: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        attributes_filter: Optional[Dict[str, Any]] = None,
        only_active: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get objects by object type with optional filtering"""
        params = {
            "objectType": object_type,
            "onlyActive": only_active,
            "page": page,
            "pageSize": page_size,
        }

        if identifier:
            params["identifier"] = identifier
        if attributes:
            params["attributes"] = attributes
        if attributes_filter:
            params["attributesFilter"] = attributes_filter

        return self._make_request("GET", "v1/objects/filterByObjectType", params=params)

    def get_children(
        self,
        parent_object_type: str,
        parent_identifier: str,
        child_object_types: Optional[List[str]] = None,
        only_active: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Optional[List[Dict]]:
        """Get children objects for provided parent object"""
        params = {
            "parentObjectType": parent_object_type,
            "parentIdentifier": parent_identifier,
            "onlyActive": only_active,
            "page": page,
            "pageSize": page_size,
        }

        if child_object_types:
            params["childObjectTypes"] = child_object_types

        return self._make_request("GET", "v1/objects/children", params=params)

    def get_metadata(self, object_type: Optional[str] = None) -> Optional[Dict]:
        """Get metadata for object types"""
        params = {}
        if object_type:
            params["objectType"] = object_type

        return self._make_request("GET", "v1/metadata", params=params)

    def get_history(
        self,
        object_type: str,
        identifier: str,
        attributes: Optional[List[str]] = None,
        change_date_start: Optional[datetime] = None,
        change_date_end: Optional[datetime] = None,
        page: int = 0,
        page_size: int = 100,
    ) -> Optional[List[Dict]]:
        """Get history by supplied filters"""
        params = {
            "objectType": object_type,
            "identifier": identifier,
            "page": page,
            "pageSize": page_size,
        }

        if attributes:
            params["attributes"] = attributes
        if change_date_start:
            params["changeDateStart"] = change_date_start.isoformat()
        if change_date_end:
            params["changeDateEnd"] = change_date_end.isoformat()

        return self._make_request("GET", "v1/history", params=params)

    def update_objects(self, objects: List[Dict]) -> Optional[List[Dict]]:
        """Update multiple objects"""
        return self._make_request("PUT", "v1/objects", data=objects)

    def upsert_objects(self, objects: List[Dict]) -> Optional[List[Dict]]:
        """Add/update multiple objects"""
        return self._make_request("POST", "v1/objects", data=objects)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
    ) -> Optional[Union[List, Dict]]:
        """Make API request and handle response"""
        try:
            response = self.client.make_request(
                endpoint, method=method, params=params, data=data
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None
