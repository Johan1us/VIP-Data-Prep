import requests
import time

class APIClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://api.accept.luxsinsights.com"):
        self.client_id = client_id
        self.client_secret = client_secret
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

    def get_metadata(self, object_type: str = None):
        """
        Haalt metadata op. Als object_type is gegeven, filter op dat type.
        GET /v1/metadata?objectType=<object_type>
        """
        params = {}
        if object_type:
            params["objectType"] = object_type
        url = f"{self.base_url}/v1/metadata"
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def get_objects(self, object_type: str, attributes: list = None, identifier: str = None, only_active: bool = False, page: int = 1, page_size: int = 50):
        """
        Haalt objecten op van een bepaald objectType.
        Gebruikt endpoint: GET /v1/objects/filterByObjectType
        """
        url = f"{self.base_url}/v1/objects/filterByObjectType"
        params = {
            "objectType": object_type,
            "onlyActive": str(only_active).lower(),
            "page": page,
            "pageSize": page_size
        }
        # attributes in query: &attributes=value&attributes=value
        if attributes:
            # requests kan array-params meestal aan via params['attributes'] = attributes
            params["attributes"] = attributes
        if identifier:
            params["identifier"] = identifier

        # Voor filtering op attributen zou je iets als:
        # params["attributesFilter"] = {"AttributeName": "AttributeValue"}
        # moeten verwerken, maar dit kan tricky zijn met requests.
        # De documentatie lijkt te suggereren dat attributesFilter
        # een object is. Je zou dit kunnen oplossen door:
        #   params[("attributesFilter[AttributeName]")] = "AttributeValue"
        # Afhankelijk van hoe de API dit exact verwacht.
        # Als attributesFilter keys dynamisch zijn, moet je misschien de request handmatig construeren.
        # Hier is het nog onduidelijk hoe de API dit exact verwacht, moet je testen of documentatie checken.

        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

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
        Update objecten:
        PUT /v1/objects
        Body: array van UpdateObjectsBody
        """
        url = f"{self.base_url}/v1/objects"
        response = requests.put(url, headers=self._headers(), json=objects_data)
        response.raise_for_status()
        return response.json()
