import requests
import time
from typing import Optional
import json

class APIClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://api.accept.luxsinsights.com"):
        self.client_id = client_id
        self.client_secret = client_secret
        # if url is http then change to https
        # if base_url.startswith("http://"):
        #     base_url = base_url.replace("http://", "https://")
        self.base_url = base_url
        self.token = None
        self.token_expires_at = 0  # Timestamp wanneer token verloopt

    def _get_token(self):
        """Haalt een nieuw OAuth2 token op met client credentials."""
        token_url = "https://auth.accept.luxsinsights.com/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)  # standaard 1 uur
        self.token_expires_at = time.time() + expires_in

    def _ensure_token(self):
        """Checkt of het token nog geldig is, anders vraag een nieuwe aan."""
        if self.token is None or time.time() > self.token_expires_at:
            self._get_token()

    def _headers(self):
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # test of de client_id en client_secret correct zijn
    def test_client(self):
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_metadata(self, object_type: str = None):
        """
        Haalt metadata op. Als object_type is gegeven, filter op dat type.
        GET /v1/metadata?objectType=<object_type>
        """
        print(f"Getting metadata for {object_type}")
        print(f"base_url: {self.base_url}")
        params = {}
        if object_type:
            params["objectType"] = object_type
        url = f"{self.base_url}/v1/metadata"
        print(f"URL: {url}")
        print(f"Headers: {self._headers()}")
        print(f"Params: {params}")
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        print(response.json())
        return response.json()

    def get_objects(self, object_type: str, attributes: list = None, identifier: str = None,
                    only_active: bool = False, page: int = 1, page_size: int = 50):
        """
        Haalt één pagina van objecten op van een bepaald objectType.

        Args:
            object_type (str): Type van het object
            attributes (list, optional): Lijst van gewenste attributen
            identifier (str, optional): Identifier om op te filteren
            only_active (bool, optional): Alleen actieve objecten ophalen
            page (int, optional): Paginanummer
            page_size (int, optional): Aantal items per pagina

        Returns:
            dict: Response van de API met objecten voor de opgevraagde pagina
        """
        url = f"{self.base_url}/v1/objects/filterByObjectType"

        params = {
            "objectType": object_type,
            "onlyActive": str(only_active).lower(),
            "page": page,
            "pageSize": page_size
        }
        if attributes:
            params["attributes"] = attributes
        if identifier:
            params["identifier"] = identifier

        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        data = response.json()

        # Ensure consistent return format
        if isinstance(data, list):
            return {
                "objects": data,
                "totalCount": len(data),
                "totalPages": 1,
                "currentPage": 1
            }
        return data

    def upsert_objects(self, objects_data: list):
        """
        Voeg objecten toe of update ze:
        POST /v1/objects
        Body: array van UpsertObjectsBody
        """
        url = f"{self.base_url}/v1/objects"
        response = requests.post(url, headers=self._headers(), json=objects_data)
        response.raise_for_status()
        return response.json()

    def update_objects(self, objects_data: list):
        """
        Update objecten via PUT /v1/objects

        Expected request body format:
        [
            {
                "objectType": "string",
                "identifier": "string",
                "attributes": {
                    "AttributeName1": "AttributeValue1",
                    "AttributeName2": "AttributeValue2"
                }
            }
        ]

        Expected response format:
        [
            {
                "objectType": "string",
                "identifier": "string",
                "success": boolean,
                "message": "string"
            }
        ]
        """
        url = f"{self.base_url}/v1/objects"

        # Log request details
        print("=== API Request Details ===")
        print(f"URL: {url}")
        print(f"Method: PUT")
        print(f"Headers: {self._headers()}")
        print(f"Request Body Sample (first 2 items): {json.dumps(objects_data[:2], indent=2)}")

        # Make the request
        response = requests.put(url, headers=self._headers(), json=objects_data)

        # Log response details
        print("\n=== API Response Details ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body Sample (first 2 items): {json.dumps(response.json()[:2], indent=2) if response.ok else response.text}")

        response.raise_for_status()
        return response.json()
if __name__ == "__main__":
    import os
    import json
    client_id = os.getenv("LUXS_ACCEPT_CLIENT_ID")
    client_secret = os.getenv("LUXS_ACCEPT_CLIENT_SECRET")
    base_url = "https://api.accept.luxsinsights.com"
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret}")
    print(f"Base URL: {base_url}")
    api_client = APIClient(client_id=client_id, client_secret=client_secret, base_url=base_url)

    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to the config folder (going up one level to app, then into config)
    config_folder = os.path.join(current_dir, "..", "config")

    datasets = []

    for file in os.listdir(config_folder):
        if file.endswith(".json"):
            with open(os.path.join(config_folder, file), 'r') as f:
                data = json.load(f)
                datasets.append(data["dataset"])

    print(f"Datasets: {datasets}")

    selected_dataset = "PO Daken"

    # open de bijbehorende json file door de naam te zoeken in de file onder de key "dataset"
    for file in os.listdir(config_folder):
        if file.endswith(".json"):
            with open(os.path.join(config_folder, file), 'r') as f:
                data = json.load(f)
                if data["dataset"] == selected_dataset:
                    print(data)
                    attribute_names = [attr["AttributeName"] for attr in data["attributes"]]
                    print(attribute_names)
                    object_type = data["objectType"]
                    print(object_type)

                    # haal de metadata op voor het objectType
                    metadata = api_client.get_metadata(object_type=object_type)
                    print(metadata)

                    # maak een metadata map
                    # metadata_map = build_metadata_map(metadata, data)
                    # print(metadata_map)

                    # haal de data op voor het objectType
                    data = api_client.get_objects(object_type=object_type, attributes=attribute_names)
                    print(data)
