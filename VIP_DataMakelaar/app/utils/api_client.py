import os
import json
import time
import requests
from typing import Optional, List, Dict, Any, Union

from attr import attributes


class APIClient:
    """
    Deze klasse beheert het ophalen en gebruiken van OAuth2 tokens
    en het uitvoeren van verzoeken naar de Luxs Insights API.

    Belangrijkste functionaliteiten:
    - Automatisch ophalen en verversen van OAuth2 tokens.
    - Ophalen van metadata en objectgegevens.
    - Upsert en update van objecten.
    """

    def __init__(self, client_id: str, client_secret: str,
                 base_url: str = "https://api.accept.luxsinsights.com") -> None:
        """
        Initialiseer de APIClient met de benodigde client credentials en basis-URL.

        Args:
            client_id (str): De Client ID voor authenticatie.
            client_secret (str): De Client Secret voor authenticatie.
            base_url (str): De basis-URL van de API.
                            Standaard: "https://api.accept.luxsinsights.com"
        """
        self.client_id = client_id
        self.client_secret = client_secret

        # Zorg ervoor dat de base_url met https begint
        # (commentaar uit originele code is behouden, maar niet meer nodig
        #  omdat we nu standaard met https werken)
        # if base_url.startswith("http://"):
        #     base_url = base_url.replace("http://", "https://")

        self.base_url = base_url
        self.token: Optional[str] = None
        self.token_expires_at: float = 0.0  # Unix timestamp wanneer token verloopt

    def _get_token(self) -> None:
        """
        Haal een nieuw OAuth2-token op middels de client credentials.

        Deze functie doet een POST-request naar de token endpoint
        en slaat het verkregen access_token en de verloopdatum op.
        """
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
        # 'expires_in' komt vaak als seconden; standaard op 3600 (1 uur) als niet aanwezig.
        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in

    def _ensure_token(self) -> None:
        """
        Controleer of het huidige token nog geldig is.
        Als het token niet bestaat of is verlopen, vraag dan een nieuw token aan.
        """
        if self.token is None or time.time() > self.token_expires_at:
            self._get_token()

    def _headers(self) -> Dict[str, str]:
        """
        Bouw de headers voor een API-request, inclusief het Bearer token.

        Returns:
            Dict[str, str]: Een dictionary met HTTP-headers.
        """
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def test_client(self) -> Dict[str, str]:
        """
        Test of de client_id en client_secret correct zijn door
        een geldige token-header te retourneren.

        Returns:
            Dict[str, str]: Headers met geldige OAuth2 token.
        """
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_metadata(self, object_type: Optional[str] = None) -> Any:
        """
        Haalt metadata op van alle beschikbare objecttypes, of filtert indien
        een object_type is opgegeven.

        Args:
            object_type (str, optional): Het type object waarvoor metadata moet worden opgehaald.
                                         Indien None, alle metadata ophalen.

        Returns:
            Any: De JSON-respons van de metadata endpoint.
        """
        # Opbouwen van de URL en query parameters
        url = f"{self.base_url}/v1/metadata"
        params: Dict[str, str] = {}
        if object_type:
            params["objectType"] = object_type

        # Voor debug: print statements om inzicht te geven in de request details
        print(f"[DEBUG] Ophalen metadata voor object_type: {object_type}")
        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] Headers: {self._headers()}")
        print(f"[DEBUG] Params: {params}")

        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def get_objects(
            self,
            object_type: str,
            attributes: Optional[List[str]] = None,
            identifier: Optional[str] = None,
            only_active: bool = False,
            page: int = 0,
            page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Haalt een pagina objecten op van een bepaald objectType. Eventueel kan worden gefilterd
        op identificatie en kunnen specifieke attributen worden opgevraagd.

        Args:
            object_type (str): Type van het object dat moet worden opgehaald.
            attributes (List[str], optional): Lijst met specifieke attributen om op te halen.
            identifier (str, optional): Specifieke identifier om op te filteren.
            only_active (bool, optional): Alleen actieve objecten ophalen.
            page (int, optional): Paginanummer.
            page_size (int, optional): Aantal items per pagina.

        Returns:
            Dict[str, Any]: De JSON-respons van de API met objecten.
        """
        url = f"{self.base_url}/v1/objects/filterByObjectType"

        # Query parameters opbouwen
        params: Dict[str, Union[str, int, bool, List[str]]] = {
            "objectType": object_type,
            "onlyActive": str(only_active).lower(),  # API verwacht 'true' of 'false' als string
            "page": page,
            "pageSize": page_size
        }
        if attributes:
            # De API kan mogelijk een list verwerken, of anders comma-separatie
            # Op basis van documentatie lijkt een lijst direct meegeven mogelijk.
            params["attributes"] = attributes
        if identifier:
            params["identifier"] = identifier

        # Request uitvoeren
        print(f"[DEBUG] Ophalen objecten van type '{object_type}'")
        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] Headers: {self._headers()}")
        print(f"[DEBUG] Params: {params}")
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()

        data = response.json()

        # Zorg voor een consistente return-structuur
        # Soms geeft de API een lijst terug, soms een dict. Als het een lijst is,
        # wrap deze dan in een standaard dict-structuur.
        if isinstance(data, list):
            return {
                "objects": data,
                "totalCount": len(data),
                "totalPages": 1,
                "currentPage": 1
            }
        return data

    def get_all_objects(
            self,
            object_type: str,
            attributes: Optional[List[str]] = None,
            identifier: Optional[str] = None,
            only_active: bool = False,
            page_size: int = 2000
    ) -> Dict[str, Any]:
        """
        Haalt alle objecten op van een bepaald objectType, over alle beschikbare pagina's heen.

        Deze methode:
        1. Haalt eerst de eerste pagina op.
        2. Leest daaruit af hoeveel totale pagina's er zijn.
        3. Haalt vervolgens, indien nodig, alle resterende pagina's op.
        4. Retourneert één gecombineerd resultaat met alle objecten.

        Args:
            object_type (str): Het type object dat moet worden opgehaald.
            attributes (List[str], optional): Lijst met specifieke attributen om op te halen.
            identifier (str, optional): Specifieke identifier om op te filteren.
            only_active (bool, optional): Alleen actieve objecten ophalen.
            page_size (int, optional): Aantal items per pagina, standaard 50.

        Returns:
            Dict[str, Any]: De JSON-respons met alle objecten, waarin:
                            - "objects": lijst met alle opgehaalde objecten
                            - "totalCount": totaal aantal opgehaalde objecten
                            - "totalPages": aantal pagina's dat is opgehaald
                            - "pageSize": het gebruikte paginaformaat
        """
        all_objects = []
        current_page = 0

        while True:
            # Haal de huidige pagina op
            resp = self.get_objects(
                object_type=object_type,
                attributes=attributes,
                identifier=identifier,
                only_active=only_active,
                page=current_page,
                page_size=page_size
            )

            # Haal objecten van de huidige pagina
            current_page_objects = resp.get("objects", [])
            all_objects.extend(current_page_objects)
            print(f"[DEBUG] Ophalen pagina {current_page}, {len(current_page_objects)} objecten")
            print(f"[DEBUG] Totaal aantal objecten nu: {len(all_objects)}")

            # Controleer of we klaar zijn: minder objecten dan page_size betekent laatste pagina
            if len(current_page_objects) < page_size:
                break

            # Ga naar de volgende pagina
            current_page += 1

        return {
            "objects": all_objects,
            "totalCount": len(all_objects),
            "pageSize": page_size
        }

    def upsert_objects(self, objects_data: List[Dict[str, Any]]) -> Any:
        """
        Voeg nieuwe objecten toe of update bestaande objecten.
        POST /v1/objects

        Args:
            objects_data (List[Dict[str, Any]]): Een lijst met objectdefinities
                                                 om toe te voegen of te updaten.

        Returns:
            Any: De JSON-respons van de API.
        """
        url = f"{self.base_url}/v1/objects"
        print(f"[DEBUG] Upsert van objecten naar {url}")
        response = requests.post(url, headers=self._headers(), json=objects_data)
        response.raise_for_status()
        return response.json()

    def update_objects(self, objects_data: List[Dict[str, Any]]) -> Any:
        """
        Update bestaande objecten.
        PUT /v1/objects

        Verwachte request body structuur:
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

        Returns:
            Any: De JSON-respons van de API, met voor elk object een bericht en successtatus.
        """
        url = f"{self.base_url}/v1/objects"

        # Debug-informatie over de request
        print("[DEBUG] Update objecten request details:")
        print(f"[DEBUG] URL: {url}")
        print("[DEBUG] Method: PUT")
        print(f"[DEBUG] Headers: {self._headers()}")
        # Print slechts de eerste 2 items voor leesbaarheid
        print(f"[DEBUG] Request Body (eerste 2 items): {json.dumps(objects_data[:2], indent=2)}")

        response = requests.put(url, headers=self._headers(), json=objects_data)

        # Debug-informatie over de response
        print("\n[DEBUG] Update objecten response details:")
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Response Headers: {dict(response.headers)}")
        if response.ok:
            resp_json = response.json()
            # Print slechts de eerste 2 items voor leesbaarheid
            print(f"[DEBUG] Response Body (eerste 2 items): {json.dumps(resp_json[:2], indent=2)}")
        else:
            print(f"[DEBUG] Response Body (error): {response.text}")

        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    # In dit blok testen we de functionaliteiten van onze APIClient.
    # Dit is handig voor debugging of om te verifiëren dat de authenticatie werkt.

    # Haal de client credentials op uit omgevingsvariabelen
    client_id = os.getenv("LUXS_ACCEPT_CLIENT_ID", "dummy_client_id")
    client_secret = os.getenv("LUXS_ACCEPT_CLIENT_SECRET", "dummy_client_secret")
    base_url = "https://api.accept.luxsinsights.com"

    print("[DEBUG] Initialiseren APIClient met:")
    print(f"        Client ID: {client_id}")
    print(f"        Client Secret: {client_secret}")
    print(f"        Base URL: {base_url}")

    api_client = APIClient(client_id=client_id, client_secret=client_secret, base_url=base_url)

    # Test de client door de headers op te halen
    print("[DEBUG] Test client authenticatie headers:")
    print(api_client.test_client())

    # Haal metadata op (bijvoorbeeld alle metadata)
    print("[DEBUG] Ophalen volledige metadata:")
    all_metadata = api_client.get_metadata("Building")
    print("[DEBUG] Metadata (eerste 200 chars):", str(all_metadata)[:200], "...")

    # Haal objecten op van een bepaald type (bijv. Building)
    print("[DEBUG] Ophalen objecten van type 'Building':")
    attributes = ["Dakpartner - Building - Woonstad Rotterdam", "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam"]
    building_objects = api_client.get_objects(object_type="Building", attributes=attributes, only_active=True)
    # Print de eerste 5 objecten voor inspectie
    print("[DEBUG] Eerste 5 objecten:")
    for obj in building_objects["objects"][:5]:
        print(obj)

    # Haal alle objecten op van een bepaald type (bijv. Building)
    print("[DEBUG] Ophalen alle objecten van type 'Building':")
    all_building_objects = api_client.get_all_objects(object_type="Building", attributes=attributes, only_active=True)
    print("[DEBUG] Aantal objecten:", all_building_objects["totalCount"])
    print("[DEBUG] Eerste 5 objecten:")
    for obj in all_building_objects["objects"][:5]:
        print(obj)
